#!/usr/bin/env python3
"""Local-first evidence capture and bilingual content scaffolding for HaoStory."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import studio  # noqa: E402


SCHEMA = "haostory/v1"
REGISTRY_SCHEMA = "haostory/story-registry/v1"
JOURNAL_DIR = ".haostory"
CONFIG_FILE = ".haostory.json"
REGISTRY_FILE = "story-registry.json"
MAX_CAPTURE_CHARS = 120_000
PHASES = ("discovery", "design", "build", "validate", "release", "operate")
CAPTURE_MODES = ("manual", "assisted-auto", "off")
HIGH_CONFIDENCE_EVENTS = (
    "decision",
    "scope_change",
    "failure",
    "recovery",
    "before_after",
    "milestone",
    "demo",
    "metric",
    "external_signal",
)
WORK_KINDS = ("meaningful", "formatting", "dependency", "simple-fix", "consulting", "rename")
DATA_KINDS = ("real", "demo", "mixed", "unspecified")
AUTO_START_EXCLUSIONS = {"formatting", "dependency", "simple-fix", "consulting", "rename"}
SENSITIVE_PATH_PARTS = (
    ".env",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "id_rsa",
    "id_ed25519",
    "cookies",
    "browser profile",
)
SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}

DEFAULT_CONFIG: dict[str, Any] = {
    "studio": {
        "sponsor": {
            "enabled": True,
            "lab_name": "浩哥 AI 实验室",
            "lab_note": "关注 AI 产品、创作与实践",
            "wechat": "HaoAILab",
            "wechat_note": "一起玩转 AI",
            "onetake_name": "OneTake",
            "onetake_note": "把脚本继续做成视频",
        }
    },
    "languages": ["zh-CN", "en"],
    "brand": {
        "name": "",
        "name_zh": "",
        "website": "",
        "cta_en": "",
        "cta_zh": "",
    },
    "commercial_note": {
        "enabled": False,
        "en": (
            "The core workflow is open source. Private integrations, tailored "
            "workflows, and implementation partnerships may be offered separately."
        ),
        "zh-CN": "核心工作流保持开源；私有系统集成、定制工作流与落地合作可另行提供。",
    },
    "capture": {
        "mode": "off",
        "auto_start": False,
        "auto_checkpoint": list(HIGH_CONFIDENCE_EVENTS),
        "auto_finish_on_handoff": True,
        "require_notice": True,
        "assets_require_confirmation": False,
        "max_events_per_phase": 4,
    },
    "visual_capture": {
        "enabled": True,
        "mode": "when-enabled",
        "capture_events": ["failure", "recovery", "before_after", "milestone", "demo"],
        "store_directly_in_assets": True,
        "wait_for_stable_view": True,
        "recapture_invalid_frames": True,
        "production_requires_request": True,
        "prompt_on_phase_close": True,
        "final_content_review_required": True,
    },
    "story_memory": {
        "enabled": True,
        "registry": f"{JOURNAL_DIR}/{REGISTRY_FILE}",
        "require_new_claim_or_evidence": True,
        "max_context_ratio_short": 0.15,
        "max_context_ratio_long": 0.10,
    },
    "project_history": {
        "enabled": False,
        "directory": "docs",
        "progress_file": "docs/progress.md",
        "screenshots_directory": "docs/screenshots",
        "requires_stage_confirmation": True,
        "auto_commit": False,
        "auto_push": False,
        "auto_upload": False,
    },
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")[:72] or "story"


def run(command: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return 124, stdout, f"{stderr}\nTIMEOUT"


def project_root(cwd: Path) -> Path:
    code, stdout, _ = run(["git", "rev-parse", "--show-toplevel"], cwd, timeout=10)
    return Path(stdout.strip()).resolve() if code == 0 and stdout.strip() else cwd.resolve()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(root: Path) -> dict[str, Any]:
    path = root / CONFIG_FILE
    if not path.exists():
        return deep_merge(DEFAULT_CONFIG, {})
    try:
        custom = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid {CONFIG_FILE}: {exc}") from exc
    merged = deep_merge(DEFAULT_CONFIG, custom)
    custom_history = custom.get("project_history", {})
    if "directory" in custom_history:
        legacy_base = Path(str(custom_history["directory"]))
        if "progress_file" not in custom_history:
            merged["project_history"]["progress_file"] = str(legacy_base / "progress.md")
        if "screenshots_directory" not in custom_history:
            merged["project_history"]["screenshots_directory"] = str(legacy_base / "screenshots")
    # V2.1 moved review from individual local assets to the final content gate.
    # Keep the legacy key deterministic even in projects created by earlier versions.
    merged.setdefault("capture", {})["assets_require_confirmation"] = False
    return merged


def is_sensitive_path(path: Path) -> bool:
    lowered = str(path).lower()
    return path.suffix.lower() in SENSITIVE_SUFFIXES or any(part in lowered for part in SENSITIVE_PATH_PARTS)


def sanitize(text: str) -> str:
    if not text:
        return ""

    home = str(Path.home())
    text = text.replace(home, "<HOME>")
    text = re.sub(
        r"\b(https?://)([^\s/:@]+):([^\s/@]+)@",
        r"\1<credentials-redacted>@",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
        "<private-key-redacted>",
        text,
        flags=re.DOTALL,
    )
    secret_patterns = (
        r"\b(?:sk|pk)-[A-Za-z0-9_-]{16,}\b",
        r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b",
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
        r"(?im)^(\s*(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\s*[:=]\s*)[^\s#]+",
    )
    for pattern in secret_patterns:
        if pattern.startswith("(?im)"):
            text = re.sub(pattern, r"\1<secret-redacted>", text)
        else:
            text = re.sub(pattern, "<secret-redacted>", text, flags=re.IGNORECASE)

    text = re.sub(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])", "<email-redacted>", text)
    text = re.sub(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)", "<phone-redacted>", text)

    def redact_ip(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return raw
        if address.is_loopback or address.is_private or address.is_link_local:
            return raw
        return "<ip-redacted>"

    return re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", redact_ip, text)


def safe_text(text: str, limit: int = MAX_CAPTURE_CHARS) -> str:
    text = sanitize(text)
    if len(text) > limit:
        return f"{text[:limit]}\n\n<captured-output-truncated>\n"
    return text


def project_history_text(text: str) -> str:
    sanitized = sanitize(text)

    def redact_private_ip(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return raw
        if address.is_private and not address.is_loopback:
            return "<private-ip-redacted>"
        return raw

    return re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", redact_private_ip, sanitized)


def ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = current.splitlines()
    if JOURNAL_DIR + "/" not in lines and JOURNAL_DIR not in lines:
        separator = "" if not current or current.endswith("\n") else "\n"
        path.write_text(f"{current}{separator}{JOURNAL_DIR}/\n", encoding="utf-8")


def project_journal(root: Path, create: bool = False) -> Path:
    journal = root / JOURNAL_DIR
    if journal.is_symlink():
        raise SystemExit(f"Refusing a symlinked {JOURNAL_DIR}/ directory; capture must stay inside the project.")
    resolved = journal.resolve()
    if resolved.parent != root.resolve():
        raise SystemExit(f"Capture journal must stay inside the project's {JOURNAL_DIR}/ directory.")
    if create:
        journal.mkdir(exist_ok=True)
    return journal


def project_output_path(
    root: Path, raw_value: str, *, label: str, create_directory: bool = False
) -> Path:
    raw = str(raw_value).strip()
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or raw in {".", ".."}:
        raise SystemExit(f"{label} must be a non-empty project-relative path.")
    if any(part in {"..", ".git", JOURNAL_DIR} for part in candidate.parts):
        raise SystemExit(f"{label} must stay outside .git/ and .haostory/ inside the project.")
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise SystemExit(f"{label} must not contain symlinks.")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} must stay inside the project.") from exc
    if create_directory:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def project_history_paths(
    root: Path, config: dict[str, Any], *, create: bool = False
) -> tuple[Path, Path]:
    history = config.get("project_history", {})
    progress = project_output_path(
        root,
        str(history.get("progress_file", "docs/progress.md")),
        label="Project progress file",
    )
    screenshots = project_output_path(
        root,
        str(history.get("screenshots_directory", "docs/screenshots")),
        label="Project screenshots directory",
        create_directory=create,
    )
    if create:
        progress.parent.mkdir(parents=True, exist_ok=True)
    return progress, screenshots


def project_history_root(
    root: Path, config: dict[str, Any], *, create: bool = False
) -> Path:
    """Compatibility helper for callers that still inspect the legacy directory."""
    raw = str(config.get("project_history", {}).get("directory", "docs")).strip()
    return project_output_path(
        root, raw, label="Project history directory", create_directory=create
    )


def setup_project(root: Path) -> Path:
    ensure_gitignore(root)
    journal = project_journal(root, create=True)
    path = root / CONFIG_FILE
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry_path = journal / REGISTRY_FILE
    if not registry_path.exists():
        save_json(
            registry_path,
            {
                "schema": REGISTRY_SCHEMA,
                "project": root.name,
                "published_stories": [],
                "do_not_repeat": [],
            },
        )
    return path


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def registry_path(root: Path, config: dict[str, Any] | None = None) -> Path:
    journal = project_journal(root, create=True).resolve()
    configured = (config or {}).get("story_memory", {}).get("registry")
    if configured:
        candidate = Path(str(configured))
        candidate = candidate if candidate.is_absolute() else root / candidate
    else:
        candidate = journal / REGISTRY_FILE
    resolved = candidate.expanduser().resolve()
    try:
        relative = resolved.relative_to(journal)
    except ValueError as exc:
        raise SystemExit(f"Story registry must stay inside the project's {JOURNAL_DIR}/ directory.") from exc
    if not relative.parts:
        raise SystemExit(f"Story registry must be a file inside the project's {JOURNAL_DIR}/ directory.")
    return resolved


def load_registry(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    path = registry_path(root, config)
    if not path.exists():
        registry = {
            "schema": REGISTRY_SCHEMA,
            "project": root.name,
            "published_stories": [],
            "do_not_repeat": [],
        }
        save_json(path, registry)
        return registry
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid story registry: {exc}") from exc
    registry.setdefault("schema", REGISTRY_SCHEMA)
    registry.setdefault("project", root.name)
    registry.setdefault("published_stories", [])
    registry.setdefault("do_not_repeat", [])
    return registry


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", sanitize(value).strip()).casefold()


def session_manifests(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    journal = project_journal(root)
    if not journal.exists():
        return []
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(journal.glob("*/manifest.json")):
        try:
            found.append((path.parent, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return found


def find_matching_window(root: Path, initiative: str, phase: str) -> Path | None:
    matches: list[Path] = []
    for session, manifest in session_manifests(root):
        window = manifest.get("capture_window", {})
        if (
            normalize_key(str(manifest.get("initiative", ""))) == normalize_key(initiative)
            and manifest.get("phase") == phase
            and window.get("status") in {"active", "paused"}
        ):
            matches.append(session)
    if len(matches) > 1:
        candidates = ", ".join(sorted(path.name for path in matches))
        raise SystemExit(
            f"Multiple active capture windows cover {initiative}/{phase}: {candidates}. "
            "Close duplicates or pass an explicit --session where supported."
        )
    return matches[0] if matches else None


def inherited_context(
    root: Path, initiative: str, phase: str, parent_session: str | None = None
) -> dict[str, str] | None:
    candidates = sorted(
        session_manifests(root),
        key=lambda item: (manifest_updated_timestamp(item[1]), item[0].name),
    )
    if parent_session:
        parent_id = validate_session_id(parent_session)
        candidates = [item for item in candidates if item[0].name == parent_id]
    for session, manifest in reversed(candidates):
        if normalize_key(str(manifest.get("initiative", ""))) != normalize_key(initiative):
            continue
        if manifest.get("phase") == phase:
            continue
        return {
            "source_session": session.name,
            "phase": str(manifest.get("phase", "")),
            "title": sanitize(str(manifest.get("title", ""))),
            "summary": sanitize(str(manifest.get("summary", ""))),
            "outcome": sanitize(str(manifest.get("outcome", ""))),
            "lesson": sanitize(str(manifest.get("lesson", ""))),
        }
    if parent_session:
        raise SystemExit(f"Parent session not found for initiative: {parent_session}")
    return None


def manifest_updated_timestamp(manifest: dict[str, Any]) -> float:
    raw = str(manifest.get("updated_at") or manifest.get("started_at") or "")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return float("-inf")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def latest_session(root: Path) -> Path | None:
    candidates = session_manifests(root)
    if not candidates:
        return None
    session, _ = max(
        candidates,
        key=lambda item: (manifest_updated_timestamp(item[1]), item[0].name),
    )
    return session


def validate_session_id(value: str) -> str:
    raw = str(value).strip()
    candidate = Path(raw)
    if (
        not raw
        or raw in {".", ".."}
        or candidate.is_absolute()
        or len(candidate.parts) != 1
        or "/" in raw
        or "\\" in raw
    ):
        raise SystemExit(f"Session must be a direct child name inside {JOURNAL_DIR}/, not a path: {value}")
    return raw


def direct_session_path(journal: Path, value: str) -> Path:
    session_id = validate_session_id(value)
    path = journal / session_id
    if path.is_symlink():
        raise SystemExit(f"Session must be a direct child directory, not a symlink: {session_id}")
    resolved = path.resolve()
    if resolved.parent != journal.resolve():
        raise SystemExit(f"Session must be a direct child name inside {JOURNAL_DIR}/, not a path: {value}")
    return path


def resolve_session(root: Path, session: str | None, create_name: str | None = None) -> Path:
    journal = project_journal(root, create=True)
    if session:
        path = direct_session_path(journal, session)
    elif create_name:
        path = direct_session_path(journal, create_name)
    else:
        active = [
            path
            for path, manifest in session_manifests(root)
            if manifest.get("capture_window", {}).get("status") in {"active", "paused"}
        ]
        if len(active) > 1:
            candidates = ", ".join(sorted(path.name for path in active))
            raise SystemExit(
                f"Multiple active capture windows found: {candidates}. Pass --session with one candidate."
            )
        if len(active) == 1:
            return active[0]
        found = latest_session(root)
        if not found:
            raise SystemExit("No HaoStory session found. Run `start` first or pass --session.")
        return found
    if create_name is not None:
        path.mkdir(exist_ok=True)
    elif not path.is_dir():
        raise SystemExit(f"HaoStory session does not exist: {path.name}")
    return path


def load_manifest(session: Path) -> dict[str, Any]:
    path = session / "manifest.json"
    if not path.exists():
        raise SystemExit(f"Missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(session: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_iso()
    (session / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def append_timeline(session: Path, heading: str, fields: list[tuple[str, str]]) -> None:
    with (session / "timeline.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {sanitize(heading)}\n\n")
        for label, value in fields:
            handle.write(f"**{label}:** {safe_text(value or '—', 8_000)}\n\n")


def create_capture_session(
    root: Path,
    config: dict[str, Any],
    *,
    title: str,
    summary: str,
    work_type: str,
    session_name: str | None,
    initiative: str | None,
    phase: str | None,
    parent_session: str | None = None,
) -> Path:
    resolved_initiative = sanitize(initiative or slugify(title))
    resolved_phase = phase or "build"
    existing = find_matching_window(root, resolved_initiative, resolved_phase)
    if existing:
        raise SystemExit(
            f"An active capture window already covers {resolved_initiative}/{resolved_phase}: {existing.name}. "
            "Run `resume` or close it first."
        )
    name = session_name or f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(title)}"
    session = resolve_session(root, session_name, name)
    if (session / "manifest.json").exists():
        raise SystemExit(f"Session already exists: {session}")
    for folder in ("evidence", "assets"):
        (session / folder).mkdir(exist_ok=True)
    started_at = now_iso()
    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "project": root.name,
        "initiative": resolved_initiative,
        "phase": resolved_phase,
        "title": sanitize(title),
        "summary": sanitize(summary),
        "type": work_type,
        "started_at": started_at,
        "updated_at": started_at,
        "capture_window": {
            "id": session.name,
            "mode": config.get("capture", {}).get("mode", "manual"),
            "status": "active",
            "started_at": started_at,
            "pause_history": [],
        },
        "events": [],
        "stages": [],
        "assets": [],
        "commands": [],
    }
    context = inherited_context(root, resolved_initiative, resolved_phase, parent_session)
    if context:
        manifest["necessary_context"] = context
    evidence = capture_git(root, session, "start")
    manifest["stages"].append(
        {
            "type": "start",
            "stage": "start",
            "notes": manifest["summary"],
            "decision": "",
            "evidence": evidence,
            "assets": [],
            "captured_at": started_at,
        }
    )
    save_manifest(session, manifest)
    append_timeline(
        session,
        f"{started_at} · start",
        [
            ("Title", manifest["title"]),
            ("Initiative", resolved_initiative),
            ("Phase", resolved_phase),
            ("Summary", manifest["summary"]),
        ],
    )
    return session


def git_text(root: Path, args: list[str]) -> str:
    code, stdout, stderr = run(["git", *args], root, timeout=60)
    return safe_text(stdout if code == 0 else stderr)


def capture_git(root: Path, session: Path, label: str) -> dict[str, str]:
    folder = session / "evidence" / label
    folder.mkdir(parents=True, exist_ok=True)
    outputs = {
        "branch.txt": git_text(root, ["branch", "--show-current"]),
        "head.txt": git_text(root, ["rev-parse", "--short", "HEAD"]),
        "status.txt": git_text(root, ["status", "--short"]),
        "diff-stat.txt": git_text(root, ["diff", "--stat"]),
        "diff.patch": git_text(root, ["diff", "--find-renames", "--unified=20"]),
        "staged-diff.patch": git_text(root, ["diff", "--cached", "--find-renames", "--unified=20"]),
    }
    result: dict[str, str] = {}
    for filename, content in outputs.items():
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        result[filename] = str(path.relative_to(session))
    return result


def copy_assets(session: Path, stage: str, assets: list[str]) -> list[str]:
    copied: list[str] = []
    destination = session / "assets" / slugify(stage)
    for raw in assets:
        source = Path(raw).expanduser().resolve()
        if not source.is_file():
            raise SystemExit(f"Asset does not exist or is not a file: {raw}")
        if is_sensitive_path(source):
            raise SystemExit(f"Refusing to copy a sensitive-looking asset: {source.name}")
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / source.name
        counter = 2
        while target.exists():
            target = destination / f"{source.stem}-{counter}{source.suffix}"
            counter += 1
        shutil.copy2(source, target)
        copied.append(str(target.relative_to(session)))
    return copied


def capture_command(root: Path, session: Path, stage: str, command: list[str]) -> dict[str, Any] | None:
    if not command:
        return None
    if any(is_sensitive_path(Path(item)) for item in command):
        raise SystemExit("Refusing to run a command containing a sensitive-looking path.")
    code, stdout, stderr = run(command, root)
    command_dir = session / "evidence" / "commands"
    command_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%H%M%S')}-{slugify(stage)}.txt"
    path = command_dir / filename
    rendered_command = sanitize(" ".join(command))
    path.write_text(
        safe_text(
            f"$ {rendered_command}\nexit_code={code}\n\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n"
        ),
        encoding="utf-8",
    )
    return {
        "command": rendered_command,
        "exit_code": code,
        "output": str(path.relative_to(session)),
        "captured_at": now_iso(),
    }


def story_score(manifest: dict[str, Any]) -> dict[str, Any]:
    stages = manifest.get("stages", [])
    joined = " ".join(
        str(item.get(key, ""))
        for item in stages
        for key in ("stage", "notes", "decision")
    ).lower()
    conflict_terms = ("fail", "error", "bug", "wrong", "change", "surprise", "失败", "错误", "问题", "改变", "意外", "矛盾")
    conflict = 20 if any(term in joined for term in conflict_terms) else 5
    decisions = sum(bool(item.get("decision")) for item in stages)
    evidence_count = sum(len(item.get("assets", [])) for item in stages) + sum(
        bool(item.get("command")) for item in stages
    )
    decision_score = min(20, decisions * 10)
    evidence_score = min(25, evidence_count * 8 + (5 if stages else 0))
    usefulness = 15 if manifest.get("lesson") else 5 if manifest.get("outcome") else 0
    visual = min(10, sum(len(item.get("assets", [])) for item in stages) * 5)
    completeness = 10 if manifest.get("finished_at") and manifest.get("outcome") else 0
    total = conflict + decision_score + evidence_score + usefulness + visual + completeness
    recommendation = "publish" if total >= 70 else "draft" if total >= 45 else "archive"
    return {
        "total": min(100, total),
        "recommendation": recommendation,
        "dimensions": {
            "conflict": conflict,
            "decision": decision_score,
            "evidence": evidence_score,
            "usefulness": usefulness,
            "visual": visual,
            "completeness": completeness,
        },
    }


def session_claims_and_evidence(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    claims: list[str] = []
    evidence: list[str] = []
    for event in manifest.get("events", []):
        claims.extend(str(item) for item in event.get("claims", []) if str(item).strip())
        evidence.extend(str(item) for item in event.get("evidence_refs", []) if str(item).strip())
    if not manifest.get("events"):
        legacy_claim = manifest.get("lesson") or manifest.get("outcome")
        if legacy_claim:
            claims.append(str(legacy_claim))
        evidence.extend(
            str(item.get("output"))
            for item in manifest.get("commands", [])
            if item.get("output")
        )
        evidence.extend(str(item) for item in manifest.get("assets", []) if str(item).strip())

    def unique(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            key = normalize_key(value)
            if key and key not in seen:
                seen.add(key)
                result.append(sanitize(value))
        return result

    return unique(claims), unique(evidence)


def check_registry(manifest: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    claims, evidence_refs = session_claims_and_evidence(manifest)
    published_claims: dict[str, str] = {}
    published_evidence: set[str] = set()
    for story in registry.get("published_stories", []):
        for claim in story.get("claims", []):
            published_claims.setdefault(normalize_key(str(claim)), str(claim))
        published_evidence.update(normalize_key(str(item)) for item in story.get("evidence_refs", []))
    do_not_repeat = {normalize_key(str(item)) for item in registry.get("do_not_repeat", [])}
    repeated_keys = set(published_claims) | do_not_repeat
    new_claims = [claim for claim in claims if normalize_key(claim) not in repeated_keys]
    repeated_claims = [claim for claim in claims if normalize_key(claim) in repeated_keys]
    new_evidence = [item for item in evidence_refs if normalize_key(item) not in published_evidence]
    repeated_evidence = [item for item in evidence_refs if normalize_key(item) in published_evidence]
    if repeated_claims and not new_claims and not new_evidence:
        recommendation = "archive"
    elif new_claims or new_evidence:
        recommendation = "standalone_story"
    else:
        recommendation = "archive"
    return {
        "new_claims": new_claims,
        "new_evidence": new_evidence,
        "necessary_context": manifest.get("necessary_context", {}),
        "repeated_claims": repeated_claims,
        "repeated_evidence": repeated_evidence,
        "open_loop_closed": [],
        "recommendation": recommendation,
    }


def build_story_plan(
    manifest: dict[str, Any], registry_result: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    claims, evidence = session_claims_and_evidence(manifest)
    phase = manifest.get("phase", "build")
    if manifest.get("archive_only") or registry_result.get("recommendation") == "archive":
        route = "archive"
        reason = "No new claim or evidence remains after story-memory comparison."
    elif claims and not evidence:
        route = "merge_later"
        reason = "A claim exists, but it needs stronger evidence."
    elif phase == "release":
        route = "release_asset"
        reason = "The phase is release and contains new evidence or claims."
    else:
        route = "standalone_story"
        reason = "The phase contains a clear new claim or new evidence."
    memory = config.get("story_memory", {})
    return {
        "route": route,
        "reason": reason,
        "phase": phase,
        "context_limits": {
            "short": memory.get("max_context_ratio_short", 0.15),
            "long": memory.get("max_context_ratio_long", 0.10),
        },
        "novelty": registry_result,
    }


def build_content_readiness(
    manifest: dict[str, Any], plan: dict[str, Any], report: dict[str, Any]
) -> dict[str, Any]:
    _, evidence_refs = session_claims_and_evidence(manifest)
    git_evidence_count = sum(bool(stage.get("evidence")) for stage in manifest.get("stages", []))
    evidence_count = len(evidence_refs) + len(manifest.get("commands", [])) + git_evidence_count
    route = plan.get("route", "archive")
    if not report.get("release_ready", False):
        route = "blocked_privacy"
    return {
        "ready_at": now_iso(),
        "event_count": len(manifest.get("events", [])),
        "evidence_count": evidence_count,
        "asset_count": len(manifest.get("assets", [])),
        "assets_path": "assets",
        "recommended_route": route,
        "privacy_release_ready": bool(report.get("release_ready", False)),
        "visual_review_at_content_gate": bool(
            report.get("visual_review_at_content_gate", report.get("manual_asset_review_required", False))
        ),
        "production_requires_request": True,
        "content_generated": False,
        "publication_confirmed": False,
        "options": ["video", "article", "video_and_article", "archive"],
        "prompt": "Produce video, article, both, or archive this phase?",
    }


def render_stage_brief(
    manifest: dict[str, Any], assets: list[str] | None = None, *, reviewed: bool = False
) -> str:
    event_lines: list[str] = []
    for event in manifest.get("events", []):
        note = project_history_text(str(event.get("notes", ""))).strip()
        if note:
            event_lines.append(
                f"- **{project_history_text(str(event.get('event_type', 'event')))}:** {note}"
            )
    if not event_lines:
        event_lines.append("- No additional key event was needed for this stage.")

    claims, evidence_refs = session_claims_and_evidence(manifest)
    claim_lines = [f"- {project_history_text(item)}" for item in claims] or ["- No separate claim recorded."]
    evidence_lines = [f"- {project_history_text(item)}" for item in evidence_refs] or ["- No separate evidence reference recorded."]
    visual_lines = [f"![Stage evidence]({Path(item).as_posix()})" for item in (assets or [])]
    if not visual_lines:
        visual_lines = ["No visual asset was needed for this stage."]

    footer = (
        "> 这是经过阶段级确认的素材包，不是已发布文章。对外使用前仍需再次核对表述与隐私。\n"
        if reviewed
        else "> 这是私有工作摘要。写入项目进展记录前，请先完成阶段级检查。\n"
    )
    return (
        f"# {project_history_text(str(manifest.get('title', 'Project stage')))}\n\n"
        f"- Project: `{project_history_text(str(manifest.get('project', '')))}`\n"
        f"- Initiative: `{project_history_text(str(manifest.get('initiative', '')))}`\n"
        f"- Phase: `{project_history_text(str(manifest.get('phase', '')))}`\n"
        f"- Source session: `{project_history_text(str(manifest.get('capture_window', {}).get('id', '')))}`\n\n"
        "## 阶段目标 / Goal\n\n"
        f"{project_history_text(str(manifest.get('summary', ''))) or 'No separate goal summary was recorded.'}\n\n"
        "## 阶段结果 / Result\n\n"
        f"{project_history_text(str(manifest.get('outcome', ''))) or 'No result recorded.'}\n\n"
        "## 关键节点 / What mattered\n\n"
        + "\n".join(event_lines)
        + "\n\n## 可复用结论 / Reusable conclusion\n\n"
        f"{project_history_text(str(manifest.get('lesson', ''))) or 'No separate lesson recorded.'}\n\n"
        "## 后续写作观点 / Claims for later writing\n\n"
        + "\n".join(claim_lines)
        + "\n\n## 证据引用 / Evidence references\n\n"
        + "\n".join(evidence_lines)
        + "\n\n## 图片素材 / Visual material\n\n"
        + "\n\n".join(visual_lines)
        + "\n\n"
        + footer
    )


def write_private_stage_brief(session: Path, manifest: dict[str, Any]) -> Path:
    path = session / "stage-brief.md"
    path.write_text(
        render_stage_brief(manifest, list(manifest.get("assets", []))), encoding="utf-8"
    )
    return path


def replace_marked_block(path: Path, marker: str, block: str, heading: str) -> None:
    start = f"<!-- haostory:{marker}:start -->"
    end = f"<!-- haostory:{marker}:end -->"
    rendered = f"{start}\n{block.strip()}\n{end}"
    if path.exists():
        current = path.read_text(encoding="utf-8")
    else:
        current = f"# {heading}\n"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(current):
        updated = pattern.sub(lambda _: rendered, current)
    else:
        updated = current.rstrip() + "\n\n" + rendered + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def stage_date(manifest: dict[str, Any]) -> str:
    value = str(
        manifest.get("capture_window", {}).get("closed_at")
        or manifest.get("finished_at")
        or now_iso()
    )
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", value)
    return match.group(1) if match else datetime.now().astimezone().date().isoformat()


def event_asset_metadata(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for event in manifest.get("events", []):
        for asset in event.get("assets", []):
            metadata[str(asset)] = {
                "caption": project_history_text(str(event.get("notes", ""))).strip(),
                "data_kind": str(event.get("data_kind", "unspecified")),
            }
    return metadata


def inspect_project_readme(root: Path) -> dict[str, Any]:
    path = root / "README.md"
    if not path.is_file():
        return {
            "path": None,
            "startup_documented": False,
            "runtime_url_documented": False,
            "recommendations": ["Add a README with startup instructions and the runtime URL."],
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    startup = bool(
        re.search(
            r"(?:npm|pnpm|yarn|python(?:3)?|uvicorn|docker|make)\s+[\w.:-]+|启动|quick\s*start|getting\s*started",
            text,
            re.IGNORECASE,
        )
    )
    runtime_url = bool(
        re.search(r"https?://(?:localhost|127\.0\.0\.1|\[[0-9a-f:]+\]|[^\s)]+)", text, re.IGNORECASE)
    )
    recommendations: list[str] = []
    if not startup:
        recommendations.append("Document the startup command in README.md.")
    if not runtime_url:
        recommendations.append("Document the runtime or preview URL in README.md.")
    return {
        "path": str(path.relative_to(root)),
        "startup_documented": startup,
        "runtime_url_documented": runtime_url,
        "recommendations": recommendations,
    }


def render_progress_block(
    manifest: dict[str, Any], screenshot_links: list[str], readme_check: dict[str, Any]
) -> str:
    events = []
    for event in manifest.get("events", []):
        note = project_history_text(str(event.get("notes", ""))).strip()
        if note:
            events.append(f"- {note}")
    completed = "\n".join(events) or "- 本阶段结果已记录；没有额外的关键节点。"
    next_steps = [project_history_text(str(item)).strip() for item in manifest.get("next_steps", [])]
    todos = "\n".join(f"- {item}" for item in next_steps if item) or "- 暂无明确待办。"
    screenshots = "\n".join(f"- [{Path(item).name}]({item})" for item in screenshot_links)
    if not screenshots:
        screenshots = "- 本阶段不需要图片。"
    readme_notes = readme_check.get("recommendations", [])
    readme_status = "README 已包含启动方式和运行地址。" if not readme_notes else " ".join(readme_notes)
    return (
        f"## {stage_date(manifest)} · {project_history_text(str(manifest.get('title', 'Project stage')))}\n\n"
        f"- 阶段：`{project_history_text(str(manifest.get('phase', '')) or 'unspecified')}`\n"
        f"- 会话：`{project_history_text(str(manifest.get('capture_window', {}).get('id', '')) or 'legacy')}`\n\n"
        "### 用户遇到的问题\n\n"
        f"{project_history_text(str(manifest.get('summary', ''))) or '未单独记录。'}\n\n"
        "### 这次解决了什么\n\n"
        f"{project_history_text(str(manifest.get('outcome', ''))) or '未单独记录。'}\n\n"
        "### 为什么调整方案\n\n"
        f"{project_history_text(str(manifest.get('lesson', ''))) or '本阶段没有单独记录方案调整原因。'}\n\n"
        "### 已完成\n\n"
        f"{completed}\n\n"
        "### 待办\n\n"
        f"{todos}\n\n"
        "### 截图\n\n"
        f"{screenshots}\n\n"
        "### README 核对\n\n"
        f"{readme_status}\n\n"
        "> 建议把本阶段代码、进展记录和截图放在同一次提交中。HaoStory 未执行 commit、push、上传或发布。"
    )


def share_stage(
    root: Path,
    session: Path,
    manifest: dict[str, Any],
    config: dict[str, Any],
    *,
    selected_assets: list[str] | None = None,
    fallback_data_kind: str | None = None,
) -> dict[str, Any]:
    if manifest.get("capture_window", {}).get("status") != "closed":
        raise SystemExit("Close the phase before preparing a shared stage package.")
    history = config.get("project_history", {})
    if not history.get("enabled", False):
        raise SystemExit("Project history is disabled. Run `enable` for this named project first.")
    report = audit_session(session)
    if not report.get("release_ready", False):
        raise SystemExit("Privacy audit blocked this stage package; review privacy-report.json first.")

    progress_file, screenshots_root = project_history_paths(root, config, create=True)
    available = [str(item) for item in manifest.get("assets", [])]
    requested = list(dict.fromkeys(selected_assets or []))
    if requested:
        missing = [item for item in requested if item not in available]
        if missing:
            raise SystemExit(f"Selected assets are not in this session: {', '.join(missing)}")
        chosen = requested
    else:
        if len(available) > 3:
            raise SystemExit(
                "This phase has more than three screenshots. Pass --asset up to three times using: "
                + ", ".join(available)
            )
        chosen = available
    if len(chosen) > 3:
        raise SystemExit("A shared stage may contain at most three screenshots.")

    metadata = event_asset_metadata(manifest)
    for raw in chosen:
        kind = metadata.get(raw, {}).get("data_kind", "unspecified")
        if kind == "unspecified" and not fallback_data_kind:
            raise SystemExit(
                f"Screenshot data type is unknown for {raw}. Pass --data-kind real, demo, or mixed."
            )

    date_dir = screenshots_root / stage_date(manifest)
    if date_dir.is_symlink():
        raise SystemExit("Project screenshot date directory must not be a symlink.")
    if chosen:
        date_dir.mkdir(parents=True, exist_ok=True)
    copied_assets: list[dict[str, str]] = []
    session_root = session.resolve()
    for raw in chosen:
        relative = Path(str(raw))
        if relative.is_absolute() or not relative.parts or relative.parts[0] != "assets" or ".." in relative.parts:
            raise SystemExit(f"Invalid session asset path: {raw}")
        source = session / relative
        if source.is_symlink() or not source.is_file():
            raise SystemExit(f"Session asset is missing or unsafe: {raw}")
        try:
            source.resolve().relative_to(session_root)
        except ValueError as exc:
            raise SystemExit(f"Session asset escapes its session: {raw}") from exc
        target = date_dir / f"{slugify(session.name)}-{relative.name}"
        if target.is_symlink():
            raise SystemExit(f"Project screenshot target is a symlink: {target}")
        shutil.copy2(source, target)
        item = metadata.get(raw, {})
        copied_assets.append(
            {
                "source": raw,
                "path": str(target.relative_to(root)),
                "caption": item.get("caption") or project_history_text(str(manifest.get("outcome", "Stage screenshot"))),
                "data_kind": item.get("data_kind")
                if item.get("data_kind") not in {None, "unspecified"}
                else str(fallback_data_kind),
            }
        )

    screenshot_index = date_dir / "README.md"
    marker = slugify(session.name)
    rows: list[str] = []
    for item in copied_assets:
        caption = item["caption"].replace("|", "\\|")
        phase = project_history_text(str(manifest.get("phase", "")) or "unspecified")
        rows.append(
            f"| [{Path(item['path']).name}]({Path(item['path']).name}) | {caption} | "
            f"`{item['data_kind']}` | `{phase}` |"
        )
    screenshot_block = (
        f"## {project_history_text(str(manifest.get('title', 'Project stage')))}\n\n"
        "| 截图 | 说明 | 数据 | 阶段 |\n"
        "|---|---|---|---|\n"
        + ("\n".join(rows) if rows else "| — | 本阶段不需要图片 | `not-applicable` | — |")
    )
    if copied_assets:
        replace_marked_block(
            screenshot_index,
            marker,
            screenshot_block,
            f"Screenshots · {stage_date(manifest)}",
        )

    readme_check = inspect_project_readme(root) if manifest.get("type") == "software" else {
        "path": "README.md" if (root / "README.md").exists() else None,
        "startup_documented": None,
        "runtime_url_documented": None,
        "recommendations": [],
    }
    screenshot_links = [
        Path(os.path.relpath(root / item["path"], progress_file.parent)).as_posix()
        for item in copied_assets
    ]
    progress_block = render_progress_block(manifest, screenshot_links, readme_check)
    replace_marked_block(progress_file, marker, progress_block, "Project progress")

    generated = [str(progress_file.relative_to(root))]
    if copied_assets:
        generated.append(str(screenshot_index.relative_to(root)))
    generated.extend(item["path"] for item in copied_assets)
    manifest["project_history"] = {
        "prepared_at": now_iso(),
        "progress_file": str(progress_file.relative_to(root)),
        "screenshots_directory": str(date_dir.relative_to(root)) if copied_assets else None,
        "asset_count": len(copied_assets),
        "confirmed_for_project_history": True,
        "uploaded": False,
        "committed": False,
    }
    save_manifest(session, manifest)
    return {
        "status": "prepared",
        "progress_file": str(progress_file),
        "screenshots_directory": str(date_dir) if copied_assets else None,
        "asset_count": len(copied_assets),
        "files": generated,
        "commit_scope": generated,
        "git_commit_recommended": True,
        "readme_check": readme_check,
        "committed": False,
        "pushed": False,
        "uploaded": False,
    }


def remember_event(
    session: Path,
    manifest: dict[str, Any],
    *,
    event_type: str,
    notes: str,
    novelty_key: str,
    claims: list[str],
    evidence_refs: list[str],
    assets: list[str],
    data_kind: str,
    max_events: int,
    force: bool,
) -> dict[str, Any]:
    window = manifest.get("capture_window", {})
    status = window.get("status", "active")
    if status == "closed":
        raise SystemExit("Capture window is closed; start a new phase instead of changing closed evidence.")
    if status != "active" and not force:
        raise SystemExit(f"Capture window is {status}; resume it or pass --force for an explicit user checkpoint.")
    events = manifest.setdefault("events", [])
    identity = f"{event_type}:{normalize_key(novelty_key)}"
    captured_at = now_iso()
    for event in events:
        if event.get("dedupe_identity") == identity:
            copied_assets = copy_assets(session, event_type, assets)
            event["occurrence_count"] = int(event.get("occurrence_count", 1)) + 1
            event["last_seen_at"] = captured_at
            for field, additions in (
                ("claims", claims),
                ("evidence_refs", evidence_refs),
                ("assets", copied_assets),
            ):
                existing = event.setdefault(field, [])
                existing_keys = {normalize_key(str(item)) for item in existing}
                for addition in additions:
                    if normalize_key(addition) not in existing_keys:
                        existing.append(sanitize(addition))
                        existing_keys.add(normalize_key(addition))
            manifest.setdefault("assets", []).extend(copied_assets)
            if data_kind != "unspecified":
                event["data_kind"] = data_kind
            for stage in manifest.setdefault("stages", []):
                if stage.get("event_id") == event.get("event_id"):
                    stage.setdefault("assets", []).extend(copied_assets)
                    break
            save_manifest(session, manifest)
            return {
                "action": "folded",
                "event_id": event["event_id"],
                "occurrence_count": event["occurrence_count"],
                "assets": copied_assets,
            }
    if max_events > 0 and len(events) >= max_events and not force:
        return {
            "action": "skipped",
            "reason": "event_budget_reached",
            "event_count": len(events),
            "max_events_per_phase": max_events,
            "ask_only_if_critical": True,
        }
    copied_assets = copy_assets(session, event_type, assets)
    event_id = f"event-{len(events) + 1:03d}"
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "notes": sanitize(notes),
        "novelty_key": sanitize(novelty_key),
        "dedupe_identity": identity,
        "occurrence_count": 1,
        "claims": [sanitize(item) for item in claims],
        "evidence_refs": [sanitize(item) for item in evidence_refs],
        "assets": copied_assets,
        "data_kind": data_kind,
        "captured_at": captured_at,
        "last_seen_at": captured_at,
    }
    events.append(event)
    manifest.setdefault("stages", []).append(
        {
            "type": "event",
            "stage": event_type,
            "notes": event["notes"],
            "decision": event["claims"][0] if event["claims"] else "",
            "evidence": {},
            "assets": copied_assets,
            "captured_at": captured_at,
            "event_id": event_id,
        }
    )
    manifest.setdefault("assets", []).extend(copied_assets)
    save_manifest(session, manifest)
    append_timeline(
        session,
        f"{captured_at} · {event_type}",
        [
            ("Notes", event["notes"]),
            ("Novelty key", event["novelty_key"]),
            ("Assets", ", ".join(copied_assets) or "—"),
        ],
    )
    return {"action": "recorded", "event_id": event_id, "occurrence_count": 1, "assets": copied_assets}


AUDIT_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("credential_url", "high", re.compile(r"https?://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE)),
    ("private_key", "high", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("secret_token", "high", re.compile(r"\b(?:sk-|ghp_|github_pat_|AKIA)[A-Za-z0-9_-]{12,}\b")),
    ("bearer_token", "high", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE)),
    ("absolute_user_path", "medium", re.compile(r"/(?:Users|home)/[^/\s]+/")),
    ("email", "medium", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
    ("redaction_marker", "low", re.compile(r"<(?:secret|email|phone|ip|credentials|private-key)-redacted>")),
)


def audit_session(session: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for path in sorted(session.rglob("*")):
        if not path.is_file() or path.name == "privacy-report.json":
            continue
        if path.suffix.lower() not in {".json", ".md", ".txt", ".patch", ".log"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, severity, pattern in AUDIT_PATTERNS:
            matches = list(pattern.finditer(text))
            if matches:
                findings.append(
                    {
                        "type": name,
                        "severity": severity,
                        "file": str(path.relative_to(session)),
                        "count": len(matches),
                    }
                )
    assets = [str(path.relative_to(session)) for path in (session / "assets").rglob("*") if path.is_file()] if (session / "assets").exists() else []
    high = sum(item["severity"] == "high" for item in findings)
    report = {
        "schema": SCHEMA,
        "audited_at": now_iso(),
        "release_ready": high == 0,
        "manual_asset_review_required": bool(assets),
        "asset_review_gate": "final_content" if assets else "none",
        "visual_review_at_content_gate": bool(assets),
        "assets": assets,
        "findings": findings,
        "note": (
            "Best-effort text scan only. Visual assets are reviewed in the finished content, "
            "not approved one by one. Review the final Git history before publication."
        ),
    }
    (session / "privacy-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def brand_lines(config: dict[str, Any], language: str) -> str:
    brand = config.get("brand", {})
    name = brand.get("name_zh") if language == "zh-CN" else brand.get("name")
    name = name or brand.get("name") or brand.get("name_zh")
    website = brand.get("website", "")
    cta = brand.get("cta_zh") if language == "zh-CN" else brand.get("cta_en")
    lines = []
    if name:
        lines.append(f"{('作者' if language == 'zh-CN' else 'By')}: {name}")
    if website:
        lines.append(website)
    if cta:
        lines.append(cta)
    commercial = config.get("commercial_note", {})
    if commercial.get("enabled"):
        lines.append(commercial.get(language, ""))
    return "\n\n".join(line for line in lines if line)


def stage_bullets(manifest: dict[str, Any], language: str) -> str:
    lines = []
    for item in manifest.get("stages", []):
        stage = item.get("stage", "checkpoint")
        notes = item.get("notes") or "—"
        decision = item.get("decision")
        line = f"- **{stage}** — {notes}"
        if decision:
            label = "判断" if language == "zh-CN" else "Decision"
            line += f" ({label}: {decision})"
        lines.append(line)
    return "\n".join(lines) or ("- 暂无检查点。" if language == "zh-CN" else "- No checkpoints yet.")


def build_exports(
    root: Path,
    session: Path,
    manifest: dict[str, Any],
    config: dict[str, Any],
    report: dict[str, Any],
) -> Path:
    exports = session / "exports"
    exports.mkdir(exist_ok=True)
    title = manifest.get("title", "Untitled story")
    summary = manifest.get("summary") or "—"
    outcome = manifest.get("outcome") or "—"
    lesson = manifest.get("lesson") or "—"
    score = story_score(manifest)
    manifest["story_score"] = score
    novelty = check_registry(manifest, load_registry(root, config))
    plan = build_story_plan(manifest, novelty, config)
    publication_recommendation = plan["route"] if report.get("release_ready") else "blocked_privacy"

    zh_brand = brand_lines(config, "zh-CN")
    en_brand = brand_lines(config, "en")
    zh = f"""# {title}

