# HaoStory Studio Design

## Product position

**Official name:** HaoStory Studio

**Slogan:** 跟浩哥一起，用 AI 讲好自己的故事。

**Promise:** Turn selected project notes, conversations, and images into articles, video plans, and Xiaohongshu posts without scanning the whole project.

HaoStory Studio is a lightweight, open-source content director invoked by an AI agent. Its primary job is to decide what story can be made, what material it needs, which platform structure and production modules fit, and which available tools should execute each step. Writing, design, animation, voice, editing, and export are handed back to the invoking agent. Existing stage capture remains an optional material source.

## Primary flow

1. The agent launches a local Studio page for the current project.
2. The page lists safe candidate material by filename and metadata only.
3. The user explicitly selects project notes, images, imported files, or host-provided conversation references.
4. The user chooses article, video, Xiaohongshu, or a multi-format bundle.
5. Studio reads only the selected local files, identifies story signals, and recommends three suitable angles.
6. Studio reports only material gaps that would materially improve the requested output.
7. The user submits a production request to the invoking agent.
8. When authorized, the agent researches current public platform rules, representative works, and maintained tools without exposing private project material.
9. The agent creates a production blueprint covering materials, script, visuals, animation, voice, captions, editing, tools, and review gates.
10. The invoking agent executes the blueprint with the capabilities available in its environment and reports editable outputs.

## Architecture

### Portable core

- Python standard-library HTTP server bound to `127.0.0.1`.
- Static HTML, CSS, and JavaScript with no network dependency.
- Safe source discovery, selected-file preview, deterministic material analysis, template catalog, and local job queue.
- Project-local private state under ignored `.haostory/studio/`.

### Host adapters

The Skill detects rather than assumes host capability.

- `current_workspace`: always available when the agent has a project directory.
- `recent_conversations`: supplied by hosts such as Codex when list/read conversation tools exist.
- `current_conversation`: supplied by the invoking agent when appropriate.
- `manual_import`: fallback for text, Markdown, and images.

The initial source list may contain project and conversation titles, but conversation bodies are retrieved only after the user selects them. A generic Skill cannot promise access to private chat history on hosts that expose no conversation API.

### Research and tool routing

Platform guidance lives in dated references rather than UI code. Stable rules come from official platform guidance; current patterns come from a small, diverse sample of public works and are labelled as hypotheses. GitHub is used to discover maintained open-source production tools and Agent Skills. Studio recommends a tool class and reason, then lets the invoking agent choose an installed or user-approved implementation. It never installs tools or sends project material to a service by itself.

## Privacy model

- Never recursively read the whole project.
- Discovery inspects names, type, and size only.
- Default candidates are top-level explanatory Markdown/text, README files, documentation folders, HaoStory project records, and common images in documentation/media folders.
- Exclude source trees, hidden folders, dependencies, `.git`, private `.haostory` captures, credentials, personal photos, and known secret paths.
- Reading begins only after explicit file selection.
- Limit text bytes, image count, and request size.
- All generated artifacts stay local until separately reviewed.

## Content modes

- Article: case study, decision story, failure/recovery, tutorial, project retrospective.
- Video: 60-second story, three-minute case study, screen walkthrough, talking-head plus evidence.
- Xiaohongshu: experience post, before/after carousel, step-by-step cards, lessons and pitfalls.
- Bundle: one shared evidence brief adapted into multiple formats rather than duplicated verbatim.

Each recommendation includes fit, reason, evidence already present, and the smallest useful supplement. Users can always choose “generate with current material”.

## Visual direction

An editorial workshop rather than a generic AI dashboard: warm paper, dark ink, vermilion accents, serif display type, precise grid, generous whitespace, and restrained motion. The four-step canvas is Material → Format → Angle → Produce. It must work on desktop and mobile and meet keyboard, contrast, and reduced-motion expectations.

## Official console branding

The official footer may show:

- 浩哥 AI 实验室；
- 微信 `HaoAILab`，共同玩转 AI；
- OneTake as an optional next step for turning a script into a video.

These notices appear only in the Studio console. They never enter user articles, scripts, Xiaohongshu copy, job payloads, or exported content. Forks can disable or replace the sponsor block through local configuration.

## MVP success criteria

- `haostory.py studio` opens a polished local console without enabling capture.
- Only safe metadata is listed before selection.
- Analysis reads only selected files and returns three useful angles plus concise gaps.
- A production request is saved deterministically and can be read by the invoking agent.
- The UI states clearly which materials will be read.
- No network request, publication, upload, commit, or push occurs.
- Existing capture and export commands remain compatible.
