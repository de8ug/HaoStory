# Project integration

Installing a global Skill makes HaoStory available, but does not guarantee that every unrelated session will invoke it. Add a short instruction to the target repository's `AGENTS.md` or equivalent project instruction file:

```markdown
## HaoStory

For meaningful development, product, content, or research work, use the `haostory` Skill in the mode configured by `.haostory.json`. In assisted-auto mode, announce every local start/resume/pause/close, capture only high-confidence observable events, keep visual assets human-selected, check story memory before export, and keep `.haostory/` local unless reviewed for publication.
```

Keep the instruction short. Do not duplicate the full Skill inside every project.

## Stage routing

Pass a stable initiative ID and one of `discovery`, `design`, `build`, `validate`, `release`, or `operate`. Resume when the goal and acceptance criteria are unchanged. Start a new phase when the success criteria, target user, positioning, release state, or audience question changes.

Use `suggest-start --work-kind formatting|dependency|simple-fix|consulting|rename` for deterministic exclusions. The command returns JSON and does not start a capture for those routine tasks. In `manual` mode it only suggests a start; in `off` mode it ignores the task.

Pass `--session` whenever more than one active or paused window exists. Never select a window by directory order. Session IDs are direct child names, and both sessions and the story registry must remain inside the project's non-symlinked `.haostory/` directory.

No integration may read hidden reasoning, run as a background recorder, scan a screen, copy visual assets, inspect private chats, or publish automatically.