## 为什么做

{summary}

## 过程中发生了什么

{stage_bullets(manifest, 'zh-CN')}

## 最终结果

{outcome}

## 判断发生了什么变化

{lesson}

## 可验证证据

- 检查点：{len(manifest.get('stages', []))}
- 命令记录：{len(manifest.get('commands', []))}
- 视觉素材：{len(manifest.get('assets', []))}
- 故事评分：{score['total']}/100（建议：{score['recommendation']}）

> 这是 HaoStory 根据真实过程记录生成的草稿。发布前请核对事实、改善叙事并检查隐私报告。

{zh_brand}
"""
    en = f"""# {title}

## Why this work mattered

{summary}

## What happened

{stage_bullets(manifest, 'en')}

## Outcome

{outcome}

## What changed in our judgment

{lesson}

## Verifiable evidence

- Checkpoints: {len(manifest.get('stages', []))}
- Command records: {len(manifest.get('commands', []))}
- Visual assets: {len(manifest.get('assets', []))}
- Story score: {score['total']}/100 ({score['recommendation']})

> This is a HaoStory scaffold generated from real process evidence. Verify facts, improve the narrative, and review the privacy report before publishing.

{en_brand}
"""
    zh_video = f"""# {title}｜短视频脚本

## 0–2 秒：冲突或结果

