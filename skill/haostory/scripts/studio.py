#!/usr/bin/env python3
"""Local, permission-scoped control plane for HaoStory Studio."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PRODUCT_NAME = "HaoStory Studio"
TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".rst"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_ROOT_TEXT = {"readme.md", "readme.zh-cn.md", "readme.txt", "about.md", "project.md"}
ALLOWED_DIRECTORIES = {"docs", "documentation", "notes", "images", "media", "screenshots", "assets"}
BLOCKED_PARTS = {
    ".git",
    ".haostory",
    ".env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    "src",
    "source",
    "secrets",
    "credentials",
    "cookies",
    "browser profile",
}
SECRET_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
MAX_SOURCES = 300
MAX_TEXT_BYTES = 600_000
MAX_IMAGE_BYTES = 25_000_000
MAX_REQUEST_BYTES = 1_000_000

DEFAULT_SPONSOR = {
    "enabled": True,
    "lab_name": "浩哥 AI 实验室",
    "lab_note": "关注 AI 产品、创作与实践",
    "wechat": "HaoAILab",
    "wechat_note": "一起玩转 AI",
    "onetake_name": "OneTake",
    "onetake_note": "把脚本继续做成视频",
}


class StudioError(ValueError):
    """A safe, user-facing Studio validation error."""


TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "article": [
        {
            "id": "failure_recovery",
            "title": "失败如何改变方案",
            "description": "用真实阻力、判断变化和最终结果构成完整故事。",
            "signals": ("失败", "failed", "error", "问题", "恢复", "fixed", "changed", "调整"),
        },
        {
            "id": "decision_story",
            "title": "一个关键决定",
            "description": "围绕一次取舍解释为什么做、怎样验证、学到了什么。",
            "signals": ("决定", "decision", "选择", "取舍", "为什么", "because"),
        },
        {
            "id": "project_case_study",
            "title": "从问题到结果",
            "description": "把项目背景、过程证据和可复用经验整理成案例文章。",
            "signals": ("结果", "result", "完成", "works", "demo", "验证"),
        },
        {
            "id": "practical_guide",
            "title": "方法拆解",
            "description": "把过程提炼成读者可以复用的步骤与避坑建议。",
            "signals": ("步骤", "方法", "how", "流程", "教程", "指南"),
        },
    ],
    "video": [
        {
            "id": "sixty_second_story",
            "title": "60 秒问题—转折—结果",
            "description": "用强开场、可见转折和结果证据完成短视频。",
            "signals": ("失败", "问题", "changed", "result", "结果", "demo"),
        },
        {
            "id": "visual_walkthrough",
            "title": "屏幕演示加旁白",
            "description": "以关键画面为主线，用旁白解释动作背后的判断。",
            "signals": ("image", "screenshot", "截图", "界面", "demo"),
        },
        {
            "id": "three_minute_case",
            "title": "3 分钟项目案例",
            "description": "交代背景、两次关键变化、结果和方法总结。",
            "signals": ("项目", "project", "完成", "result", "lesson"),
        },
    ],
    "xiaohongshu": [
        {
            "id": "before_after",
            "title": "前后对比图文",
            "description": "用封面结论、前后画面和三条变化构成可收藏卡片。",
            "signals": ("before", "after", "前后", "变化", "截图", "image"),
        },
        {
            "id": "experience_notes",
            "title": "真实体验与避坑",
            "description": "从亲历问题切入，写清尝试、踩坑和建议。",
            "signals": ("失败", "踩坑", "问题", "经验", "尝试", "error"),
        },
        {
            "id": "step_cards",
            "title": "步骤卡片",
            "description": "将方法压缩成封面和可快速浏览的步骤卡。",
            "signals": ("步骤", "流程", "方法", "how", "guide"),
        },
    ],
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _blocked(path: Path) -> bool:
    lowered = {part.casefold() for part in path.parts}
    if lowered & BLOCKED_PARTS or any(part.startswith(".") for part in path.parts):
        return True
    name = path.name.casefold()
    if path.suffix.casefold() in SECRET_SUFFIXES:
        return True
    return any(token in name for token in ("secret", "credential", "token", "cookie", "id_rsa", "id_ed25519"))


def _safe_project_file(root: Path, relative: str) -> Path:
    raw = str(relative).strip()
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts or _blocked(candidate):
        raise StudioError(f"Unsafe or unsupported material path: {relative}")
    path = root / candidate
    if path.is_symlink() or not path.is_file():
        raise StudioError(f"Material is missing or unsafe: {relative}")
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise StudioError(f"Material must stay inside the selected project: {relative}") from exc
    return resolved


def _is_candidate(relative: Path, size: int) -> bool:
    if _blocked(relative) or len(relative.parts) > 5:
        return False
    suffix = relative.suffix.casefold()
    if suffix not in TEXT_EXTENSIONS | IMAGE_EXTENSIONS:
        return False
    if len(relative.parts) == 1:
        if suffix in TEXT_EXTENSIONS and relative.name.casefold() not in ALLOWED_ROOT_TEXT:
            return False
    elif relative.parts[0].casefold() not in ALLOWED_DIRECTORIES:
        return False
    if suffix in TEXT_EXTENSIONS:
        return size <= MAX_TEXT_BYTES * 4
    return size <= MAX_IMAGE_BYTES


def discover_sources(root: Path, limit: int = MAX_SOURCES) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise StudioError(f"Project directory does not exist: {root}")
    candidate_paths: list[Path] = []
    for path in root.iterdir():
        if path.is_file():
            candidate_paths.append(path)
        elif path.is_dir() and path.name.casefold() in ALLOWED_DIRECTORIES and not path.is_symlink():
            for current, directories, files in os.walk(str(path), topdown=True):
                current_path = Path(current)
                try:
                    depth = len(current_path.relative_to(root).parts)
                except ValueError:
                    directories[:] = []
                    continue
                directories[:] = [
                    name
                    for name in directories
                    if depth < 4 and name.casefold() not in BLOCKED_PARTS and not (current_path / name).is_symlink()
                ]
                candidate_paths.extend(current_path / name for name in files)

    sources: list[dict[str, Any]] = []
    for path in sorted(candidate_paths):
        if len(sources) >= max(1, min(limit, MAX_SOURCES)):
            break
        if path.is_symlink() or not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
            size = path.stat().st_size
        except (OSError, ValueError):
            continue
        if not _is_candidate(relative, size):
            continue
        suffix = relative.suffix.casefold()
        sources.append(
            {
                "path": relative.as_posix(),
                "name": relative.name,
                "kind": "text" if suffix in TEXT_EXTENSIONS else "image",
                "size": size,
            }
        )
    return {
        "project": root.name,
        "root": str(root),
        "sources": sources,
        "truncated": len(sources) >= max(1, min(limit, MAX_SOURCES)),
        "privacy": "File bodies have not been read. Select material before analysis.",
    }


def load_host_context(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"host": "generic", "conversations": []}
    source = path.expanduser().resolve()
    if not source.is_file() or source.is_symlink() or source.stat().st_size > MAX_REQUEST_BYTES:
        raise StudioError("Host context must be a small, regular JSON file.")
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StudioError("Host context must contain valid JSON.") from exc
    if not isinstance(raw, dict):
        raise StudioError("Host context must be a JSON object.")
    conversations: list[dict[str, str]] = []
    for item in raw.get("conversations", []):
        if not isinstance(item, dict) or not item.get("id") or not item.get("title"):
            raise StudioError("Every host conversation requires an id and title.")
        forbidden = {"content", "body", "messages", "turns", "transcript"} & set(item)
        if forbidden:
            raise StudioError("Host context may contain conversation metadata only, not message bodies.")
        conversations.append(
            {
                "id": _sanitize_text(str(item["id"]))[:200],
                "title": _sanitize_text(str(item["title"]))[:300],
                "project": _sanitize_text(str(item.get("project", "")))[:200],
                "updated_at": _sanitize_text(str(item.get("updated_at", "")))[:80],
            }
        )
    return {
        "host": _sanitize_text(str(raw.get("host", "generic")))[:80],
        "conversations": conversations[:50],
    }


def studio_sponsor(root: Path) -> dict[str, Any]:
    sponsor = dict(DEFAULT_SPONSOR)
    config = root.resolve() / ".haostory.json"
    if not config.is_file() or config.is_symlink():
        return sponsor
    try:
        value = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return sponsor
    override = value.get("studio", {}).get("sponsor", {}) if isinstance(value, dict) else {}
    if not isinstance(override, dict):
        return sponsor
    for key in sponsor:
        if key in override:
            sponsor[key] = bool(override[key]) if key == "enabled" else _sanitize_text(str(override[key]))[:200]
    return sponsor


def _sanitize_text(text: str) -> str:
    text = text.replace(str(Path.home()), "<HOME>")
    text = re.sub(r"\b(?:sk-|ghp_|github_pat_|AKIA)[A-Za-z0-9_-]{12,}\b", "<secret-redacted>", text)
    text = re.sub(r"(?i)\b(?:token|password|secret|api[_-]?key)\s*[:=]\s*[^\s]+", "<secret-redacted>", text)
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "<email-redacted>", text, flags=re.I)
    return text


def _selected_materials(root: Path, selections: list[str]) -> list[dict[str, Any]]:
    discovered = {item["path"]: item for item in discover_sources(root)["sources"]}
    materials: list[dict[str, Any]] = []
    for relative in list(dict.fromkeys(str(item) for item in selections)):
        if relative not in discovered:
            raise StudioError(f"Material was not offered for selection: {relative}")
        path = _safe_project_file(root, relative)
        metadata = dict(discovered[relative])
        if metadata["kind"] == "text":
            raw = path.read_bytes()[:MAX_TEXT_BYTES]
            metadata["content"] = _sanitize_text(raw.decode("utf-8", errors="replace"))
            metadata["truncated"] = path.stat().st_size > MAX_TEXT_BYTES
        else:
            metadata["content"] = None
            metadata["truncated"] = False
        materials.append(metadata)
    return materials


def template_catalog() -> dict[str, Any]:
    return {
        "formats": [
            {"id": "article", "title": "文章", "description": "适合完整案例、复盘和方法分享。"},
            {"id": "video", "title": "视频", "description": "生成口播、旁白、分镜和素材建议。"},
            {"id": "xiaohongshu", "title": "小红书图文", "description": "生成封面标题、卡片结构和发布文案。"},
        ],
        "templates": {
            key: [
                {name: value for name, value in item.items() if name != "signals"}
                for item in items
            ]
            for key, items in TEMPLATES.items()
        },
    }


def analyze_materials(
    root: Path,
    selections: list[str],
    formats: list[str],
    goal: str = "",
    audience: str = "",
    conversation_refs: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    normalized_formats = list(dict.fromkeys(str(item) for item in formats))
    if not normalized_formats or any(item not in TEMPLATES for item in normalized_formats):
        raise StudioError("Choose at least one supported format: article, video, or xiaohongshu.")
    materials = _selected_materials(root.resolve(), selections)
    text = "\n".join(str(item.get("content") or "") for item in materials).casefold()
    refs = conversation_refs or []
    text += "\n" + "\n".join(str(item.get("title", "")) for item in refs).casefold()
    if any(item["kind"] == "image" for item in materials):
        text += " image screenshot 截图"

    ranked: list[dict[str, Any]] = []
    for format_id in normalized_formats:
        for order, template in enumerate(TEMPLATES[format_id]):
            matched = [signal for signal in template["signals"] if signal.casefold() in text]
            score = 55 + min(35, len(matched) * 9) - order
            reason = (
                "已有材料包含可支撑这个结构的转折或证据。"
                if matched
                else "这是当前内容目标下稳定、易理解的基础结构。"
            )
            ranked.append(
                {
                    "id": template["id"],
                    "format": format_id,
                    "title": template["title"],
                    "description": template["description"],
                    "score": score,
                    "reason": reason,
                    "matched_signals": matched[:4],
                }
            )
    ranked.sort(key=lambda item: (-item["score"], item["format"], item["id"]))
    recommendations: list[dict[str, Any]] = []
    used: set[str] = set()
    for item in ranked:
        if item["id"] in used:
            continue
        recommendations.append(item)
        used.add(item["id"])
        if len(recommendations) == 3:
            break

    gaps: list[dict[str, str]] = []
    if not any(item["kind"] == "image" for item in materials):
        gaps.append(
            {
                "id": "visual_proof",
                "title": "是否有一张结果图？",
                "why": "文章封面、视频画面和小红书卡片都会更具体；没有也可以继续。",
            }
        )
    if not goal.strip():
        gaps.append({"id": "goal", "title": "这次最想让读者记住什么？", "why": "用于收敛标题和结尾。"})
    if not audience.strip():
        gaps.append({"id": "audience", "title": "主要讲给谁听？", "why": "用于调整解释深度和语气。"})
    if not any(token in text for token in ("结果", "result", "完成", "works", "验证", "效果")):
        gaps.append({"id": "outcome", "title": "最终发生了什么变化？", "why": "真实结果能避免内容只有过程没有结论。"})

    return {
        "material_count": len(materials) + len(refs),
        "approved_sources": [item["path"] for item in materials],
        "approved_conversations": refs,
        "formats": normalized_formats,
        "goal": _sanitize_text(goal.strip()),
        "audience": _sanitize_text(audience.strip()),
        "recommendations": recommendations,
        "gaps": gaps[:3],
        "can_generate_now": bool(materials or refs),
        "materials": [
            {key: value for key, value in item.items() if key != "content"}
            for item in materials
        ],
    }


def selected_conversations(
    host_context: dict[str, Any], requested: list[dict[str, Any]]
) -> list[dict[str, str]]:
    available = {str(item["id"]): item for item in host_context.get("conversations", [])}
    selected: list[dict[str, str]] = []
    for item in requested:
        if not isinstance(item, dict) or str(item.get("id", "")) not in available:
            raise StudioError("A selected conversation was not offered by the host adapter.")
        source = available[str(item["id"])]
        selected.append(
            {
                "host": str(host_context.get("host", "generic")),
                "id": str(source["id"]),
                "title": str(source["title"]),
            }
        )
    return selected


def _studio_root(root: Path, create: bool = True) -> Path:
    project = root.resolve()
    journal = project / ".haostory"
    if journal.is_symlink():
        raise StudioError("Refusing a symlinked .haostory directory.")
    studio = journal / "studio"
    if studio.is_symlink():
        raise StudioError("Refusing a symlinked Studio directory.")
    if create:
        ignore = project / ".gitignore"
        current = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
        if ".haostory/" not in current.splitlines() and ".haostory" not in current.splitlines():
            separator = "" if not current or current.endswith("\n") else "\n"
            ignore.write_text(f"{current}{separator}.haostory/\n", encoding="utf-8")
        studio.mkdir(parents=True, exist_ok=True)
    return studio


def _validate_job_id(job_id: str) -> str:
    value = str(job_id).strip()
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}-[a-f0-9]{8}", value):
        raise StudioError("Invalid Studio job id.")
    return value


def create_job(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    selected_paths = list(dict.fromkeys(str(item) for item in payload.get("selected_paths", [])))
    discovered = {item["path"] for item in discover_sources(root)["sources"]}
    if any(path not in discovered for path in selected_paths):
        raise StudioError("A selected file is no longer available or was never approved.")
    formats = list(dict.fromkeys(str(item) for item in payload.get("formats", [])))
    if not formats or any(item not in TEMPLATES for item in formats):
        raise StudioError("A production job requires at least one supported format.")
    refs: list[dict[str, str]] = []
    for item in payload.get("conversation_refs", []):
        if not isinstance(item, dict) or not item.get("id"):
            raise StudioError("Conversation references require an id.")
        refs.append(
            {
                "host": _sanitize_text(str(item.get("host", "unknown")))[:80],
                "id": _sanitize_text(str(item["id"]))[:200],
                "title": _sanitize_text(str(item.get("title", "Conversation")))[:300],
            }
        )
    job_id = f"{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    request = {
        "schema": "haostory/studio-job/v1",
        "job_id": job_id,
        "status": "pending",
        "created_at": now_iso(),
        "project": root.resolve().name,
        "selected_paths": selected_paths,
        "conversation_refs": refs,
        "formats": formats,
        "angle": _sanitize_text(str(payload.get("angle", "")))[:120],
        "goal": _sanitize_text(str(payload.get("goal", "")))[:2_000],
        "audience": _sanitize_text(str(payload.get("audience", "")))[:500],
        "supplements": _sanitize_text(str(payload.get("supplements", "")))[:8_000],
        "generate_with_current_material": bool(payload.get("generate_with_current_material", True)),
        "research_current_examples": bool(payload.get("research_current_examples", False)),
        "privacy": {
            "selected_material_only": True,
            "external_research_authorized": bool(payload.get("research_current_examples", False)),
            "publication_authorized": False,
            "upload_authorized": False,
        },
    }
    directory = _studio_root(root) / "jobs" / job_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "request.json").write_text(
        json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"job_id": job_id, "status": "pending", "request": str(directory / "request.json")}


def load_job(root: Path, job_id: str) -> dict[str, Any]:
    value = _validate_job_id(job_id)
    directory = _studio_root(root) / "jobs" / value
    path = directory / "request.json"
    if directory.is_symlink() or not path.is_file() or path.is_symlink():
        raise StudioError(f"Studio job not found: {value}")
    return json.loads(path.read_text(encoding="utf-8"))


def latest_job(root: Path) -> dict[str, Any] | None:
    jobs = _studio_root(root) / "jobs"
    if not jobs.exists():
        return None
    candidates = [path for path in jobs.glob("*/request.json") if not path.parent.is_symlink()]
    if not candidates:
        return None
    latest = max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.parent.name))
    return load_job(root, latest.parent.name)


def wait_for_job(root: Path, after: str = "", timeout: float = 600) -> dict[str, Any] | None:
    deadline = time.monotonic() + max(0, min(float(timeout), 3600))
    while time.monotonic() <= deadline:
        latest = latest_job(root)
        if latest and latest.get("job_id") != after:
            return latest
        time.sleep(0.25)
    return None


def complete_job(root: Path, job_id: str, outputs: list[str]) -> dict[str, Any]:
    request = load_job(root, job_id)
    approved: list[str] = []
    for output in outputs:
        path = _safe_project_file(root.resolve(), str(output))
        approved.append(path.relative_to(root.resolve()).as_posix())
    request["status"] = "completed"
    request["completed_at"] = now_iso()
    request["outputs"] = approved
    path = _studio_root(root) / "jobs" / request["job_id"] / "request.json"
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return request


class StudioRequestHandler(BaseHTTPRequestHandler):
    server_version = "HaoStoryStudio/1"

    @property
    def project_root(self) -> Path:
        return self.server.project_root  # type: ignore[attr-defined]

    @property
    def assets_root(self) -> Path:
        return self.server.assets_root  # type: ignore[attr-defined]

    @property
    def host_context(self) -> dict[str, Any]:
        return self.server.host_context  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _headers(self, content_type: str, length: int, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _json(self, value: Any, status: int = 200) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._headers("application/json; charset=utf-8", len(payload), status)
        self.wfile.write(payload)

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message, "status": status}, status)

    def _read_json(self) -> dict[str, Any]:
        if self.headers.get_content_type() != "application/json":
            raise StudioError("Studio API requests must use application/json.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise StudioError("Invalid request length.") from exc
        if size <= 0 or size > MAX_REQUEST_BYTES:
            raise StudioError("Request body is empty or too large.")
        try:
            value = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StudioError("Request must contain valid JSON.") from exc
        if not isinstance(value, dict):
            raise StudioError("Request JSON must be an object.")
        return value

    def _validate_local_request(self) -> None:
        host = self.headers.get("Host", "")
        port = self.server.server_address[1]
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in allowed_hosts:
            raise StudioError("Studio accepts requests from its local address only.")
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
            raise StudioError("Cross-origin Studio requests are not allowed.")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            self._validate_local_request()
            if path == "/api/capabilities":
                self._json(
                    {
                        "product": PRODUCT_NAME,
                        "project": self.project_root.name,
                        "capabilities": {
                            "current_workspace": True,
                            "recent_conversations": bool(self.host_context["conversations"]),
                            "manual_import": False,
                            "formats": list(TEMPLATES),
                        },
                        "privacy": "Only selected project material will be read.",
                        "sponsor": studio_sponsor(self.project_root),
                    }
                )
                return
            if path == "/api/host-context":
                self._json(self.host_context)
                return
            if path == "/api/sources":
                self._json(discover_sources(self.project_root))
                return
            if path == "/api/templates":
                self._json(template_catalog())
                return
            static = {"/": "index.html", "/index.html": "index.html", "/studio.css": "studio.css", "/studio.js": "studio.js"}
            if path in static:
                target = self.assets_root / static[path]
                if not target.is_file():
                    self._error(HTTPStatus.NOT_FOUND, "Studio asset not found.")
                    return
                body = target.read_bytes()
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                if content_type.startswith("text/") or content_type == "application/javascript":
                    content_type += "; charset=utf-8"
                self._headers(content_type, len(body))
                self.wfile.write(body)
                return
            self._error(HTTPStatus.NOT_FOUND, "Route not found.")
        except StudioError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            self._validate_local_request()
            payload = self._read_json()
            if path == "/api/analyze":
                refs = selected_conversations(
                    self.host_context, list(payload.get("conversation_refs", []))
                )
                self._json(
                    analyze_materials(
                        self.project_root,
                        list(payload.get("selections", [])),
                        list(payload.get("formats", [])),
                        str(payload.get("goal", "")),
                        str(payload.get("audience", "")),
                        refs,
                    )
                )
                return
            if path == "/api/jobs":
                payload["conversation_refs"] = selected_conversations(
                    self.host_context, list(payload.get("conversation_refs", []))
                )
                self._json(create_job(self.project_root, payload), HTTPStatus.CREATED)
                return
            self._error(HTTPStatus.NOT_FOUND, "Route not found.")
        except StudioError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))


def build_server(
    root: Path,
    assets_root: Path,
    host: str = "127.0.0.1",
    port: int = 0,
    host_context: dict[str, Any] | None = None,
) -> ThreadingHTTPServer:
    project = root.resolve()
    assets = assets_root.resolve()
    if not assets.is_dir():
        raise StudioError(f"Studio assets not found: {assets}")
    server = ThreadingHTTPServer((host, port), StudioRequestHandler)
    server.project_root = project  # type: ignore[attr-defined]
    server.assets_root = assets  # type: ignore[attr-defined]
    server.host_context = host_context or {"host": "generic", "conversations": []}  # type: ignore[attr-defined]
    return server


def serve_in_thread(
    root: Path, assets_root: Path, host_context: dict[str, Any] | None = None
) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    server = build_server(root, assets_root, host_context=host_context)
    thread = threading.Thread(target=server.serve_forever, name="haostory-studio", daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, thread, f"http://{host}:{port}"


def run_server(
    root: Path,
    assets_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
    host_context: dict[str, Any] | None = None,
) -> None:
    server = build_server(root, assets_root, host=host, port=port, host_context=host_context)
    address, bound_port = server.server_address[:2]
    url = f"http://{address}:{bound_port}"
    print(json.dumps({"product": PRODUCT_NAME, "url": url, "project": str(root.resolve())}, ensure_ascii=False), flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
