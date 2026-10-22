# HaoStory

> **Local operating policy: paused by default.** HaoStory runs only after Howie explicitly enables it for a named project or requests one manual capture. `setup` initializes configuration but does not opt a project in.

**Build it once. Tell it well.**

HaoStory is a local-first, bilingual Agent Skill that turns real development and experiments into evidence-backed articles, video scripts, social posts, and build logs.

> Created by [Howie Wang](https://howie.wang/) · 浩哥 AI 实验室

[中文说明](README.zh-CN.md)

## Why HaoStory

Most project stories are reconstructed after the work is done. The useful details are already gone: the failed attempt, the decision that changed, the test output, and the before/after proof.

HaoStory keeps only a few decisive moments while work is happening, then prepares material for later articles or videos. The CLI does not call an AI service. Nothing is committed, pushed, uploaded, produced, or published automatically.

## Who it is for

HaoStory is not only for software development. It is for anyone doing meaningful work with an AI agent who wants to preserve the useful parts of the journey:

- independent builders and creators;
- educators, researchers, and content teams;
- product, workflow, and creative experiments;
- people turning real work, learning, or everyday problem-solving into reusable knowledge.

When code exists, HaoStory can capture Git evidence. Code is not required: decisions, drafts, tests, visuals, feedback, and before/after proof can tell the story too.

## What it captures

- stage intent and outcome;
- privacy-redacted Git status and diffs;
- decisions and lessons at meaningful checkpoints;
- selected command output and automatically preserved key visual evidence;
- a story-value score that helps decide whether to publish.

## Stage-aware capture

HaoStory V2 organizes evidence as Project → Initiative → Phase → Capture Window → Event. A phase may be one meaningful development task or a planned roadmap stage. New projects start `off`; explicit `enable` opts a named project into `assisted-auto`. The agent announces lifecycle changes, folds repeats, and normally keeps at most four distinct events per phase.

Routine formatting, dependency installation, simple fixes, consulting answers, and mechanical renames do not auto-start a story. High-confidence events include decisions, scope changes, failures, recoveries, before/after proof, milestones, demos, metrics, and redacted external signals.

Published claims are remembered in local `.haostory/story-registry.json`. Before export, HaoStory separates new claims and evidence from necessary context and repetition. A repeated claim without new evidence is routed to archive.

During assisted work, the Agent can save stable screenshots of key failures, recoveries, before/after states, milestones, and demos directly into the private session's `assets/`. There is no candidates queue or per-image confirmation. When an important choice is genuinely ambiguous, the Agent asks one focused question instead of interviewing the user repeatedly.

Closing a phase writes a small private brief and reports the material location. After one phase-level review, `share-stage --confirmed` updates one project progress log and copies at most three key screenshots into a dated folder. Each screenshot carries a short caption and a `real`, `demo`, or `mixed` data label. The command also checks whether a software project's README appears to contain a startup command and runtime URL, then reports the exact files recommended for the same commit as the code. HaoStory itself never edits the README, commits, pushes, uploads, or publishes. Final article or video production still requires a separate request.

When `--session` is omitted, HaoStory uses the only active or paused window. Multiple candidates produce an explicit error; with no active window, V1 fallback uses the newest manifest `updated_at`. Ordinary session IDs and registry paths cannot escape the project's non-symlinked `.haostory/` directory.

## Outputs

```text
.haostory/YYYY-MM-DD-task/
├── manifest.json
├── timeline.md
├── stage-brief.md
├── evidence/
├── assets/
├── privacy-report.json
└── exports/
    ├── article.zh-CN.md
    ├── article.en.md
    ├── video-script.zh-CN.md
    ├── video-script.en.md
    ├── social.zh-CN.md
    ├── social.en.md
    └── content-package.json

docs/                                         # only after share-stage --confirmed
├── progress.md                               # one deterministic block per stage
└── screenshots/YYYY-MM-DD/
    ├── README.md                             # captions and real/demo/mixed labels
    └── <up to three key screenshots>
```

## Quick start

Private raw records stay in Git-ignored `.haostory/`. After phase-level confirmation, a concise record can be prepared in `docs/progress.md` and `docs/screenshots/YYYY-MM-DD/`; committing or syncing it remains a separate user decision. Prefer committing these files with the meaningful code change they explain.

Copy `skill/haostory` into the skills directory used by your agent, or ask the agent to read this repository's `SKILL.md`.

```bash
python3 skill/haostory/scripts/haostory.py setup
python3 skill/haostory/scripts/haostory.py enable \
  --progress-file docs/progress.md \
  --screenshots-dir docs/screenshots
# Assisted-auto route (use this or the explicit start below)
python3 skill/haostory/scripts/haostory.py suggest-start \
  --title "Build stage-aware capture" \
  --initiative stage-aware-capture-v2 \
  --phase build
# Explicit/manual-compatible start
python3 skill/haostory/scripts/haostory.py start \
  --title "Build the first homepage" \
  --summary "Test a new product direction" \
  --type product
python3 skill/haostory/scripts/haostory.py checkpoint \
  --stage decision \
  --notes "Changed the homepage from a tool directory to a problem navigator" \
  --decision "Lead with user problems, not AI brands"
python3 skill/haostory/scripts/haostory.py remember \
  --event demo \
  --notes "The stable desktop result" \
  --novelty-key stable-demo \
  --asset /tmp/stable-demo.png \
  --data-kind demo
python3 skill/haostory/scripts/haostory.py pause --reason "This section is excluded"
python3 skill/haostory/scripts/haostory.py resume
python3 skill/haostory/scripts/haostory.py close-phase \
  --result "The build is ready for validation" \
  --todo "Verify the mobile flow with real data" \
  --handoff
python3 skill/haostory/scripts/haostory.py share-stage \
  --confirmed
python3 skill/haostory/scripts/haostory.py archive-only \
  --reason "The user said this must not be public"
python3 skill/haostory/scripts/haostory.py registry do-not-repeat \
  --text "Background that must not be repeated"
python3 skill/haostory/scripts/haostory.py registry check
python3 skill/haostory/scripts/haostory.py story-plan
python3 skill/haostory/scripts/haostory.py finish \
  --outcome "The homepage shipped and passed its tests" \
  --lesson "Positioning decisions are part of the product"
python3 skill/haostory/scripts/haostory.py export
python3 skill/haostory/scripts/haostory.py disable
```

HaoStory never generates content, changes Git history, uploads files, or publishes merely because a phase closed. Review the privacy report, the phase package, and any finished video or article before the next action.

### V1 compatibility

Existing `haostory/v1` manifests and the `start`, `checkpoint`, `finish`, `audit`, and `export` commands continue to work. V2 adds optional fields and a local registry; no destructive migration is required.

## Open core

The core workflow is open source under the MIT License. Private integrations, tailored workflows, and implementation partnerships may be offered separately. See [howie.wang](https://howie.wang/) for current projects and contact options.

## About Howie

[Howie Wang](https://howie.wang/) / 浩哥 explores how AI can help people work, learn, create, and live better. HaoStory is one part of that ongoing practice, alongside real products, content experiments, education, and everyday problem-solving.

## Follow the experiments

HaoStory is being developed in public through real projects, beginning with UP2U, a personally curated AI problem and experiment navigator.

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
