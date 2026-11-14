from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "haostory" / "scripts" / "studio.py"
ASSETS = ROOT / "skill" / "haostory" / "assets" / "studio"
SPEC = importlib.util.spec_from_file_location("haostory_studio", SCRIPT)
assert SPEC and SPEC.loader
STUDIO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDIO)


class StudioTests(unittest.TestCase):
    def make_project(self, parent: Path) -> Path:
        project = parent / "story-project"
        (project / "docs" / "screenshots").mkdir(parents=True)
        (project / "src").mkdir()
        (project / "node_modules" / "pkg").mkdir(parents=True)
        (project / ".haostory").mkdir()
        (project / "README.md").write_text("# Story Project\n\nA public project overview.\n", encoding="utf-8")
        (project / "docs" / "progress.md").write_text(
            "The first attempt failed. We changed the design and the demo now works.",
            encoding="utf-8",
        )
        (project / "docs" / "screenshots" / "result.png").write_bytes(b"safe-image")
        (project / "src" / "app.py").write_text("print('source')\n", encoding="utf-8")
        (project / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
        (project / ".haostory" / "private.md").write_text("private capture", encoding="utf-8")
        (project / "node_modules" / "pkg" / "README.md").write_text("dependency", encoding="utf-8")
        return project

    def test_discovery_lists_only_safe_explanatory_material_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            result = STUDIO.discover_sources(project)
            paths = {item["path"] for item in result["sources"]}
            self.assertEqual(
                paths,
                {"README.md", "docs/progress.md", "docs/screenshots/result.png"},
            )
            source = next(item for item in result["sources"] if item["path"] == "docs/progress.md")
            self.assertEqual(source["kind"], "text")
            self.assertNotIn("content", source)
            self.assertNotIn("failed", json.dumps(result))

    def test_analysis_reads_only_selected_material_and_recommends_three_angles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            result = STUDIO.analyze_materials(
                project,
                selections=["docs/progress.md"],
                formats=["article", "video", "xiaohongshu"],
                goal="Share a useful project lesson",
                audience="independent creators",
            )
            self.assertEqual(result["material_count"], 1)
            self.assertEqual(len(result["recommendations"]), 3)
            self.assertIn("failure_recovery", {item["id"] for item in result["recommendations"]})
            self.assertIn("docs/progress.md", result["approved_sources"])
            serialized = json.dumps(result).lower()
            self.assertNotIn("src/app.py", serialized)
            self.assertNotIn("print('source')", serialized)
            self.assertTrue(any(item["id"] == "visual_proof" for item in result["gaps"]))

    def test_analysis_rejects_unapproved_or_escaping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            for unsafe in ("../outside.md", "src/app.py", ".env", ".haostory/private.md"):
                with self.subTest(unsafe=unsafe), self.assertRaises(STUDIO.StudioError):
                    STUDIO.analyze_materials(project, [unsafe], ["article"])

    def test_job_round_trip_is_private_and_excludes_console_sponsors(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            payload = {
                "selected_paths": ["README.md", "docs/screenshots/result.png"],
                "conversation_refs": [{"host": "codex", "id": "thread-1", "title": "Project review"}],
                "formats": ["article", "xiaohongshu"],
                "angle": "before_after",
                "goal": "Explain what changed",
                "audience": "builders",
                "supplements": "Use a calm, practical tone.",
                "research_current_examples": True,
            }
            created = STUDIO.create_job(project, payload)
            loaded = STUDIO.load_job(project, created["job_id"])
            self.assertEqual(loaded["status"], "pending")
            self.assertEqual(loaded["selected_paths"], payload["selected_paths"])
            self.assertTrue(loaded["privacy"]["external_research_authorized"])
            serialized = json.dumps(loaded, ensure_ascii=False)
            self.assertNotIn("HaoAILab", serialized)
            self.assertNotIn("OneTake", serialized)
            self.assertTrue((project / ".haostory" / "studio" / "jobs" / created["job_id"] / "request.json").exists())

            output = project / "article.md"
            output.write_text("# Generated article\n", encoding="utf-8")
            completed = STUDIO.complete_job(project, created["job_id"], ["article.md"])
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(STUDIO.latest_job(project)["job_id"], created["job_id"])

    def test_host_context_exposes_conversation_metadata_but_rejects_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "host-context.json"
            path.write_text(
                json.dumps(
                    {
                        "host": "codex",
                        "conversations": [
                            {
                                "id": "thread-1",
                                "title": "拾光项目更新",
                                "project": "story-project",
                                "updated_at": "2026-11-15T10:00:00+08:00",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            context = STUDIO.load_host_context(path)
            self.assertEqual(context["host"], "codex")
            self.assertEqual(context["conversations"][0]["title"], "拾光项目更新")
            self.assertNotIn("content", json.dumps(context))

            path.write_text(
                json.dumps(
                    {
                        "host": "codex",
                        "conversations": [{"id": "thread-1", "title": "Private", "content": "body"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(STUDIO.StudioError):
                STUDIO.load_host_context(path)

    def test_wait_for_job_returns_only_after_a_new_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            first = STUDIO.create_job(
                project,
                {"selected_paths": ["README.md"], "formats": ["article"], "angle": "decision_story"},
            )

            def create_later() -> None:
                time.sleep(0.1)
                STUDIO.create_job(
                    project,
                    {"selected_paths": ["README.md"], "formats": ["video"], "angle": "sixty_second_story"},
                )

            worker = threading.Thread(target=create_later)
            worker.start()
            found = STUDIO.wait_for_job(project, after=first["job_id"], timeout=2)
            worker.join(timeout=2)
            self.assertIsNotNone(found)
            self.assertNotEqual(found["job_id"], first["job_id"])

    def test_http_api_serves_local_json_routes_with_security_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            try:
                server, thread, base_url = STUDIO.serve_in_thread(project, ASSETS)
            except PermissionError:
                self.skipTest("Local socket binding is restricted in this sandbox.")
            try:
                with urllib.request.urlopen(f"{base_url}/api/capabilities") as response:
                    data = json.loads(response.read())
                    self.assertEqual(data["product"], "HaoStory Studio")
                    self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                with urllib.request.urlopen(f"{base_url}/api/sources") as response:
                    data = json.loads(response.read())
                    self.assertEqual(len(data["sources"]), 3)
                request = urllib.request.Request(
                    f"{base_url}/api/analyze",
                    data=json.dumps(
                        {"selections": ["docs/progress.md"], "formats": ["article"]}
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request) as response:
                    data = json.loads(response.read())
                    self.assertEqual(len(data["recommendations"]), 3)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(f"{base_url}/private")
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
