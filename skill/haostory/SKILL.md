---
name: haostory
description: Open HaoStory Studio to turn user-selected project notes, images, or host-provided conversations into articles, video plans, and Xiaohongshu posts. Also supports optional, explicitly enabled project-stage capture. Use when the user wants to discover, organize, or produce shareable content from real work without scanning the whole project.
---

# HaoStory Studio

跟浩哥一起，用 AI 讲好自己的故事。

HaoStory Studio is a local, open-source content workspace used by an AI agent. Its default job is to help the user select a small amount of existing material, find a useful story angle, and generate editable content. Continuous project capture is optional and paused by default.

## Choose the mode

Use **Studio mode** when the user wants an article, video, Xiaohongshu post, content angle, or a review of existing project material.

Use **capture mode** only when the user explicitly enables HaoStory for a named project or asks to preserve a specific stage while work is happening. Do not start capture merely because another project is being developed.

## Studio workflow

1. Confirm the intended current project. Read [references/privacy.md](references/privacy.md).
2. Detect host capability without reading private content. Always offer safe material from the current workspace. When the host exposes project or recent-conversation tools, retrieve titles and identifiers only; otherwise use the current conversation or a user-provided export.
3. If recent conversations are available, write a temporary host-context JSON containing only `host`, `id`, `title`, `project`, and `updated_at`. Never put message bodies in this file.
4. Note the current latest job ID, then launch the local console:

   ```bash
   python3 <skill>/scripts/haostory.py studio [--host-context /tmp/haostory-host-context.json]
   ```

   Keep the managed process running and show the returned local URL when the host cannot open it automatically.
5. Tell the user that Studio lists names and metadata first; file bodies and conversation messages are read only after selection.
6. Wait for a newly submitted request:

   ```bash
   python3 <skill>/scripts/haostory.py studio-job wait --after <previous-job-id>
   ```

7. Read the returned request. Open only `selected_paths`. For each `conversation_ref`, use the host's conversation-reading tool only now, after selection. Do not expand to adjacent chats, full project trees, hidden folders, or source code unless the user separately asks.
8. Read [references/content-studio.md](references/content-studio.md) and first design the material plan, narrative, production modules, tool routing, and review gates. When `research_current_examples` is true, also read [references/platform-research.md](references/platform-research.md) and research current public rules, representative works, and maintained tools without exposing private material. Then use the invoking agent's available capabilities to produce the requested formats. Ask at most one focused question when a missing fact would materially change the result; otherwise generate with current material.
9. Save editable outputs in the project or user-approved destination, then register them:

   ```bash
   python3 <skill>/scripts/haostory.py studio-job complete --job <id> --output <project-relative-file>
   ```

10. Report outputs for review. Never publish, upload, commit, push, or register a story as published without a separate request.

## Studio privacy rules

- The source list is metadata-only. Selection is consent to read those items for the current production job, not blanket access to the project.
- Never recursively read the entire repository, image library, or conversation history.
- Default local candidates are README files, explanatory Markdown/text under documentation folders, and common images under documentation/media folders.
- Exclude source trees, dependencies, hidden folders, `.git`, private `.haostory` captures, credentials, browser data, personal photos, private messages, and unrelated third-party material.
- The official console may show Hao AI Lab, WeChat `HaoAILab`, and OneTake notices. These console notices must never enter job payloads or generated content. Forks may disable or replace them.
- Opening Studio is an explicit content-production action. It does not enable future capture.

## Content outcomes

Studio supports articles and case studies; short-video hooks, scripts, storyboards, animation/audio/caption plans; Xiaohongshu cover copy, carousel structure, body copy, and posting notes; and multi-format bundles grounded in one evidence brief. HaoStory is the director and workflow layer: concrete design, rendering, narration, editing, and export are handed to the invoking agent and the tools it can use.

Prefer a specific result, changed judgment, visible before/after, or useful failure over a smooth activity log. Never invent events, metrics, quotes, people, or outcomes. Read [references/content-studio.md](references/content-studio.md) for the maintained templates and production contract.

## Optional capture mode

`setup` initializes capture as `off`. `enable` is the explicit project-level opt-in; `disable` pauses future capture without deleting history. An explicit `start` may create one manual session while the project remains off.

When enabled, model work as Project → Initiative → Phase → Capture Window → Event. Keep at most four distinct, high-confidence events per phase and fold retries. Useful events are decisions, scope changes, meaningful failures and recoveries, before/after proof, milestones, demos, metrics, and redacted external signals.

```bash
python3 <skill>/scripts/haostory.py setup
python3 <skill>/scripts/haostory.py enable --progress-file docs/progress.md --screenshots-dir docs/screenshots
python3 <skill>/scripts/haostory.py suggest-start --title "Stage goal" --initiative project-v1 --phase build
python3 <skill>/scripts/haostory.py remember --event demo --notes "Stable result" --novelty-key first-demo --asset /tmp/demo.png --data-kind demo
python3 <skill>/scripts/haostory.py close-phase --result "What is now known" --todo "What remains" --handoff
python3 <skill>/scripts/haostory.py share-stage --confirmed
python3 <skill>/scripts/haostory.py disable
```

Capture stable visual proof directly into private session assets; do not create candidate queues or ask about every image. `share-stage` may update `docs/progress.md` and copy at most three reviewed screenshots to `docs/screenshots/YYYY-MM-DD/`, but it never runs Git or a network operation. Read [references/project-integration.md](references/project-integration.md) before adding future-session project instructions and [references/output-schema.md](references/output-schema.md) before changing compatibility behavior.

## Publication and brand boundary

Generated work is a draft until the user reviews it. Keep claims factual and language natural in every requested language. Apply the user's own brand only from approved configuration or explicit direction. Read [references/brand-and-commercial.md](references/brand-and-commercial.md) before adding attribution, calls to action, sponsor language, or commercial availability.

Old `haostory/v1` manifests and `start`, `checkpoint`, `finish`, `audit`, and `export` remain supported. The local story registry is publication memory, not permission to publish.
