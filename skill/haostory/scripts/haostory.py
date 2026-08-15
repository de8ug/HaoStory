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
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA = "haostory/v1"
JOURNAL_DIR = ".haostory"
CONFIG_FILE = ".haostory.json"
MAX_CAPTURE_CHARS = 120_000
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
    return deep_merge(DEFAULT_CONFIG, custom)


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


def ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = current.splitlines()
    if JOURNAL_DIR + "/" not in lines and JOURNAL_DIR not in lines:
        separator = "" if not current or current.endswith("\n") else "\n"
        path.write_text(f"{current}{separator}{JOURNAL_DIR}/\n", encoding="utf-8")


def setup_project(root: Path) -> Path:
    ensure_gitignore(root)
    path = root / CONFIG_FILE
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def latest_session(root: Path) -> Path | None:
    journal = root / JOURNAL_DIR
    if not journal.exists():
        return None
    sessions = sorted(path for path in journal.iterdir() if path.is_dir())
    return sessions[-1] if sessions else None


def resolve_session(root: Path, session: str | None, create_name: str | None = None) -> Path:
    journal = root / JOURNAL_DIR
    journal.mkdir(exist_ok=True)
    if session:
        path = journal / session
    elif create_name:
        path = journal / create_name
    else:
        found = latest_session(root)
        if not found:
            raise SystemExit("No HaoStory session found. Run `start` first or pass --session.")
        return found
    path.mkdir(parents=True, exist_ok=True)
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
        "assets": assets,
        "findings": findings,
        "note": "Best-effort text scan only. Review every asset and the final Git history manually.",
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


def build_exports(session: Path, manifest: dict[str, Any], config: dict[str, Any], report: dict[str, Any]) -> Path:
    exports = session / "exports"
    exports.mkdir(exist_ok=True)
    title = manifest.get("title", "Untitled story")
    summary = manifest.get("summary") or "—"
    outcome = manifest.get("outcome") or "—"
    lesson = manifest.get("lesson") or "—"
    score = story_score(manifest)
    manifest["story_score"] = score

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

    start = sub.add_parser("start", help="Start a HaoStory session")
    start.add_argument("--title", required=True)
    start.add_argument("--summary", default="")
    start.add_argument("--type", choices=("software", "product", "content", "research"), default="software")
    start.add_argument("--session")

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

    for name in ("audit", "export"):
        command = sub.add_parser(name, help=f"{name.title()} a HaoStory session")
        command.add_argument("session_path", nargs="?")
        command.add_argument("--session")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = project_root(Path.cwd())

    if args.action == "setup":
        path = setup_project(root)
        print(path)
        return 0

    ensure_gitignore(root)
    config = load_config(root)

    if args.action == "start":
        session_name = args.session or f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(args.title)}"
        session = resolve_session(root, args.session, session_name)
        if (session / "manifest.json").exists():
            raise SystemExit(f"Session already exists: {session}")
        for folder in ("evidence", "assets"):
            (session / folder).mkdir(exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": SCHEMA,
            "project": root.name,
            "title": sanitize(args.title),
            "summary": sanitize(args.summary),
            "type": args.type,
            "started_at": now_iso(),
            "updated_at": now_iso(),
            "stages": [],
            "assets": [],
            "commands": [],
        }
        evidence = capture_git(root, session, "start")
        manifest["stages"].append(
            {"type": "start", "stage": "start", "notes": manifest["summary"], "decision": "", "evidence": evidence, "assets": [], "captured_at": now_iso()}
        )
        save_manifest(session, manifest)
        append_timeline(session, f"{now_iso()} · start", [("Title", manifest["title"]), ("Summary", manifest["summary"])])
        print(session)
        return 0

    if args.action in {"audit", "export"} and args.session_path:
        session = Path(args.session_path).expanduser().resolve()
    else:
        session = resolve_session(root, getattr(args, "session", None))
    manifest = load_manifest(session)

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
        manifest["stages"].append(item)
        manifest["assets"].extend(assets)
        if command:
            manifest["commands"].append(command)
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
        manifest["stages"].append(
            {"type": "finish", "stage": "finish", "notes": manifest["outcome"], "decision": manifest["lesson"], "evidence": evidence, "assets": assets, "captured_at": now_iso()}
        )
        manifest["assets"].extend(assets)
        manifest["story_score"] = story_score(manifest)
        save_manifest(session, manifest)
        append_timeline(session, f"{now_iso()} · finish", [("Outcome", args.outcome), ("Lesson", args.lesson)])
        print(session)
        return 0

    report = audit_session(session)
    if args.action == "audit":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["release_ready"] else 2

    exports = build_exports(session, manifest, config, report)
    print(exports)
    return 0 if report["release_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
