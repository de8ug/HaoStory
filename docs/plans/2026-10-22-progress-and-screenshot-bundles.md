# Lightweight Progress and Screenshot Bundles

## Goal

Replace the nested project-history package with a small, project-native record that is useful for later articles and videos without turning HaoStory into a continuous logger.

## Product rules

- HaoStory remains paused by default and runs only after explicit opt-in for a named project.
- Capture only meaningful feature work, visible redesigns, and real problem resolutions.
- Keep private raw material in `.haostory/`; prepare project-visible files only after phase review.
- Never commit, push, upload, publish, or edit the project's README automatically.
- Exclude credentials, private photos, household storage, private repository details, and identifiable third-party material.

## Project-visible output

- Append or update one deterministic stage block in `docs/progress.md`.
- Copy at most three reviewed screenshots to `docs/screenshots/YYYY-MM-DD/`.
- Maintain a small dated screenshot index containing a caption and `real`, `demo`, or `mixed` data label.
- Report whether the project README appears to include a startup command and a runtime URL.
- Return the generated file list as the recommended commit scope so screenshots can travel with the corresponding code change.

## CLI changes

- `enable` accepts explicit progress-file and screenshots-directory paths; the old history directory remains a compatibility shortcut.
- `remember` records the data classification associated with captured visuals.
- `close-phase` accepts repeatable next steps.
- `share-stage` accepts an optional fallback data classification and repeatable asset selections.
- If a phase contains more than three screenshots, require an explicit selection rather than guessing.
- If a selected screenshot has no data classification, require one focused answer rather than inventing it.

## Verification

- Add tests for path containment, data classification, three-image limit, deterministic reruns, progress content, screenshot captions, README checks, and zero Git/network side effects.
- Run the complete unit-test suite.
- Run the Codex Skill validator.
- Review the final diff, commit HaoStory itself, and push only the HaoStory commit requested by the user.
