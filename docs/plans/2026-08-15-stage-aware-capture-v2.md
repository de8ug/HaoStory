# Stage-Aware Capture V2 Implementation Plan

> **For Codex:** Implement this plan task-by-task in the current workstream. Do not publish, push, or change the accepted product rules.

**Goal:** Add deterministic stage-aware capture, lifecycle control, event deduplication, and published-story memory while preserving HaoStory V1 commands and data.

**Architecture:** Keep `haostory/v1` manifests readable and writable, adding optional initiative, phase, capture-window, event, and inherited-context fields. Store project-level publication memory in ignored `.haostory/story-registry.json`; expose all mutations through explicit CLI commands, while `suggest-start` provides the deterministic assisted-auto routing layer used by the Skill.

**Tech Stack:** Python standard library CLI, JSON/Markdown local files, `unittest` integration tests.

---

### Task 1: Lock V1 Compatibility and V2 Acceptance Behavior

**Files:**
- Modify: `tests/test_haostory.py`

1. Retain the existing V1 end-to-end export and privacy tests unchanged in intent.
2. Add tests for the ten accepted scenarios: meaningful build start, formatting exclusion, failure folding plus recovery, phase inheritance, registry repetition, pause behavior, manual assets, handoff close without publication, V1 commands, and privacy blocking.
3. Run `python3 -m unittest -v tests/test_haostory.py`; expect new tests to fail before implementation.

### Task 2: Add the V2-Compatible Data and Lifecycle Layer

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`

1. Extend default configuration with `manual | assisted-auto | off` capture rules and story-memory settings.
2. Add optional Project → Initiative → Phase → Capture Window → Event metadata without changing `haostory/v1` or breaking old manifests.
3. Add deterministic `suggest-start`, enhanced `start`, `pause`, `resume`, `remember`, and `close-phase` commands.
4. Reject automatic event capture when paused/off/closed; never accept visual assets through automatic `remember`.
5. Fold equal `event_type + novelty_key` events into one occurrence counter, while preserving a later recovery event.
6. Run focused lifecycle and compatibility tests; expect pass.

### Task 3: Add Published-Story Memory and Export Routing

**Files:**
- Modify: `skill/haostory/scripts/haostory.py`
- Modify: `tests/test_haostory.py`

1. Add `story-plan`, `registry check`, and confirmation-only `registry publish` commands.
2. Compare normalized claims and evidence refs against `.haostory/story-registry.json`.
3. Route repeated claims without new evidence to `archive`, valuable but under-evidenced work to `merge_later`, and eligible work to the phase-aware route.
4. Include novelty and privacy gates in `content-package.json`; never publish or register an export automatically.
5. Run registry, export, and privacy tests; expect pass.

### Task 4: Document Natural-Language and Migration Rules

**Files:**
- Modify: `skill/haostory/SKILL.md`
- Modify: `skill/haostory/references/output-schema.md`
- Modify: `skill/haostory/references/project-integration.md`
- Modify: `skill/haostory/assets/haostory.example.json`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

1. Document assisted-auto notices, start exclusions, high-confidence events, natural-language triggers, phase story questions, and human-only asset/brand/publication authority.
2. Document optional V2 fields, registry shape, V1 migration behavior, and CLI examples.
3. Verify the docs contain no private absolute paths and remain bilingual where required.

### Task 5: Demonstrate and Validate

**Files:**
- Create locally ignored demo sessions under a temporary project only.

1. Run the full unit suite.
2. Run a clean demo project through `build` start/demo/close, then `validate` start with inherited context and registry deduplication.
3. Run privacy audit and confirm no automatic asset copy or publication occurs.
4. Run the official Skill validator available in the local Codex skill tooling; update `agents/openai.yaml` only if it exists and validation requires a relevant change.
5. Record exact commands and outcomes in workstream status and handoff.

### Task 6: Enter Review

**Files:**
- Modify: workstream `status.json`
- Modify: workstream `handoff.md`

1. Update the milestone status after implementation and again after verification.
2. Fill the handoff with acceptance results, changed files, commands, risks, and HaoStory signal.
3. Set the workstream state to `review`, stop implementation, and return to the central conversation for acceptance.
