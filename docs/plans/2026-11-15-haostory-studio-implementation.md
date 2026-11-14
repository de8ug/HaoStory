# HaoStory Studio Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a portable local HaoStory Studio that lets users select approved project material, choose an output format and story angle, identify useful missing material, and hand a deterministic production request back to the invoking AI agent.

**Architecture:** Add a standalone standard-library Studio module behind the existing CLI. The module serves bundled static assets on localhost, exposes narrow JSON APIs for safe discovery/analysis/job creation, and stores private requests under `.haostory/studio/`. Host conversation access remains an explicit adapter contract rather than a hidden filesystem scan.

**Tech Stack:** Python 3 standard library, semantic HTML, CSS, vanilla JavaScript, `unittest`.

---

### Task 1: Safe source discovery

**Files:**
- Create: `skill/haostory/scripts/studio.py`
- Create: `tests/test_studio.py`

1. Write failing tests proving discovery returns only explanatory text and media metadata, ignores hidden/source/dependency/secret paths, does not read file bodies, and caps results.
2. Run `python3 -m unittest tests.test_studio -v` and verify failure.
3. Implement project-relative containment, allowlisted extensions and directories, size limits, and metadata-only results.
4. Run the focused tests and verify pass.

### Task 2: Selected-material analysis and template catalog

**Files:**
- Modify: `skill/haostory/scripts/studio.py`
- Modify: `tests/test_studio.py`
- Create: `skill/haostory/references/content-studio.md`

1. Write failing tests proving only selected paths are opened, unsafe selections fail, text is bounded and sanitized, and image metadata is recorded without OCR.
2. Add deterministic story-signal detection, format-specific templates, three ranked recommendations, and concise gap prompts.
3. Test article, video, Xiaohongshu, multi-format, empty-material, and unsafe-path behavior.

### Task 3: Private production job protocol

**Files:**
- Modify: `skill/haostory/scripts/studio.py`
- Modify: `tests/test_studio.py`

1. Write failing tests for creating, listing, reading, and completing a project-local job.
2. Store requests under `.haostory/studio/jobs/<id>/request.json` with selected relative paths, host conversation references, format, angle, audience, goals, supplements, and privacy flags.
3. Ensure sponsor copy is never stored in the production request.
4. Add deterministic CLI-readable job summaries and output registration.

### Task 4: Local HTTP API and console UI

**Files:**
- Modify: `skill/haostory/scripts/studio.py`
- Create: `skill/haostory/assets/studio/index.html`
- Create: `skill/haostory/assets/studio/studio.css`
- Create: `skill/haostory/assets/studio/studio.js`
- Modify: `tests/test_studio.py`

1. Add API tests for capabilities, sources, analyze, templates, jobs, and error envelopes.
2. Implement a localhost-only threaded server with strict routes, JSON limits, no directory listing, and security headers.
3. Build the four-step Material → Format → Angle → Produce interface with responsive layout, keyboard support, reduced motion, loading/error/empty states, and an explicit selected-material summary.
4. Add configurable console-only Hao AI Lab, `HaoAILab`, and OneTake notices.

### Task 5: CLI and agent handoff

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`
- Modify: `tests/test_haostory.py`
- Modify: `skill/haostory/SKILL.md`

1. Add failing CLI tests for `studio`, `studio-job latest`, `studio-job show`, and `studio-job complete`.
2. Implement browser launch with `--no-open`, automatic free port selection, explicit project root, and readable JSON output for agents.
3. Document the host adapter contract: list only metadata first; retrieve conversation content only after a selected job requests it.
4. Preserve paused-by-default capture behavior; opening Studio is an explicit content-production action, not capture opt-in.

### Task 6: Public documentation and packaging

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `skill/haostory/references/brand-and-commercial.md`
- Modify: `skill/haostory/references/privacy.md`
- Modify: `skill/haostory/references/output-schema.md`
- Modify: `skill/haostory/assets/haostory.example.json`
- Rebuild: `dist/haostory.skill`

1. Reposition the project as HaoStory Studio while retaining capture as an optional source.
2. Keep English and Chinese documentation aligned.
3. Document sponsor configurability and the rule that console notices never enter generated content.
4. Rebuild the distributable from the current `skill/haostory` tree and inspect its contents.

### Task 7: Verification

**Files:**
- Modify as needed based on observed defects.

1. Run `python3 -m unittest discover -s tests -v`.
2. Run Python compilation for all scripts.
3. Run the Skill validator.
4. Launch Studio against a synthetic temporary project.
5. Inspect desktop and mobile states visually, including source selection, recommendations, job success, empty state, and error state.
6. Confirm no network request occurs and the Git working tree contains only intended source, test, documentation, and rebuilt distribution changes.
