---
name: haostory
description: Capture real software development, product experiments, content production, or research as privacy-reviewed bilingual story assets. Use for stage-aware local capture, meaningful decisions, failures and recoveries, Git or test evidence, story deduplication, build-in-public drafts, articles, or video scripts while work is happening.
---

# HaoStory

Turn real work into evidence-backed stories. Capture first, select second, publish only after human review.

## Core rule

Record meaningful changes in judgment, not every mechanical action. Allow two content layers:

1. what was built or learned;
2. how it was built or learned.

Do not recursively create content about routine packaging unless that work reveals a reusable method, failure, or result.

## Capture modes and authority

Read `capture.mode` from `.haostory.json`:

- `manual`: record only after an explicit user request;
- `assisted-auto`: locally start or resume meaningful work and record high-confidence observable events; this is the default for an enabled local project;
- `off`: do not capture.

Assisted-auto is not automatic publication. Screenshots, recordings, video, private messages, analytics, visual assets, story splitting or merging, people, clients, brand, commercial CTA, and publication always require human selection or confirmation. A configured brand is treated as the user's prior selection, but the final export still requires review.

## Stage-aware workflow

1. Read `references/privacy.md` before the first capture in a repository.
2. Run `scripts/haostory.py setup` when the project has no `.haostory.json`.
3. Model work as Project → Initiative → Phase → Capture Window → Event. Phases are `discovery`, `design`, `build`, `validate`, `release`, and `operate`.
4. Before meaningful work, run `suggest-start` in assisted-auto mode or explicit `start` in manual mode. If capture starts, tell the user in commentary: “HaoStory 已为 `<initiative>/<phase>` 开始本地记录”. Never start silently.
5. Run `remember` only for a high-confidence observable event: `decision`, `scope_change`, `failure`, `recovery`, `before_after`, `milestone`, `demo`, `metric`, or redacted `external_signal`. Generate a stable `novelty_key`; repeated `event type + novelty_key` attempts fold into one event.
6. Use `pause` while waiting or excluding a section, `resume` when the same goal and acceptance criteria continue, and `close-phase` when the phase result is known or a handoff enters review. Closing does not export or publish.
7. Before content work, run `registry check` and `story-plan`; then run `audit` and explicit `export`. A repeated claim without new evidence routes to archive.
8. Improve generated drafts using the evidence package. Rewrite or translate each requested language naturally; do not leave untranslated source text in the other language. Do not invent events, metrics, quotes, or results.
9. Ask for human approval before publishing, registering a story as published, or copying any raw evidence into a public repository.

Read `references/project-integration.md` when the user wants HaoStory applied automatically across future sessions in a project.

## Assisted-auto start rules

Start or resume only when all are true:

- `.haostory.json` exists or project instructions explicitly enable HaoStory;
- the task is development, a product experiment, content production, or research;
- it has a stage goal, artifact, or acceptance criteria;
- no active window covers the same `project + initiative + phase`;
- the work is outside sensitive or user-excluded scope.

Do not auto-start for formatting, dependency installation, a simple bug fix, consulting answers, mechanical renames, or packaging without an independent result. Do not checkpoint every command, file save, repeated error, wording change, background restatement, or ordinary passing test.

Open a new phase when success criteria, target users, product position, release/operation state, or the audience's story question changes. Otherwise pause or resume the existing phase. Build asks how an idea became runnable; validate asks whether it works and where its limits are. Inherited context must remain minimal.

## Session and path routing

Omit `--session` only when exactly one active or paused capture window exists. If multiple windows are active or paused, stop and ask the user to choose from the CLI's listed candidates; never infer from directory names. With no active window, V1 compatibility selects the manifest with the latest `updated_at`.

Treat ordinary `--session` values as direct child names under the current project's `.haostory/`. Do not pass absolute paths, `..`, separators, or symlinks. Keep `story_memory.registry` inside that same `.haostory/` directory.

