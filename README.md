# HaoStory Studio

> **Capture policy: paused by default.** Opening Studio is an explicit, one-time content task and reads only selected material. Ongoing stage capture starts only after Howie explicitly enables it for a named project or requests one manual capture.

**Turn your work into stories worth sharing.**

HaoStory Studio is a local-first, open-source content director invoked by AI agents. Select a few project notes, images, or recent conversations; Studio decides what can be made, what material is missing, which structure fits, and how writing, visuals, animation, voice, captions, and editing should work together. The invoking agent performs the concrete production. Studio never scans the whole project by default.

> Created by [Howie Wang](https://howie.wang/) · 浩哥 AI 实验室

[中文说明](README.zh-CN.md)

## From selected material to publishable drafts

Run HaoStory from a supported agent and it opens a polished local console:

```text
Choose notes, images, or host-provided conversations
                         ↓
Choose article, video, Xiaohongshu, or a bundle
                         ↓
Review three recommended story angles and useful material gaps
                         ↓
Optionally research current platform patterns and production tools
                         ↓
Submit one production blueprint to the invoking agent
                         ↓
Review editable local outputs
```

Studio lists safe filenames and conversation metadata first. It reads file bodies and conversation messages only after the user selects them. Recent conversations are available when the host agent exposes an appropriate API; other agents fall back to the current conversation or user-provided exports.

```bash
python3 skill/haostory/scripts/haostory.py studio
```

The official console includes a small Hao AI Lab, WeChat `HaoAILab`, and OneTake footer. It is configurable for forks and is never inserted into generated content.

HaoStory itself stays small. Platform research and tool routing are maintained as dated workflow references: official rules first, public examples as hypotheses, and GitHub repositories as candidates whose license and maintenance must be checked. Concrete production can use the host's writing, image, OneTake, Remotion, FFmpeg, transcription, voice, and editing capabilities with the user's authorization.

## Install and invoke

For a user-wide Codex installation, copy the complete skill directory to `~/.agents/skills/haostory/`. For project-only use, place it under that project's `.agents/skills/haostory/`. Start a new chat after replacing an existing version.

Invoke it explicitly with `$haostory` or choose HaoStory Studio from `/skills`. Natural-language requests can also match the skill description, for example:

> Use HaoStory to turn this project's selected notes and images into an article and short-video production plan.

Explicit invocation is the most deterministic option. Opening Studio is consent for that one content job only; it does not enable continuous capture. The full local console requires a host agent that can read approved local files and run local commands. Hosts without those capabilities can still follow the packaged content workflow, but cannot inspect a local project or open the console on their own.

The packaged archive is written to `dist/haostory.skill`. Agent platforms that accept Skill ZIP uploads may import this archive after their own compatibility and security review. Publishing it to a marketplace, charging for it, or installing it for other users is always a separate action.

## Why HaoStory Studio

Most project stories are reconstructed after the work is done. The useful details are already gone: the failed attempt, the decision that changed, the test output, and the before/after proof.

Studio can work directly from existing, user-selected material. For teams that also want to preserve evidence while work happens, the original stage-aware capture remains available as an optional, paused-by-default source. The CLI does not call an AI service. Nothing is committed, pushed, uploaded, or published automatically.

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

## Optional stage-aware capture

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

## Optional capture quick start

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

HaoStory can also be adapted for agent marketplaces such as WorkBuddy. A practical distribution model is a free open-source Studio workflow plus an optional paid expert that maintains current platform research, tailored templates, and production orchestration. Marketplace packaging, pricing, review, cloud execution, privacy terms, and payouts belong to the target platform and are not performed by this repository.

## About Howie

[Howie Wang](https://howie.wang/) / 浩哥 explores how AI can help people work, learn, create, and live better. HaoStory is one part of that ongoing practice, alongside real products, content experiments, education, and everyday problem-solving.

## Follow the experiments

HaoStory is being developed in public through real projects, beginning with UP2U, a personally curated AI problem and experiment navigator.

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
