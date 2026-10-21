---
name: haostory
description: Keep a lightweight, stage-based project history with a few key decisions, proofs, and screenshots for later articles or videos. Use only after the user explicitly enables HaoStory for a named project, or asks to organize, review, or produce that project's story materials.
---

# HaoStory

Keep the few moments that will make a later article or video true, concrete, and easy to produce.

## Core rule

HaoStory is paused by default. Do not start or maintain capture merely because a project is being developed. Record only after the user enables it for a named project or explicitly starts a session.

Record meaningful changes in judgment, not every mechanical action. Keep two possible content layers:

1. what was built or learned;
2. how it was built or learned.

Do not recursively create content about routine packaging unless that work reveals a reusable method, failure, or result. A normal phase should contain no more than four distinct events; repeated events fold together. Preserve an exceptional fifth event only with `--force`.

## Capture modes and authority

Read `capture.mode` from `.haostory.json`:

- `manual`: record only after an explicit user request;
- `assisted-auto`: locally start or resume meaningful work and record high-confidence observable events after the project was explicitly enabled;
- `off`: do not capture.

`setup` initializes an off/paused project. `enable` is the explicit project-level opt-in; `disable` pauses future capture without deleting history. An explicit `start` may create one manual session while the project remains off.

In assisted-auto mode, capture useful screenshots at visual `failure`, `recovery`, `before_after`, `milestone`, and `demo` events and store them directly in the session's `assets/`. Do not create a candidates workflow or interrupt the work for per-image approval. Content production still requires an explicit request, and the finished video or article is the human visual-review gate. Story splitting or merging, people, clients, brand, commercial CTA, registry publication facts, and real publication remain human-controlled.

## Stage-aware workflow

1. Read `references/privacy.md` before the first capture in a repository.
2. Run `scripts/haostory.py setup` when the project has no `.haostory.json`. This does not enable capture. Run `enable` only after the user opts in for this named project.
3. Model work as Project → Initiative → Phase → Capture Window → Event. Phases are `discovery`, `design`, `build`, `validate`, `release`, and `operate`.
4. Before meaningful work, run `suggest-start` in assisted-auto mode or explicit `start` in manual mode. If capture starts, tell the user in commentary: “HaoStory 已为 `<initiative>/<phase>` 开始本地记录”. Never start silently.
5. Run `remember` only for a high-confidence observable event: `decision`, `scope_change`, `failure`, `recovery`, `before_after`, `milestone`, `demo`, `metric`, or redacted `external_signal`. Generate a stable `novelty_key`; repeated `event type + novelty_key` attempts fold into one event. Prefer one result, one changed judgment, and one or two pieces of proof over a complete chronology. When the event has useful visual proof, wait for the page or app to stabilize, save the screenshot locally, and attach it with `remember --asset` so it goes directly into `assets/`.
6. Use `pause` while waiting or excluding a section, `resume` when the same goal and acceptance criteria continue, and `close-phase` when the phase result is known or a handoff enters review. Closing writes a private `stage-brief.md`, audits the session, reports its asset location, and asks whether to produce video, article, both, archive, or prepare a reviewed project-history package. It does not export, render, commit, push, upload, publish, or update published-story memory.
7. If the user has reviewed the whole phase and wants its materials available with the project, run `share-stage --confirmed`. This copies only the concise brief and selected assets into the configured project-relative history directory. It never runs Git or a network operation.
8. Do not produce content until the user explicitly asks. Then run `registry check`, `story-plan`, `audit`, and explicit `export` before editorial or rendering work. A repeated claim without new evidence routes to archive.
9. Improve generated drafts using the evidence package. Rewrite or translate each requested language naturally; do not leave untranslated source text in the other language. Do not invent events, metrics, quotes, or results.
10. Ask for human approval before publishing, registering a story as published, committing or uploading a project-history package, or copying raw evidence into a public repository.

Read `references/project-integration.md` when the user wants HaoStory applied automatically across future sessions in a project.

## Assisted-auto start rules

Start or resume automatically only when all are true:

- `.haostory.json` has `capture.mode: assisted-auto`, set by explicit project opt-in;
- the task is development, a product experiment, content production, or research;
- it has a stage goal, artifact, or acceptance criteria;
- no active window covers the same `project + initiative + phase`;
- the work is outside sensitive or user-excluded scope.

Do not auto-start for formatting, dependency installation, a simple bug fix, consulting answers, mechanical renames, or packaging without an independent result. Do not checkpoint every command, file save, repeated error, wording change, background restatement, or ordinary passing test.

If an event could materially improve the later story but its privacy, relevance, or preferred image is genuinely ambiguous, ask one short question with the smallest useful choice. Otherwise use judgment and continue. Do not ask about routine events or each image.

Open a new phase when success criteria, target users, product position, release/operation state, or the audience's story question changes. Otherwise pause or resume the existing phase. Build asks how an idea became runnable; validate asks whether it works and where its limits are. Inherited context must remain minimal.

