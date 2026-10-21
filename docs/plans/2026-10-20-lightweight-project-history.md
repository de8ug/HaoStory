# Lightweight Project History Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make HaoStory an explicit opt-in, low-frequency stage journal that can prepare a reviewed, Git-friendly package of key notes and images inside the named project.

**Architecture:** Keep raw captures private in `.haostory/`. Add explicit project enable/disable commands, a soft per-phase event budget, and a separately confirmed `share-stage` operation that copies a concise stage brief plus approved assets into a safe project-relative history directory. HaoStory never commits, pushes, uploads, publishes, or starts content production by itself.

**Tech Stack:** Python standard library CLI, JSON manifests/configuration, Markdown output, `unittest`.

---

### Task 1: Lock the opt-in and lightweight policy with tests

**Files:**
- Modify: `tests/test_haostory.py`

1. Add a test proving `setup` leaves capture off and `enable` explicitly selects assisted-auto plus a safe history directory.
2. Add a test proving `disable` returns the project to paused/off state.
3. Add a test proving a fifth distinct event is skipped at the default phase budget while a folded duplicate does not consume another slot and `--force` can preserve an exceptional event.
4. Run the focused tests and confirm they fail before implementation.

### Task 2: Implement project activation and capture budget

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`
- Modify: `skill/haostory/assets/haostory.example.json`

1. Change new-project defaults to `capture.mode: off` and `auto_start: false`.
2. Add deterministic `enable` and `disable` commands that update only HaoStory configuration.
3. Add `max_events_per_phase: 4` and return a structured `skipped` result when the budget is full, unless the event folds into an existing identity or the caller passes `--force`.
4. Validate configured history paths remain ordinary project-relative directories outside `.git/` and `.haostory/`.

### Task 3: Add the reviewed Git-friendly stage package

**Files:**
- Modify: `tests/test_haostory.py`
- Modify: `skill/haostory/scripts/haostory.py`

1. Add a failing end-to-end test for `share-stage --confirmed` after a closed phase.
2. Require a closed phase, successful privacy audit, and explicit confirmation.
3. Write a concise `README.md` with the phase goal, outcome, lesson, key events, evidence references, and relative image links.
4. Copy only the session assets already selected for that phase into the configured project history directory.
5. Reject absolute, escaping, symlinked, `.git/`, or `.haostory/` history destinations.
6. Return local paths and Git readiness without running Git mutation or network operations.

### Task 4: Simplify and align the public guidance

**Files:**
- Modify: `skill/haostory/SKILL.md`
- Modify: `skill/haostory/references/project-integration.md`
- Modify: `skill/haostory/references/output-schema.md`
- Modify: `skill/haostory/references/privacy.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `examples/stage-aware-v2/README.md`

1. Define the core outcome as a small number of stage-ready writing and visual assets, not a comprehensive activity log.
2. State that Howie's operating policy is paused by default and activation is per named project.
3. Explain the two storage layers: private raw journal and reviewed project history.
4. Instruct the Agent to ask at most one focused question only when a genuinely important capture choice is ambiguous.
5. Keep English and Chinese documentation aligned and explicitly prohibit automatic commit, push, upload, publication, or content generation.

### Task 5: Verify the full change

**Files:**
- Test: `tests/test_haostory.py`
- Validate: `skill/haostory`

1. Run `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
2. Run `python3 -m py_compile skill/haostory/scripts/haostory.py`.
3. Run `python3 -m json.tool skill/haostory/assets/haostory.example.json`.
4. Run `git diff --check`.
5. Run the official Skill validator against `skill/haostory`.
6. Confirm `git status --short` contains no generated captures or shared test packages.
