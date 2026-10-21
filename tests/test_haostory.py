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

    def make_project(self, parent: Path, name: str = "demo-project") -> Path:
        project = parent / name
        project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        (project / "README.md").write_text("# Demo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=HaoStory Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "init",
            ],
            cwd=project,
            check=True,
        )
        return project

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
            project = self.make_project(Path(temp))

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

    def test_assisted_auto_starts_meaningful_build_and_records_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            self.run_cli(project, "enable")
            result = self.run_cli(
                project,
                "suggest-start",
                "--title",
                "Build stage-aware capture",
                "--summary",
                "Implement a verifiable V2 capture window.",
                "--type",
                "software",
                "--initiative",
                "stage-aware-capture-v2",
                "--phase",
                "build",
            )
            decision = json.loads(result.stdout)
            self.assertEqual(decision["action"], "started")
            session = Path(decision["session"])
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "The CLI completed its first end-to-end run.",
                "--novelty-key",
                "first-cli-demo",
                "--claim",
                "Stage-aware capture can run locally.",
                "--evidence-ref",
                "command:first-demo",
            )
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["initiative"], "stage-aware-capture-v2")
            self.assertEqual(manifest["phase"], "build")
            self.assertEqual(manifest["capture_window"]["status"], "active")
            self.assertEqual(manifest["events"][-1]["event_type"], "demo")

    def test_formatting_change_does_not_start_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            result = self.run_cli(
                project,
                "suggest-start",
                "--title",
                "Reformat Markdown",
                "--initiative",
                "docs-cleanup",
                "--phase",
                "build",
                "--work-kind",
                "formatting",
            )
            decision = json.loads(result.stdout)
            self.assertEqual(decision["action"], "ignore")
            self.assertFalse(list((project / ".haostory").glob("*/manifest.json")))

    def test_unconfigured_manual_and_off_modes_do_not_auto_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            unconfigured = self.run_cli(
                project,
                "suggest-start",
                "--title",
                "Unconfigured work",
                "--initiative",
                "mode-test",
                "--phase",
                "build",
            )
            self.assertEqual(json.loads(unconfigured.stdout)["action"], "ignore")
            self.assertFalse((project / ".gitignore").exists())

            config_path = Path(self.run_cli(project, "setup").stdout.strip())
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["capture"]["mode"], "off")
            self.assertFalse(config["capture"]["auto_start"])
            self.assertFalse(config["capture"]["assets_require_confirmation"])
            self.assertTrue(config["visual_capture"]["enabled"])
            self.assertTrue(config["visual_capture"]["production_requires_request"])
            config["capture"]["assets_require_confirmation"] = True
            config_path.write_text(json.dumps(config), encoding="utf-8")
            self.assertFalse(MODULE.load_config(project)["capture"]["assets_require_confirmation"])
            config["capture"]["mode"] = "manual"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manual = self.run_cli(
                project,
                "suggest-start",
                "--title",
                "Manual work",
                "--initiative",
                "mode-test",
                "--phase",
                "build",
            )
            self.assertEqual(json.loads(manual.stdout)["action"], "start_suggested")
            self.assertFalse(list((project / ".haostory").glob("*/manifest.json")))

            config["capture"]["mode"] = "off"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            disabled = self.run_cli(
                project,
                "suggest-start",
                "--title",
                "Disabled work",
                "--initiative",
                "mode-test",
                "--phase",
                "build",
            )
            self.assertEqual(json.loads(disabled.stdout)["action"], "ignore")

    def test_project_must_be_explicitly_enabled_and_can_be_paused_again(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            config_path = Path(self.run_cli(project, "setup").stdout.strip())

            before = json.loads(
                self.run_cli(
                    project,
                    "suggest-start",
                    "--title",
                    "A meaningful stage",
                    "--initiative",
                    "opt-in",
                    "--phase",
                    "build",
                ).stdout
            )
            self.assertEqual(before["action"], "ignore")

            enabled = json.loads(
                self.run_cli(
                    project,
                    "enable",
                    "--history-dir",
                    "docs/progress",
                ).stdout
            )
            self.assertEqual(enabled["mode"], "assisted-auto")
            self.assertEqual(enabled["history_directory"], "docs/progress")
            self.assertFalse(enabled["uploaded"])
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["capture"]["mode"], "assisted-auto")
            self.assertTrue(config["capture"]["auto_start"])
            self.assertEqual(config["capture"]["max_events_per_phase"], 4)
            self.assertTrue(config["project_history"]["enabled"])

            disabled = json.loads(self.run_cli(project, "disable").stdout)
            self.assertEqual(disabled["mode"], "off")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["capture"]["mode"], "off")
            self.assertFalse(config["capture"]["auto_start"])
            self.assertTrue(config["project_history"]["enabled"])

    def test_project_history_directory_cannot_escape_or_enter_private_control_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            outside = project.parent / "outside-history"
            for unsafe in ("../outside-history", ".git/story", ".haostory/shared", str(outside)):
                result = self.run_cli(
                    project,
                    "enable",
                    "--history-dir",
                    unsafe,
                    expected=1,
                )
                self.assertIn("history", result.stderr.lower())
            self.assertFalse(outside.exists())

    def test_lightweight_event_budget_folds_duplicates_and_requires_force_for_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Keep only decisive moments",
                    "--initiative",
                    "lightweight",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            for index in range(4):
                self.run_cli(
                    project,
                    "remember",
                    "--session",
                    session.name,
                    "--event",
                    "decision",
                    "--notes",
                    f"Decisive event {index}",
                    "--novelty-key",
                    f"decision-{index}",
                )
            folded = json.loads(
                self.run_cli(
                    project,
                    "remember",
                    "--session",
                    session.name,
                    "--event",
                    "decision",
                    "--notes",
                    "The same decision was reconfirmed.",
                    "--novelty-key",
                    "decision-0",
                ).stdout
            )
            self.assertEqual(folded["action"], "folded")

            skipped = json.loads(
                self.run_cli(
                    project,
                    "remember",
                    "--session",
                    session.name,
                    "--event",
                    "milestone",
                    "--notes",
                    "A routine extra event.",
                    "--novelty-key",
                    "routine-extra",
                ).stdout
            )
            self.assertEqual(skipped["action"], "skipped")
            self.assertEqual(skipped["reason"], "event_budget_reached")
            self.assertTrue(skipped["ask_only_if_critical"])

            forced = json.loads(
                self.run_cli(
                    project,
                    "remember",
                    "--session",
                    session.name,
                    "--event",
                    "recovery",
                    "--notes",
                    "A critical recovery worth preserving.",
                    "--novelty-key",
                    "critical-recovery",
                    "--force",
                ).stdout
            )
            self.assertEqual(forced["action"], "recorded")
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["events"]), 5)

    def test_share_stage_prepares_reviewed_git_friendly_materials_without_uploading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            self.run_cli(project, "enable", "--history-dir", "docs/project-history")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "First useful demo",
                    "--summary",
                    "Prove the smallest useful result.",
                    "--initiative",
                    "demo-flow",
                    "--phase",
                    "validate",
                ).stdout.strip()
            )
            asset = project / "stable-demo.png"
            asset.write_bytes(b"reviewed-image")
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "The first stable result worked on 192.168.1.2.",
                "--novelty-key",
                "stable-demo",
                "--claim",
                "The smallest useful flow is now demonstrable.",
                "--evidence-ref",
                "test:demo-flow",
                "--asset",
                str(asset),
            )
            self.run_cli(
                project,
                "close-phase",
                "--session",
                session.name,
                "--result",
                "The stage passed validation.",
                "--lesson",
                "Keep only evidence that explains the result.",
            )
            unconfirmed = self.run_cli(
                project,
                "share-stage",
                "--session",
                session.name,
                expected=1,
            )
            self.assertIn("--confirmed", unconfirmed.stderr)

            shared = json.loads(
                self.run_cli(
                    project,
                    "share-stage",
                    "--session",
                    session.name,
                    "--confirmed",
                ).stdout
            )
            package = Path(shared["package"])
            self.assertTrue(package.is_relative_to(project.resolve()))
            self.assertTrue((package / "README.md").exists())
            self.assertEqual((package / "assets" / "demo" / "stable-demo.png").read_bytes(), b"reviewed-image")
            article_material = (package / "README.md").read_text(encoding="utf-8")
            self.assertIn("The stage passed validation.", article_material)
            self.assertIn("The first stable result worked", article_material)
            self.assertNotIn("192.168.1.2", article_material)
            self.assertIn("<private-ip-redacted>", article_material)
            self.assertIn("assets/demo/stable-demo.png", article_material)
            self.assertFalse(shared["uploaded"])
            self.assertFalse(shared["committed"])
            self.assertFalse((package / ".git").exists())

    def test_omitted_session_requires_one_active_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            only = Path(
                self.run_cli(
                    project,
                    "start",
                    "--session",
                    "only-active",
                    "--title",
                    "Only active window",
                    "--initiative",
                    "only-active",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "remember",
                "--event",
                "decision",
                "--notes",
                "The unique active window may be inferred.",
                "--novelty-key",
                "unique-window",
            )
            only_manifest = json.loads((only / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(only_manifest["events"][-1]["novelty_key"], "unique-window")

            second = Path(
                self.run_cli(
                    project,
                    "start",
                    "--session",
                    "second-active",
                    "--title",
                    "Second active window",
                    "--initiative",
                    "second-active",
                    "--phase",
                    "validate",
                ).stdout.strip()
            )
            result = self.run_cli(
                project,
                "remember",
                "--event",
                "decision",
                "--notes",
                "This must not be routed by directory name.",
                "--novelty-key",
                "ambiguous-window",
                expected=1,
            )
            self.assertIn("only-active", result.stderr)
            self.assertIn("second-active", result.stderr)
            self.assertIn("--session", result.stderr)
            for session in (only, second):
                manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
                self.assertNotIn("ambiguous-window", json.dumps(manifest))

    def test_v1_session_fallback_uses_manifest_updated_at(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            journal = project / ".haostory"
            for name, updated_at in (
                ("z-old", "2026-01-01T00:00:00+00:00"),
                ("a-new", "2026-08-15T00:00:00+00:00"),
            ):
                session = journal / name
                (session / "evidence").mkdir(parents=True)
                (session / "assets").mkdir()
                (session / "manifest.json").write_text(
                    json.dumps(
                        {
                            "schema": "haostory/v1",
                            "project": project.name,
                            "title": name,
                            "summary": "",
                            "type": "software",
                            "started_at": updated_at,
                            "updated_at": updated_at,
                            "stages": [],
                            "assets": [],
                            "commands": [],
                        }
                    ),
                    encoding="utf-8",
                )
            self.run_cli(
                project,
                "checkpoint",
                "--stage",
                "decision",
                "--notes",
                "The newest V1 manifest is selected by updated_at.",
            )
            old = json.loads((journal / "z-old" / "manifest.json").read_text(encoding="utf-8"))
            new = json.loads((journal / "a-new" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(old["stages"], [])
            self.assertEqual(new["stages"][-1]["notes"], "The newest V1 manifest is selected by updated_at.")

    def test_session_ids_cannot_escape_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            outside = project / "outside-session"
            outside.mkdir()
            outside_manifest = {
                "schema": "haostory/v1",
                "project": project.name,
                "title": "Outside",
                "summary": "",
                "type": "software",
                "started_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "capture_window": {"status": "active"},
                "events": [],
                "stages": [],
                "assets": [],
                "commands": [],
            }
            (outside / "manifest.json").write_text(json.dumps(outside_manifest), encoding="utf-8")
            for unsafe_session in ("../outside-session", str(outside)):
                result = self.run_cli(
                    project,
                    "remember",
                    "--session",
                    unsafe_session,
                    "--event",
                    "decision",
                    "--notes",
                    "Must stay inside the journal.",
                    "--novelty-key",
                    "path-escape",
                    expected=1,
                )
                self.assertIn("direct child", result.stderr)
            unchanged = json.loads((outside / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(unchanged["events"], [])

    def test_registry_path_cannot_escape_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            config_path = Path(self.run_cli(project, "setup").stdout.strip())
            outside = project.parent / "outside-registry.json"
            outside.write_text('{"sentinel": true}\n', encoding="utf-8")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            for unsafe_registry in ("../outside-registry.json", str(outside)):
                config["story_memory"]["registry"] = unsafe_registry
                config_path.write_text(json.dumps(config), encoding="utf-8")
                result = self.run_cli(
                    project,
                    "registry",
                    "do-not-repeat",
                    "--text",
                    "Do not write outside the journal.",
                    expected=1,
                )
                self.assertIn("inside", result.stderr)
                self.assertIn(".haostory", result.stderr)
                self.assertEqual(outside.read_text(encoding="utf-8"), '{"sentinel": true}\n')

    def test_symlinked_journal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            project = self.make_project(parent, "symlink-project")
            outside = parent / "outside-journal"
            outside.mkdir()
            (project / ".haostory").symlink_to(outside, target_is_directory=True)
            result = self.run_cli(project, "setup", expected=1)
            self.assertIn("symlinked", result.stderr)
            self.assertFalse((outside / "story-registry.json").exists())

    def test_archive_only_and_do_not_repeat_have_cli_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            first = self.run_cli(
                project,
                "registry",
                "do-not-repeat",
                "--text",
                "The complete project origin.",
            )
            second = self.run_cli(
                project,
                "registry",
                "do-not-repeat",
                "--text",
                "The complete project origin.",
            )
            self.assertEqual(json.loads(first.stdout)["action"], "recorded")
            self.assertEqual(json.loads(second.stdout)["action"], "already_present")

            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Human publication controls",
                    "--initiative",
                    "human-controls",
                    "--phase",
                    "design",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "decision",
                "--notes",
                "This restates excluded background.",
                "--novelty-key",
                "origin-repeat",
                "--claim",
                "The complete project origin.",
            )
            checked = json.loads(
                self.run_cli(project, "registry", "check", "--session", session.name).stdout
            )
            self.assertEqual(checked["recommendation"], "archive")
            self.assertEqual(checked["repeated_claims"], ["The complete project origin."])

            marked = json.loads(
                self.run_cli(
                    project,
                    "archive-only",
                    "--session",
                    session.name,
                    "--reason",
                    "The user said this must not be public.",
                ).stdout
            )
            self.assertTrue(marked["archive_only"])
            plan = json.loads(self.run_cli(project, "story-plan", "--session", session.name).stdout)
            self.assertEqual(plan["route"], "archive")
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["archive_only"])
            self.assertIn("must not be public", manifest["archive_only_reason"])

    def test_duplicate_failures_fold_and_recovery_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            started = self.run_cli(
                project,
                "start",
                "--title",
                "Deduplicate retries",
                "--initiative",
                "dedupe",
                "--phase",
                "build",
            )
            session = Path(started.stdout.strip())
            for _ in range(3):
                self.run_cli(
                    project,
                    "remember",
                    "--session",
                    session.name,
                    "--event",
                    "failure",
                    "--notes",
                    "The same test failed with exit code 1.",
                    "--novelty-key",
                    "test-exit-1",
                )
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "recovery",
                "--notes",
                "A different implementation made the test pass.",
                "--novelty-key",
                "test-exit-1",
            )
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            failures = [item for item in manifest["events"] if item["event_type"] == "failure"]
            recoveries = [item for item in manifest["events"] if item["event_type"] == "recovery"]
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]["occurrence_count"], 3)
            self.assertEqual(len(recoveries), 1)

    def test_validate_phase_inherits_minimal_build_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            build = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Build the capture model",
                    "--summary",
                    "Create the first working implementation.",
                    "--initiative",
                    "capture-v2",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "close-phase",
                "--session",
                build.name,
                "--result",
                "The build is runnable.",
                "--lesson",
                "Validation must test behavior, not implementation activity.",
            )
            validate = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Validate the capture model",
                    "--initiative",
                    "capture-v2",
                    "--phase",
                    "validate",
                ).stdout.strip()
            )
            manifest = json.loads((validate / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["phase"], "validate")
            self.assertEqual(manifest["necessary_context"]["source_session"], build.name)
            self.assertNotEqual(validate.name, build.name)

    def test_registry_marks_published_claim_without_new_evidence_as_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")

            first = Path(
                self.run_cli(
                    project,
                    "start",
                    "--session",
                    "positioning-first",
                    "--title",
                    "Positioning",
                    "--initiative",
                    "positioning",
                    "--phase",
                    "design",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "remember",
                "--session",
                first.name,
                "--event",
                "decision",
                "--notes",
                "Keep the product personally curated.",
                "--novelty-key",
                "curated-positioning",
                "--claim",
                "UP2U is curated by one person.",
                "--evidence-ref",
                "decision:positioning",
            )
            self.run_cli(
                project,
                "registry",
                "publish",
                "--session",
                first.name,
                "--story",
                "positioning-v1",
                "--channel",
                "wechat",
                "--confirmed",
            )

            second = Path(
                self.run_cli(
                    project,
                    "start",
                    "--session",
                    "positioning-repeat",
                    "--title",
                    "Positioning again",
                    "--initiative",
                    "positioning-followup",
                    "--phase",
                    "design",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "remember",
                "--session",
                second.name,
                "--event",
                "decision",
                "--notes",
                "Repeat the existing positioning.",
                "--novelty-key",
                "curated-positioning-repeat",
                "--claim",
                "UP2U is curated by one person.",
                "--evidence-ref",
                "decision:positioning",
            )
            checked = self.run_cli(project, "registry", "check", "--session", second.name)
            result = json.loads(checked.stdout)
            self.assertEqual(result["recommendation"], "archive")
            self.assertEqual(result["repeated_claims"], ["UP2U is curated by one person."])

    def test_pause_stops_auto_remember_until_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Pause test",
                    "--initiative",
                    "pause-test",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            self.run_cli(project, "pause", "--session", session.name, "--reason", "This section is excluded.")
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "decision",
                "--notes",
                "This must not be captured.",
                "--novelty-key",
                "excluded",
                expected=1,
            )
            self.run_cli(project, "resume", "--session", session.name)
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "decision",
                "--notes",
                "Capture resumed.",
                "--novelty-key",
                "resumed",
            )
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("excluded", json.dumps(manifest["events"]))
            self.assertIn("resumed", json.dumps(manifest["events"]))

    def test_remember_stores_visual_assets_directly_without_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            asset = project / "demo.png"
            asset.write_bytes(b"first-stable-frame")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Asset boundary",
                    "--initiative",
                    "assets",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "Save the stable desktop result directly.",
                "--novelty-key",
                "asset-demo",
                "--asset",
                str(asset),
            )
            asset.write_bytes(b"second-stable-frame")
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "Save the stable mobile result directly.",
                "--novelty-key",
                "asset-demo",
                "--asset",
                str(asset),
            )
            copied = sorted((session / "assets" / "demo").glob("*.png"))
            self.assertEqual(len(copied), 2)
            self.assertEqual({path.read_bytes() for path in copied}, {b"first-stable-frame", b"second-stable-frame"})
            self.assertFalse((session / "candidates").exists())
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            event = manifest["events"][0]
            self.assertEqual(event["occurrence_count"], 2)
            self.assertEqual(len(event["assets"]), 2)
            self.assertEqual(len(manifest["assets"]), 2)

            sensitive = project / "secret-screen.png"
            sensitive.write_bytes(b"sensitive")
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "Never save a sensitive-looking path.",
                "--novelty-key",
                "sensitive-asset",
                "--asset",
                str(sensitive),
                expected=1,
            )
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("sensitive-asset", json.dumps(manifest))

    def test_handoff_close_does_not_export_publish_or_register(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Close on handoff",
                    "--initiative",
                    "handoff",
                    "--phase",
                    "build",
                ).stdout.strip()
            )
            asset = project / "phase-result.png"
            asset.write_bytes(b"stable-phase-result")
            self.run_cli(
                project,
                "remember",
                "--session",
                session.name,
                "--event",
                "demo",
                "--notes",
                "The stage has a stable visual result.",
                "--novelty-key",
                "phase-result",
                "--claim",
                "The phase produced a runnable result.",
                "--evidence-ref",
                "demo:phase-result",
                "--asset",
                str(asset),
            )
            closed = self.run_cli(
                project,
                "close-phase",
                "--session",
                session.name,
                "--result",
                "Implementation entered review.",
                "--handoff",
            )
            result = json.loads(closed.stdout)
            self.assertEqual(result["status"], "closed")
            self.assertFalse(result["published"])
            self.assertFalse(result["content_generated"])
            readiness = result["content_readiness"]
            self.assertEqual(readiness["asset_count"], 1)
            self.assertEqual(readiness["assets_path"], str(session / "assets"))
            self.assertTrue(readiness["production_requires_request"])
            self.assertEqual(readiness["recommended_route"], "standalone_story")
            self.assertIn("video", readiness["prompt"])
            self.assertIn("article", readiness["prompt"])
            self.assertFalse((session / "exports").exists())
            self.assertTrue((session / "privacy-report.json").exists())
            report = json.loads((session / "privacy-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["asset_review_gate"], "final_content")
            self.assertTrue(report["visual_review_at_content_gate"])
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["content_readiness"]["asset_count"], 1)
            registry = json.loads((project / ".haostory" / "story-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["published_stories"], [])

    def test_v1_commands_work_on_manifest_without_v2_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            session = project / ".haostory" / "legacy-v1"
            (session / "evidence").mkdir(parents=True)
            (session / "assets").mkdir()
            (session / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema": "haostory/v1",
                        "project": "demo-project",
                        "title": "Legacy V1",
                        "summary": "An old manifest.",
                        "type": "software",
                        "started_at": "2026-01-01T00:00:00+00:00",
                        "updated_at": "2026-01-01T00:00:00+00:00",
                        "stages": [],
                        "assets": [],
                        "commands": [],
                    }
                ),
                encoding="utf-8",
            )
            self.run_cli(
                project,
                "checkpoint",
                "--session",
                session.name,
                "--stage",
                "decision",
                "--notes",
                "Legacy checkpoint remains supported.",
            )
            self.run_cli(
                project,
                "finish",
                "--session",
                session.name,
                "--outcome",
                "Legacy session finished.",
                "--lesson",
                "Compatibility is explicit.",
            )
            self.run_cli(project, "audit", "--session", session.name)
            self.run_cli(project, "export", "--session", session.name)
            manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "haostory/v1")

    def test_high_risk_privacy_finding_blocks_publication_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = self.make_project(Path(temp))
            self.run_cli(project, "setup")
            session = Path(
                self.run_cli(
                    project,
                    "start",
                    "--title",
                    "Privacy gate",
                    "--initiative",
                    "privacy",
                    "--phase",
                    "validate",
                ).stdout.strip()
            )
            unsafe = session / "evidence" / "unsafe.txt"
            unsafe.write_text("Bearer " + "x" * 24, encoding="utf-8")
            self.run_cli(project, "export", "--session", session.name, expected=2)
            package = json.loads((session / "exports" / "content-package.json").read_text(encoding="utf-8"))
            self.assertFalse(package["privacy"]["release_ready"])
            self.assertEqual(package["publication_recommendation"], "blocked_privacy")

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
