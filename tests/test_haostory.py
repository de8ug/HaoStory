from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "haostory" / "scripts" / "haostory.py"
SPEC = importlib.util.spec_from_file_location("haostory_cli", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HaoStoryTests(unittest.TestCase):
    def run_cli(self, cwd: Path, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return result

    def test_sanitize_common_private_values(self) -> None:
        fake_token = "sk-" + "a" * 16
        credential_url = "https://" + "alice:" + "password" + "@example.com"
        source = (
            f"{Path.home()}/work token={fake_token} "
            f"{credential_url} x@example.com 8.8.8.8 127.0.0.1"
        )
        result = MODULE.sanitize(source)
        self.assertNotIn(str(Path.home()), result)
        self.assertNotIn("alice:password", result)
        self.assertNotIn(fake_token, result)
        self.assertNotIn("x@example.com", result)
        self.assertNotIn("8.8.8.8", result)
        self.assertIn("127.0.0.1", result)

    def test_end_to_end_bilingual_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "demo-project"
            project.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            (project / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
            subprocess.run(
                ["git", "-c", "user.name=HaoStory Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "init"],
                cwd=project,
                check=True,
            )

            self.run_cli(project, "setup")
            started = self.run_cli(
                project,
                "start",
                "--title",
                "UP2U first experiment",
                "--summary",
                "Turn a product decision into reusable content.",
                "--type",
                "product",
            )
            session = Path(started.stdout.strip())
            self.run_cli(
                project,
                "checkpoint",
                "--stage",
                "decision",
                "--notes",
                "The homepage now leads with user problems.",
                "--decision",
                "A curated navigator is sustainable for one person.",
                "--run",
                sys.executable,
                "-c",
                "print('verified')",
            )
            self.run_cli(
                project,
                "finish",
                "--outcome",
                "The first experiment produced a verified homepage story.",
                "--lesson",
                "Capture decisions during work instead of reconstructing them later.",
            )
            self.run_cli(project, "export")

            exports = session / "exports"
            expected = {
                "article.zh-CN.md",
                "article.en.md",
                "video-script.zh-CN.md",
                "video-script.en.md",
                "social.zh-CN.md",
                "social.en.md",
                "content-package.json",
            }
            self.assertTrue(expected.issubset({path.name for path in exports.iterdir()}))
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "haostory/v1")
            self.assertEqual(manifest["project"], "demo-project")
            self.assertNotIn(str(project), json.dumps(manifest))
            report = json.loads((session / "privacy-report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["release_ready"])
            self.assertIn(".haostory/", (project / ".gitignore").read_text(encoding="utf-8"))

    def test_public_tree_has_no_personal_absolute_paths(self) -> None:
        forbidden = ("/" + "Users/", "/root/" + "howie", "192." + "144.")
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"private marker in {path}")


if __name__ == "__main__":
    unittest.main()
