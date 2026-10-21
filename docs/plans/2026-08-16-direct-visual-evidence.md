# Direct Visual Evidence Implementation Plan

> **For Codex:** Implement this plan task-by-task in the current repository. Do not publish, push, or install the Skill globally.

**Goal:** Capture key screenshots directly into a HaoStory session during work, then prompt for optional content production with the asset location when a phase closes.

**Architecture:** Keep screenshot creation in the Agent's existing browser/computer tools and make the CLI the deterministic persistence layer. Extend `remember` to copy selected-by-workflow files directly into `assets/`, store their event relationship, and make `close-phase` compute a local content-readiness summary without exporting, rendering, or publishing.

**Tech Stack:** Python standard library CLI, JSON/Markdown local files, `unittest` integration tests.

---

### Task 1: Lock the New Authorization Boundary

**Files:**
- Modify: `tests/test_haostory.py`

1. Replace the old per-asset-confirmation regression with a test that `remember --asset` copies key screenshots directly into `assets/`.
2. Verify repeated filenames do not overwrite earlier evidence.
3. Verify no `candidates/` directory or candidate manifest is created.
4. Verify sensitive-looking asset paths remain rejected.
5. Run the focused tests and confirm failure before implementation.

### Task 2: Add Direct Visual Evidence to Events

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`

1. Add repeatable `remember --asset` arguments.
2. Copy each file into the event's asset directory with collision-safe names.
3. Store relative paths on the event, compatibility stage, and manifest asset list.
4. Preserve deduplication: folding the same event merges newly supplied asset refs without losing prior files.
5. Keep sensitive-path rejection and local `.haostory/` containment intact.

### Task 3: Prompt for Content at Phase Close

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`
- Modify: `tests/test_haostory.py`

1. On `close-phase`, run the local privacy audit and story-memory plan without generating exports.
2. Persist `content_readiness` with event, evidence, and asset counts, asset location, route, privacy state, and `production_requires_request: true`.
3. Return a clear prompt asking whether to produce video, article, both, or archive.
4. Verify close still does not create exports, publish, or update published-story memory.

### Task 4: Update Skill, Config, and User Documentation

**Files:**
- Modify: `skill/haostory/SKILL.md`
- Modify: `skill/haostory/assets/haostory.example.json`
- Modify: `skill/haostory/references/privacy.md`
- Modify: `skill/haostory/references/output-schema.md`
- Modify: `skill/haostory/references/project-integration.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `examples/stage-aware-v2/README.md`

1. Replace per-image confirmation with direct capture of stable, meaningful visual evidence.
2. Define the visual triggers, stable-view requirement, invalid-frame recapture behavior, and prohibited sensitive contexts.
3. State the three separate gates: automatic local capture, explicit content-production request, explicit publication approval.
4. Document the phase-close prompt and asset location.

### Task 5: Validate

1. Run the full unittest suite.
2. Run Python syntax, JSON, and `git diff --check` validation.
3. Run the official Skill validator.
4. Confirm no candidates workflow, automatic export, rendering, publication, push, or global installation occurred.