## Commands

From the target project root:

```bash
python3 <skill>/scripts/haostory.py setup
python3 <skill>/scripts/haostory.py suggest-start --title "Stage goal" --initiative capture-v2 --phase build
python3 <skill>/scripts/haostory.py start --title "Task title" --summary "Why it matters" --type product
python3 <skill>/scripts/haostory.py checkpoint --stage decision --notes "What changed" --decision "Why"
python3 <skill>/scripts/haostory.py checkpoint --stage tests --notes "What was verified" --run npm test
python3 <skill>/scripts/haostory.py remember --event failure --notes "What failed" --novelty-key test-exit-1
python3 <skill>/scripts/haostory.py pause --reason "This section is excluded"
python3 <skill>/scripts/haostory.py resume
python3 <skill>/scripts/haostory.py close-phase --result "What is now known" --handoff
python3 <skill>/scripts/haostory.py archive-only --reason "The user said this must not be public"
python3 <skill>/scripts/haostory.py registry do-not-repeat --text "Background that must not be repeated"
python3 <skill>/scripts/haostory.py registry check
python3 <skill>/scripts/haostory.py story-plan
python3 <skill>/scripts/haostory.py finish --outcome "What happened" --lesson "What changed in our understanding"
python3 <skill>/scripts/haostory.py audit
python3 <skill>/scripts/haostory.py export
python3 <skill>/scripts/haostory.py registry publish --story story-id --channel channel-name --confirmed
```

Use `--asset path/to/file` only for material the user intentionally selected. Treat screenshots as potentially sensitive even when the text audit passes.

## Output policy

Generate Chinese and English drafts by default. Keep raw evidence local under `.haostory/`. Read `references/output-schema.md` when changing the package format.

Generated drafts are scaffolds, not final editorial copy. Strengthen them around one tension, one changed judgment, and verifiable proof. Prefer:

- a specific result over a broad claim;
- a failed attempt over a smooth chronology;
- before/after evidence over adjectives;
- the user's judgment over generic AI narration.

## Story selection

Export only after an explicit request. Recommend a standalone story only when it has a new claim or new evidence and sufficient proof. Otherwise route it to archive or merge later. For eligible work, retain the V1 story-value signals:

- a real conflict or surprise;
- a decision that changed;
- visual or test evidence;
- a lesson useful beyond this project;
- a timely reason to care;
- a result that can be demonstrated.

Read `references/story-shapes.md` when choosing an article or video angle.

Old `haostory/v1` manifests and `start/checkpoint/finish/audit/export` remain supported. V2 adds optional fields and never requires destructive migration. Read `references/output-schema.md` before changing compatibility behavior.

## Natural-language control

Map intent to deterministic operations:

| User intent | Action |
|---|---|
| “从这里开始记录” | `start` the current phase |
| “这是上一阶段的继续” | start/resume with the same initiative and inherited context |
| “这段别记” | `pause` and retain the exclusion reason |
| “这个失败留一下” | `remember --event failure --force` |
| “这个可以单独做一期” | mark a standalone candidate for human review |
| “前面不用再讲了” | `registry do-not-repeat --text "..."` |
| “到这里先结束” | `close-phase`, without export or publication |
| “把这阶段整理成视频和文章” | `registry check`, `story-plan`, `audit`, then explicit `export` |
| “这两个阶段合成一篇” | create a human-approved combined plan without changing source evidence |
| “这次不要公开” | `archive-only --reason "..."` |

## Brand and commercial boundary

Keep public defaults neutral. Apply the user's brand only from `.haostory.json`. Read `references/brand-and-commercial.md` before adding attribution, calls to action, sponsor language, or commercial availability.

## Privacy boundary

Never capture `.env` files, credentials, cookies, private keys, browser profiles, production user data, or private conversations. The text sanitizer reduces risk but does not replace manual review. If the privacy report contains a high-severity finding, do not recommend publication.