## Visual evidence capture

Capture only a few images that materially support the story: a meaningful before/after, a visible failure, the recovered state, the first stable demo, or a completed milestone. Use the current task's browser/app capture capability; HaoStory itself is not a background screen recorder.

Before saving, wait for loading, transitions, and entrance animations to finish. Reject and recapture transparent first frames, spinners, blank states, clipped layouts, or images that do not show the claimed result. Capture desktop and mobile views only when each proves something useful. Save directly with `remember --asset`; do not create `candidates/`, thumbnails, or approval queues.

## Session and path routing

Omit `--session` only when exactly one active or paused capture window exists. If multiple windows are active or paused, stop and ask the user to choose from the CLI's listed candidates; never infer from directory names. With no active window, V1 compatibility selects the manifest with the latest `updated_at`.

Treat ordinary `--session` values as direct child names under the current project's `.haostory/`. Do not pass absolute paths, `..`, separators, or symlinks. Keep `story_memory.registry` inside that same `.haostory/` directory.

## Commands

From the target project root:

```bash
python3 <skill>/scripts/haostory.py setup
python3 <skill>/scripts/haostory.py enable --history-dir docs/project-history
python3 <skill>/scripts/haostory.py suggest-start --title "Stage goal" --initiative capture-v2 --phase build
python3 <skill>/scripts/haostory.py start --title "Task title" --summary "Why it matters" --type product
python3 <skill>/scripts/haostory.py checkpoint --stage decision --notes "What changed" --decision "Why"
python3 <skill>/scripts/haostory.py checkpoint --stage tests --notes "What was verified" --run npm test
python3 <skill>/scripts/haostory.py remember --event demo --notes "Stable result" --novelty-key first-demo --asset /tmp/stable-demo.png
python3 <skill>/scripts/haostory.py pause --reason "This section is excluded"
python3 <skill>/scripts/haostory.py resume
python3 <skill>/scripts/haostory.py close-phase --result "What is now known" --handoff
python3 <skill>/scripts/haostory.py share-stage --confirmed
python3 <skill>/scripts/haostory.py disable
python3 <skill>/scripts/haostory.py archive-only --reason "The user said this must not be public"
python3 <skill>/scripts/haostory.py registry do-not-repeat --text "Background that must not be repeated"
python3 <skill>/scripts/haostory.py registry check
python3 <skill>/scripts/haostory.py story-plan
python3 <skill>/scripts/haostory.py finish --outcome "What happened" --lesson "What changed in our understanding"
python3 <skill>/scripts/haostory.py audit
python3 <skill>/scripts/haostory.py export
python3 <skill>/scripts/haostory.py registry publish --story story-id --channel channel-name --confirmed
```

Use `--asset path/to/file` for task-relevant visual evidence captured by the Agent or explicitly provided by the user. The CLI copies it directly into the session and prevents filename collisions. Treat screenshots as potentially sensitive even when the text audit passes; never capture prohibited contexts listed in `references/privacy.md`.

## Output policy

Keep raw evidence local under ignored `.haostory/`. A confirmed project-history package contains only a concise Markdown brief and selected images under the configured project-relative directory, so it can be reviewed and later included in ordinary version control. Preparing it is not approval to commit, push, upload, publish, or produce final content. Read `references/output-schema.md` when changing either layer.

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
| “这个项目开始用 HaoStory” | `enable` for the named project, then announce the local opt-in |
| “从这里开始记录” | `start` the current phase |
| “这是上一阶段的继续” | start/resume with the same initiative and inherited context |
| “这段别记” | `pause` and retain the exclusion reason |
| “这个失败留一下” | `remember --event failure --force` |
| “这个可以单独做一期” | mark a standalone candidate for human review |
| “前面不用再讲了” | `registry do-not-repeat --text "..."` |
| “到这里先结束” | `close-phase`, then report assets and ask whether to produce content |
| “把这阶段材料放到项目里” | after phase-level review, `share-stage --confirmed` |
| “把这阶段整理成视频和文章” | `registry check`, `story-plan`, `audit`, then explicit `export` |
| “这两个阶段合成一篇” | create a human-approved combined plan without changing source evidence |
| “这次不要公开” | `archive-only --reason "..."` |
| “这个项目先别记录了” | `disable` without deleting prior records |

## Brand and commercial boundary

Keep public defaults neutral. Apply the user's brand only from `.haostory.json`. Read `references/brand-and-commercial.md` before adding attribution, calls to action, sponsor language, or commercial availability.

## Privacy boundary

Never capture `.env` files, credentials, cookies, private keys, browser profiles, production user data, private conversations, or unrelated screens. The text sanitizer reduces risk but does not inspect image pixels. If the privacy report contains a high-severity finding, do not recommend production or publication. Review the finished content before release.
