# HaoStory

**Build it once. Tell it well.**

HaoStory is a local-first, bilingual Agent Skill that turns real development and experiments into evidence-backed articles, video scripts, social posts, and build logs.

> Created by [Howie Wang](https://howie.wang/) · 浩哥 AI 实验室

[中文说明](README.zh-CN.md)

## Why HaoStory

Most project stories are reconstructed after the work is done. The useful details are already gone: the failed attempt, the decision that changed, the test output, and the before/after proof.

HaoStory captures those moments while the work is happening, then creates an editable bilingual output structure. The CLI does not call an AI service; the agent using the Skill rewrites or translates each language from the evidence. Nothing is uploaded or published automatically.

## What it captures

- task intent and outcome;
- privacy-redacted Git status and diffs;
- decisions and lessons at meaningful checkpoints;
- selected command output and visual evidence;
- a story-value score that helps decide whether to publish.

## Outputs

```text
.haostory/YYYY-MM-DD-task/
├── manifest.json
├── timeline.md
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
```

## Quick start

Copy `skill/haostory` into the skills directory used by your agent, or ask the agent to read this repository's `SKILL.md`.

```bash
python3 skill/haostory/scripts/haostory.py setup
python3 skill/haostory/scripts/haostory.py start \
  --title "Build the first homepage" \
  --summary "Test a new product direction" \
  --type product
python3 skill/haostory/scripts/haostory.py checkpoint \
  --stage decision \
  --notes "Changed the homepage from a tool directory to a problem navigator" \
  --decision "Lead with user problems, not AI brands"
python3 skill/haostory/scripts/haostory.py finish \
  --outcome "The homepage shipped and passed its tests" \
  --lesson "Positioning decisions are part of the product"
python3 skill/haostory/scripts/haostory.py export
```

HaoStory never makes captured material public automatically. Review the privacy report and every image before sharing.

## Open core

The core workflow is open source under the MIT License. Private integrations, tailored workflows, and implementation partnerships may be offered separately. See [howie.wang](https://howie.wang/) for current projects and contact options.

## Follow the experiments

HaoStory is being developed in public through real projects, beginning with UP2U, a personally curated AI problem and experiment navigator.

微信公众号：浩哥 AI 实验室

<img src="https://howie.wang/haoQR.jpg" alt="浩哥 AI 实验室微信公众号" width="180" />
