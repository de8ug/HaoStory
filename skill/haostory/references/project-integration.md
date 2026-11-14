# Project integration

Installing a global Skill only makes HaoStory Studio available. The user may explicitly open Studio for a one-time content job; this does not authorize ongoing capture. Capture must remain paused until the user explicitly enables it for a named project. Run `setup`, then `enable --progress-file docs/progress.md --screenshots-dir docs/screenshots` only after that capture opt-in. Add a short instruction to the target repository's `AGENTS.md` or equivalent project instruction file:

```markdown
## HaoStory

HaoStory is opt-in and follows `.haostory.json`. When enabled, announce lifecycle changes, keep at most a few decisive events per phase, save stable key screenshots directly into private session assets, and ask only when an important capture choice is genuinely ambiguous. `close-phase` creates a private brief. Use `share-stage --confirmed` only after phase-level review to update `docs/progress.md` and at most three dated screenshots. Never commit, push, upload, produce final content, or publish without a separate request.
```

Keep the instruction short. Do not duplicate the full Skill inside every project.

## Stage routing

Pass a stable initiative ID and one of `discovery`, `design`, `build`, `validate`, `release`, or `operate`. Resume when the goal and acceptance criteria are unchanged. Start a new phase when the success criteria, target user, positioning, release state, or audience question changes.

Use `suggest-start --work-kind formatting|dependency|simple-fix|consulting|rename` for deterministic exclusions. The command returns JSON and does not start a capture for those routine tasks. In `manual` mode it only suggests a start; in `off` mode it ignores the task.

The default event budget is four distinct events per phase. Repeated `event type + novelty_key` values fold into one event. When the budget is full, `remember` returns `event_budget_reached`; use `--force` only for an exceptional moment that would materially change the later story. If importance is uncertain, ask one focused question rather than starting a broader interview.

Pass `--session` whenever more than one active or paused window exists. Never select a window by directory order. Session IDs are direct child names, and both sessions and the story registry must remain inside the project's non-symlinked `.haostory/` directory.

Private raw capture stays under ignored `.haostory/`. A confirmed stage record updates `project_history.progress_file` and `project_history.screenshots_directory`, which must be non-symlinked paths inside the project and outside `.git/` and `.haostory/`. Record each screenshot's caption and whether it uses real, demo, or mixed data. This makes it possible for the user's ordinary version-control workflow to sync reviewed materials across devices with the related code, but HaoStory itself never stages, commits, pushes, uploads, or publishes them.

No integration may read hidden reasoning, run as a background recorder, inspect unrelated screens or private chats, generate content before the user asks, or publish automatically. Targeted screenshots of the current task are allowed only at meaningful visual events and must follow `privacy.md`.