{outcome}

## 2–8 秒：为什么要做

{summary}

## 8–20 秒：关键变化

{stage_bullets(manifest, 'zh-CN')}

## 20–50 秒：证据与结果

展示测试输出、关键差异和人工检查过的前后对比素材。不要用无法验证的效果描述。

## 50–60 秒：新的判断

{lesson}

{zh_brand}
"""
    en_video = f"""# {title} | Short video script

## 0–2s: conflict or result

{outcome}

## 2–8s: intent

{summary}

## 8–20s: decisive change

{stage_bullets(manifest, 'en')}

## 20–50s: proof

Show test output, a focused diff, and manually reviewed before/after visuals. Avoid claims the evidence cannot support.

## 50–60s: changed judgment

{lesson}

{en_brand}
"""
    social_zh = f"# {title}\n\n{outcome}\n\n这次真正值得记录的不是操作步骤，而是：{lesson}\n\n{zh_brand}\n"
    social_en = f"# {title}\n\n{outcome}\n\nThe useful story is not the activity log. It is the changed judgment: {lesson}\n\n{en_brand}\n"

    files = {
        "article.zh-CN.md": zh,
        "article.en.md": en,
        "video-script.zh-CN.md": zh_video,
        "video-script.en.md": en_video,
        "social.zh-CN.md": social_zh,
        "social.en.md": social_en,
    }
    for filename, content in files.items():
        (exports / filename).write_text(content.strip() + "\n", encoding="utf-8")

    package = {
        "schema": SCHEMA,
        "project": manifest.get("project"),
        "title": title,
        "summary": summary,
        "outcome": outcome,
        "lesson": lesson,
        "story_score": score,
        "privacy": {
            "release_ready": report.get("release_ready", False),
            "manual_asset_review_required": report.get("manual_asset_review_required", False),
        },
        "novelty": novelty,
        "story_plan": plan,
        "publication_recommendation": publication_recommendation,
        "stages": manifest.get("stages", []),
        "assets": manifest.get("assets", []),
        "exports": list(files),
    }
    (exports / "content-package.json").write_text(
        json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_manifest(session, manifest)
    return exports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture real work and export bilingual story assets")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("setup", help="Create a safe project configuration and ignore local journals")
    studio_command = sub.add_parser("studio", help="Open the local HaoStory Studio content console")
    studio_command.add_argument("--port", type=int, default=0)
    studio_command.add_argument("--no-open", action="store_true")
    studio_command.add_argument(
        "--host-context",
        help="Agent-provided JSON containing recent conversation metadata only",
    )
    studio_command.add_argument("--check", action="store_true", help="Validate Studio without starting a server")

    studio_job = sub.add_parser("studio-job", help="Read or complete a Studio production request")
    studio_job_sub = studio_job.add_subparsers(dest="studio_job_action", required=True)
    studio_job_sub.add_parser("latest", help="Read the newest Studio production request")
    studio_job_wait = studio_job_sub.add_parser("wait", help="Wait for the user to submit a new Studio request")
    studio_job_wait.add_argument("--after", default="")
    studio_job_wait.add_argument("--timeout", type=float, default=600)
    studio_job_show = studio_job_sub.add_parser("show", help="Read one Studio production request")
    studio_job_show.add_argument("--job", required=True)
    studio_job_complete = studio_job_sub.add_parser("complete", help="Register generated local outputs")
    studio_job_complete.add_argument("--job", required=True)
    studio_job_complete.add_argument("--output", action="append", required=True)

    enable = sub.add_parser("enable", help="Explicitly enable lightweight capture for this project")
    enable.add_argument("--history-dir")
    enable.add_argument("--progress-file", default="docs/progress.md")
    enable.add_argument("--screenshots-dir", default="docs/screenshots")
    sub.add_parser("disable", help="Pause capture for this project without deleting existing records")

    suggest = sub.add_parser("suggest-start", help="Deterministically route an assisted-auto start")
    suggest.add_argument("--title", required=True)
    suggest.add_argument("--summary", default="")
    suggest.add_argument("--type", choices=("software", "product", "content", "research"), default="software")
    suggest.add_argument("--initiative", required=True)
    suggest.add_argument("--phase", choices=PHASES, required=True)
    suggest.add_argument("--work-kind", choices=WORK_KINDS, default="meaningful")
    suggest.add_argument("--session")
    suggest.add_argument("--parent-session")

    start = sub.add_parser("start", help="Start a HaoStory session")
    start.add_argument("--title", required=True)
    start.add_argument("--summary", default="")
    start.add_argument("--type", choices=("software", "product", "content", "research"), default="software")
    start.add_argument("--session")
    start.add_argument("--initiative")
    start.add_argument("--phase", choices=PHASES)
    start.add_argument("--parent-session")

    checkpoint = sub.add_parser("checkpoint", help="Capture a meaningful checkpoint")
    checkpoint.add_argument("--session")
    checkpoint.add_argument("--stage", required=True)
    checkpoint.add_argument("--notes", required=True)
    checkpoint.add_argument("--decision", default="")
    checkpoint.add_argument("--asset", action="append", default=[])
    checkpoint.add_argument("--run", nargs=argparse.REMAINDER, default=[])

    finish = sub.add_parser("finish", help="Finish the latest session")
    finish.add_argument("--session")
    finish.add_argument("--outcome", required=True)
    finish.add_argument("--lesson", required=True)
    finish.add_argument("--asset", action="append", default=[])

    remember = sub.add_parser("remember", help="Record or fold a high-confidence observable event")
    remember.add_argument("--session")
    remember.add_argument("--event", choices=HIGH_CONFIDENCE_EVENTS, required=True)
    remember.add_argument("--notes", required=True)
    remember.add_argument("--novelty-key", required=True)
    remember.add_argument("--claim", action="append", default=[])
    remember.add_argument("--evidence-ref", action="append", default=[])
    remember.add_argument("--asset", action="append", default=[])
    remember.add_argument("--data-kind", choices=DATA_KINDS, default="unspecified")
    remember.add_argument("--force", action="store_true")

    pause = sub.add_parser("pause", help="Pause automatic capture without ending the phase")
    pause.add_argument("--session")
    pause.add_argument("--reason", required=True)

    resume = sub.add_parser("resume", help="Resume a paused capture window")
    resume.add_argument("--session")

    close = sub.add_parser("close-phase", help="Close a phase without exporting or publishing")
    close.add_argument("--session")
    close.add_argument("--result", required=True)
    close.add_argument("--lesson", default="")
    close.add_argument("--todo", action="append", default=[])
    close.add_argument("--handoff", action="store_true")

    share = sub.add_parser("share-stage", help="Prepare a reviewed progress-and-screenshot record locally")
    share.add_argument("--session")
    share.add_argument("--confirmed", action="store_true")
    share.add_argument("--asset", action="append", default=[])
    share.add_argument("--data-kind", choices=("real", "demo", "mixed"))

    archive_only = sub.add_parser("archive-only", help="Mark a session as never recommended for publication")
    archive_only.add_argument("--session")
    archive_only.add_argument("--reason", required=True)

    plan = sub.add_parser("story-plan", help="Route a phase based on novelty and evidence")
    plan.add_argument("--session")

    registry = sub.add_parser("registry", help="Check or update confirmed published-story memory")
    registry_sub = registry.add_subparsers(dest="registry_action", required=True)
    registry_check = registry_sub.add_parser("check", help="Compare a session with published story memory")
    registry_check.add_argument("--session")
    registry_do_not_repeat = registry_sub.add_parser(
        "do-not-repeat", help="Add reviewed background that must not be repeated"
    )
    registry_do_not_repeat.add_argument("--text", required=True)
    registry_publish = registry_sub.add_parser("publish", help="Register a human-confirmed published story")
    registry_publish.add_argument("--session")
    registry_publish.add_argument("--story", required=True)
    registry_publish.add_argument("--channel", action="append", required=True)
    registry_publish.add_argument("--claim", action="append", default=[])
    registry_publish.add_argument("--evidence-ref", action="append", default=[])
    registry_publish.add_argument("--published-at")
    registry_publish.add_argument("--confirmed", action="store_true")

    for name in ("audit", "export"):
        command = sub.add_parser(name, help=f"{name.title()} a HaoStory session")
        command.add_argument(
            "session_path",
            nargs="?",
            help="Explicit human-authorized session directory; may be outside the current project",
        )
        command.add_argument("--session")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = project_root(Path.cwd())

    if args.action == "setup":
        path = setup_project(root)
        print(path)
        return 0

    if args.action == "studio":
        assets_root = Path(__file__).resolve().parents[1] / "assets" / "studio"
        host_context = studio.load_host_context(
            Path(args.host_context) if args.host_context else None
        )
        if args.check:
            discovered = studio.discover_sources(root)
            print(
                json.dumps(
                    {
                        "product": studio.PRODUCT_NAME,
                        "project": root.name,
                        "source_count": len(discovered["sources"]),
                        "conversation_count": len(host_context["conversations"]),
                        "capture_enabled": False,
                        "server_started": False,
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        if not 0 <= args.port <= 65535:
            raise SystemExit("Studio port must be between 0 and 65535.")
        studio.run_server(
            root,
            assets_root,
            port=args.port,
            open_browser=not args.no_open,
            host_context=host_context,
        )
        return 0

    if args.action == "studio-job":
        if args.studio_job_action == "latest":
            value = studio.latest_job(root)
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0
        if args.studio_job_action == "wait":
            value = studio.wait_for_job(root, args.after, args.timeout)
            print(
                json.dumps(
                    value if value is not None else {"status": "timeout"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.studio_job_action == "show":
            value = studio.load_job(root, args.job)
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0
        if args.studio_job_action == "complete":
            value = studio.complete_job(root, args.job, args.output)
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0

    if args.action == "enable":
        setup_project(root)
        config = load_config(root)
        config.setdefault("capture", {}).update(mode="assisted-auto", auto_start=True)
        config["capture"].setdefault("max_events_per_phase", 4)
        if args.history_dir:
            legacy_base = Path(args.history_dir)
            progress_file = str(legacy_base / "progress.md")
            screenshots_directory = str(legacy_base / "screenshots")
            history_directory = args.history_dir
        else:
            progress_file = args.progress_file
            screenshots_directory = args.screenshots_dir
            history_directory = str(Path(progress_file).parent)
        config.setdefault("project_history", {}).update(
            enabled=True,
            directory=history_directory,
            progress_file=progress_file,
            screenshots_directory=screenshots_directory,
            requires_stage_confirmation=True,
            auto_commit=False,
            auto_push=False,
            auto_upload=False,
        )
        progress_path, screenshots_path = project_history_paths(root, config)
        save_json(root / CONFIG_FILE, config)
        print(
            json.dumps(
                {
                    "mode": "assisted-auto",
                    "history_directory": history_directory,
                    "progress_file": str(progress_path.relative_to(root)),
                    "screenshots_directory": str(screenshots_path.relative_to(root)),
                    "max_events_per_phase": config["capture"]["max_events_per_phase"],
                    "committed": False,
                    "pushed": False,
                    "uploaded": False,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.action == "disable":
        setup_project(root)
        config = load_config(root)
        config.setdefault("capture", {}).update(mode="off", auto_start=False)
        save_json(root / CONFIG_FILE, config)
        print(
            json.dumps(
                {
                    "mode": "off",
                    "existing_records_preserved": True,
                    "project_history_preserved": True,
                    "deleted": False,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.action == "suggest-start" and not (root / CONFIG_FILE).exists():
        print(
            json.dumps(
                {
                    "mode": "off",
                    "initiative": sanitize(args.initiative),
                    "phase": args.phase,
                    "notice_required": True,
                    "action": "ignore",
                    "reason": "HaoStory is not enabled in this project.",
                },
                ensure_ascii=False,
            )
        )
        return 0

    ensure_gitignore(root)
    config = load_config(root)

    capture_config = config.get("capture", {})
    mode = capture_config.get("mode", "assisted-auto")
    if mode not in CAPTURE_MODES:
        raise SystemExit(f"Invalid capture mode: {mode}")

    if args.action == "suggest-start":
        decision: dict[str, Any] = {
            "mode": mode,
            "initiative": sanitize(args.initiative),
            "phase": args.phase,
            "notice_required": bool(capture_config.get("require_notice", True)),
        }
        if mode == "off":
            decision.update(action="ignore", reason="Capture mode is off.")
        elif args.work_kind in AUTO_START_EXCLUSIONS:
            decision.update(action="ignore", reason=f"{args.work_kind} work does not justify a capture window.")
        else:
            existing = find_matching_window(root, args.initiative, args.phase)
            if existing:
                decision.update(
                    action="resume_suggested",
                    session=str(existing),
                    reason="An active or paused window already covers this initiative and phase.",
                )
            elif mode == "manual" or not capture_config.get("auto_start", True):
                decision.update(action="start_suggested", reason="Human confirmation is required by project mode.")
            else:
                session = create_capture_session(
                    root,
                    config,
                    title=args.title,
                    summary=args.summary,
                    work_type=args.type,
                    session_name=args.session,
                    initiative=args.initiative,
                    phase=args.phase,
                    parent_session=args.parent_session,
                )
                decision.update(
                    action="started",
                    session=str(session),
                    notice=f"HaoStory started local capture for {args.initiative}/{args.phase}.",
                )
        print(json.dumps(decision, ensure_ascii=False))
        return 0

    if args.action == "start":
        start_config = config
        if mode == "off":
            start_config = deep_merge(config, {"capture": {"mode": "manual"}})
        session = create_capture_session(
            root,
            start_config,
            title=args.title,
            summary=args.summary,
            work_type=args.type,
            session_name=args.session,
            initiative=args.initiative,
            phase=args.phase,
            parent_session=args.parent_session,
        )
        print(session)
        return 0

    if args.action == "registry" and args.registry_action == "do-not-repeat":
        registry = load_registry(root, config)
        value = sanitize(args.text).strip()
        if not value:
            raise SystemExit("do-not-repeat text must not be empty.")
        entries = registry.setdefault("do_not_repeat", [])
        existing = {normalize_key(str(item)) for item in entries}
        if normalize_key(value) in existing:
            action = "already_present"
        else:
            entries.append(value)
            save_json(registry_path(root, config), registry)
            action = "recorded"
        print(json.dumps({"action": action, "text": value}, ensure_ascii=False))
        return 0

    if args.action in {"audit", "export"} and args.session_path:
        session = Path(args.session_path).expanduser().resolve()
    else:
        session = resolve_session(root, getattr(args, "session", None))
    manifest = load_manifest(session)

    if args.action == "share-stage":
        if not args.confirmed:
            raise SystemExit(
                "share-stage writes reviewed materials into the project record; pass --confirmed after stage-level review."
            )
        print(
            json.dumps(
                share_stage(
                    root,
                    session,
                    manifest,
                    config,
                    selected_assets=args.asset,
                    fallback_data_kind=args.data_kind,
                ),
                ensure_ascii=False,
            )
        )
        return 0

    if args.action == "archive-only":
        marked_at = now_iso()
        manifest["archive_only"] = True
        manifest["archive_only_reason"] = sanitize(args.reason)
        manifest["archive_only_at"] = marked_at
        save_manifest(session, manifest)
        append_timeline(session, f"{marked_at} · archive only", [("Reason", args.reason)])
        print(
            json.dumps(
                {
                    "session": str(session),
                    "archive_only": True,
                    "reason": manifest["archive_only_reason"],
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.action == "checkpoint":
        label = f"checkpoints/{datetime.now().strftime('%H%M%S')}-{slugify(args.stage)}"
        evidence = capture_git(root, session, label)
        assets = copy_assets(session, args.stage, args.asset)
        command = capture_command(root, session, args.stage, args.run)
        item = {
            "type": "checkpoint",
            "stage": sanitize(args.stage),
            "notes": sanitize(args.notes),
            "decision": sanitize(args.decision),
            "evidence": evidence,
            "assets": assets,
            "command": command,
            "captured_at": now_iso(),
        }
        manifest.setdefault("stages", []).append(item)
        manifest.setdefault("assets", []).extend(assets)
        if command:
            manifest.setdefault("commands", []).append(command)
        save_manifest(session, manifest)
        append_timeline(session, f"{now_iso()} · {args.stage}", [("Notes", args.notes), ("Decision", args.decision)])
        print(session)
        return 0

    if args.action == "finish":
        evidence = capture_git(root, session, "finish")
        assets = copy_assets(session, "finish", args.asset)
        manifest.update(
            {
                "outcome": sanitize(args.outcome),
                "lesson": sanitize(args.lesson),
                "finished_at": now_iso(),
            }
        )
        manifest.setdefault("stages", []).append(
            {"type": "finish", "stage": "finish", "notes": manifest["outcome"], "decision": manifest["lesson"], "evidence": evidence, "assets": assets, "captured_at": now_iso()}
        )
        manifest.setdefault("assets", []).extend(assets)
        if manifest.get("capture_window"):
            manifest["capture_window"].update(status="closed", closed_at=now_iso(), close_reason="finish")
        manifest["story_score"] = story_score(manifest)
        save_manifest(session, manifest)
        append_timeline(session, f"{now_iso()} · finish", [("Outcome", args.outcome), ("Lesson", args.lesson)])
        print(session)
        return 0

    if args.action == "remember":
        result = remember_event(
            session,
            manifest,
            event_type=args.event,
            notes=args.notes,
            novelty_key=args.novelty_key,
            claims=args.claim,
            evidence_refs=args.evidence_ref,
            assets=args.asset,
            data_kind=args.data_kind,
            max_events=int(capture_config.get("max_events_per_phase", 4)),
            force=args.force,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.action == "pause":
        captured_at = now_iso()
        window = manifest.setdefault(
            "capture_window",
            {
                "id": session.name,
                "mode": "manual",
                "status": "active",
                "started_at": manifest.get("started_at", captured_at),
                "pause_history": [],
            },
        )
        if window.get("status") != "active":
            raise SystemExit(f"Only an active capture window can be paused; current status is {window.get('status')}.")
        window["status"] = "paused"
        window["paused_at"] = captured_at
        window.setdefault("pause_history", []).append(
            {"paused_at": captured_at, "reason": sanitize(args.reason)}
        )
        save_manifest(session, manifest)
        append_timeline(session, f"{captured_at} · pause", [("Reason", args.reason)])
        print(json.dumps({"status": "paused", "session": str(session)}, ensure_ascii=False))
        return 0

    if args.action == "resume":
        window = manifest.get("capture_window")
        if not window:
            raise SystemExit("This V1 session has no capture window to resume; use checkpoint or start a V2 phase.")
        if window.get("status") != "paused":
            raise SystemExit(f"Only a paused capture window can be resumed; current status is {window.get('status')}.")
        resumed_at = now_iso()
        window["status"] = "active"
        window["resumed_at"] = resumed_at
        history = window.setdefault("pause_history", [])
        if history and "resumed_at" not in history[-1]:
            history[-1]["resumed_at"] = resumed_at
        save_manifest(session, manifest)
        append_timeline(session, f"{resumed_at} · resume", [("Status", "active")])
        print(json.dumps({"status": "active", "session": str(session)}, ensure_ascii=False))
        return 0

    if args.action == "close-phase":
        closed_at = now_iso()
        if manifest.get("capture_window", {}).get("status") == "closed":
            raise SystemExit("Capture window is already closed.")
        evidence = capture_git(root, session, "close-phase")
        manifest["outcome"] = sanitize(args.result)
        if args.lesson:
            manifest["lesson"] = sanitize(args.lesson)
        manifest["next_steps"] = [sanitize(item) for item in args.todo if sanitize(item).strip()]
        manifest["finished_at"] = closed_at
        window = manifest.setdefault(
            "capture_window",
            {
                "id": session.name,
                "mode": "manual",
                "started_at": manifest.get("started_at", closed_at),
                "pause_history": [],
            },
        )
        window.update(
            status="closed",
            closed_at=closed_at,
            close_reason="handoff" if args.handoff else "phase_result",
        )
        manifest.setdefault("stages", []).append(
            {
                "type": "close_phase",
                "stage": "close_phase",
                "notes": manifest["outcome"],
                "decision": manifest.get("lesson", ""),
                "evidence": evidence,
                "assets": [],
                "captured_at": closed_at,
            }
        )
        manifest["story_score"] = story_score(manifest)
        save_manifest(session, manifest)
        append_timeline(
            session,
            f"{closed_at} · close phase",
            [("Result", args.result), ("Reason", window["close_reason"])],
        )
        report = audit_session(session)
        novelty = check_registry(manifest, load_registry(root, config))
        plan = build_story_plan(manifest, novelty, config)
        readiness = build_content_readiness(manifest, plan, report)
        readiness["project_history_requires_confirmation"] = True
        readiness["project_history_enabled"] = bool(
            config.get("project_history", {}).get("enabled", False)
        )
        if readiness["project_history_enabled"]:
            readiness["options"].append("prepare_project_history")
        manifest["content_readiness"] = readiness
        stage_brief = write_private_stage_brief(session, manifest)
        save_manifest(session, manifest)
        response_readiness = dict(readiness)
        response_readiness["assets_path"] = str(session / "assets")
        response_readiness["prompt"] = (
            f"Phase complete. Assets are in {session / 'assets'}. "
            "Produce video, article, both, archive, or prepare a reviewed project record?"
        )
        print(
            json.dumps(
                {
                    "status": "closed",
                    "session": str(session),
                    "published": False,
                    "exported": False,
                    "content_generated": False,
                    "reason": window["close_reason"],
                    "stage_brief": str(stage_brief),
                    "project_history_next_action": {
                        "command": "share-stage",
                        "session": session.name,
                        "requires_confirmation": True,
                    },
                    "content_readiness": response_readiness,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.action in {"story-plan", "registry"}:
        registry = load_registry(root, config)
        result = check_registry(manifest, registry)
        if args.action == "story-plan":
            print(json.dumps(build_story_plan(manifest, result, config), ensure_ascii=False, indent=2))
            return 0
        if args.registry_action == "check":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not args.confirmed:
            raise SystemExit("registry publish records a human-confirmed fact; pass --confirmed after confirmation.")
        claims, evidence_refs = session_claims_and_evidence(manifest)
        story = {
            "story_id": sanitize(args.story),
            "phase": manifest.get("phase", ""),
            "published_at": args.published_at or datetime.now().astimezone().date().isoformat(),
            "channels": [sanitize(item) for item in args.channel],
            "claims": [sanitize(item) for item in (args.claim or claims)],
            "evidence_refs": [sanitize(item) for item in (args.evidence_ref or evidence_refs)],
            "next_open_questions": [],
            "source_session": session.name,
        }
        existing_ids = {item.get("story_id") for item in registry.get("published_stories", [])}
        if story["story_id"] in existing_ids:
            raise SystemExit(f"Story is already registered: {story['story_id']}")
        registry.setdefault("published_stories", []).append(story)
        save_json(registry_path(root, config), registry)
        print(json.dumps(story, ensure_ascii=False, indent=2))
        return 0

    report = audit_session(session)
    if args.action == "audit":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["release_ready"] else 2

    exports = build_exports(root, session, manifest, config, report)
    print(exports)
    return 0 if report["release_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
