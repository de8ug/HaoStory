# Output package

## Studio jobs

Studio production requests are private handoff records:

```text
.haostory/studio/jobs/<job-id>/request.json
```

The `haostory/studio-job/v1` request contains the selected project-relative paths, selected host conversation references, requested formats, chosen angle, audience, goal, supplements, status, and explicit false publication/upload authorization. It never contains console sponsor copy or automatically retrieved conversation bodies.

The invoking agent may open only the selected paths and retrieve only the selected conversation references. `studio-job complete` records project-relative generated outputs after they exist. It does not publish, upload, commit, or push them.

Each task creates a local package:

```text
.haostory/YYYY-MM-DD-task-slug/
├── manifest.json
├── timeline.md
├── stage-brief.md
├── evidence/
│   ├── start/
│   ├── checkpoints/
│   └── finish/
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
.haostory/story-registry.json
```

New projects start with capture off. `.haostory/` is the private working layer and remains ignored by Git.

## Manifest

- `schema`: `haostory/v1`
- `title`, `summary`, `type`
- `project`: public-safe project name, never an absolute repository path
- `started_at`, `updated_at`, `finished_at`
- `outcome`, `lesson`
- `stages`: ordered task events
- `assets`: paths relative to the session
- `commands`: redacted command names, exit codes and relative output paths
- `story_score`: deterministic editorial signal, not a performance prediction

V2 keeps `schema: haostory/v1` and adds optional, backward-compatible fields:

- `initiative` and `phase` identify the stage goal;
- `capture_window` stores mode, active/paused/closed status, pause history, and close reason;
- `events` stores observable high-confidence events, stable `novelty_key` values, occurrence counts, claims, and evidence refs;
- event-level `data_kind` labels screenshots as `real`, `demo`, `mixed`, or the legacy/default `unspecified`;
- `necessary_context` links a new phase to a minimal public-safe summary of the prior phase.
- `archive_only`, `archive_only_reason`, and `archive_only_at` record an explicit human decision to suppress publication recommendations.
- event-level `assets` and manifest-level `assets` contain direct, session-relative visual evidence paths; repeated filenames receive collision-safe suffixes.
- `content_readiness` records counts, the relative `assets/` location, privacy state, recommended route, available production choices, and the fact that production still requires an explicit request.
- `next_steps` stores the concise unfinished items supplied with `close-phase --todo`.
- `project_history` is added only after `share-stage --confirmed`; it records the progress file, dated screenshot directory, and explicitly keeps commit/upload flags false.

V1 readers may ignore these fields. V2 commands continue to read manifests that do not contain them; `checkpoint`, `finish`, `audit`, and `export` do not require migration. For an old manifest, story planning may use its lesson/outcome as a claim and its selected command or asset references as evidence.

## Story registry

`.haostory/story-registry.json` is local project memory, not a publishing connector:

```json
{
  "schema": "haostory/story-registry/v1",
  "project": "project-name",
  "published_stories": [
    {
      "story_id": "positioning-v1",
      "phase": "design",
      "published_at": "2026-08-15",
      "channels": ["wechat"],
      "claims": ["The product is personally curated."],
      "evidence_refs": ["decision:positioning"],
      "next_open_questions": [],
      "source_session": "positioning-first"
    }
  ],
  "do_not_repeat": []
}
```

`registry do-not-repeat --text "..."` adds reviewed background without direct JSON editing. `registry check` classifies `new_claims`, `new_evidence`, `necessary_context`, and `repeated_claims`. `registry publish` only records a publication that a human has already confirmed; it never contacts a platform. The configured registry path must resolve inside the project's non-symlinked `.haostory/` directory.

## Public export

`content-package.json` adds `novelty`, `story_plan`, and `publication_recommendation`. A high-severity privacy finding sets the recommendation to `blocked_privacy`; a repeated claim without new evidence routes to `archive`.

`close-phase` may create or refresh `privacy-report.json` and `content_readiness`, but it does not create `exports/`. The CLI response expands the relative asset location into a local path so the user knows where the accumulated screenshots live.

It also writes a short private `stage-brief.md`. This brief is writing material, not a finished article, and remains under `.haostory/` until the user reviews the whole phase.

## Reviewed project record

After a closed phase and a successful privacy audit, `share-stage --confirmed` may prepare:

```text
docs/
├── progress.md
└── screenshots/YYYY-MM-DD/
    ├── README.md
    └── <up to three selected images>
```

`progress.md` contains one marker-delimited block per session, so rerunning the command replaces that block instead of duplicating it. It keeps the user problem, result, reason for the adjustment, completed work, TODOs, screenshot links, and README check. The dated screenshot index records a caption and data label for every image. If more than three screenshots exist, the caller must select up to three with repeatable `--asset`. A legacy or unlabelled image requires one `--data-kind real|demo|mixed` fallback.

These files contain no raw Git patches, terminal dumps, registry, hidden reasoning, or full timeline. Both configurable destinations must remain inside the project and outside `.git/` and `.haostory/`.

`share-stage` returns the generated files as `commit_scope` and checks whether a software README appears to include a startup command and runtime URL. It does not edit the README, stage, commit, push, upload, render, or publish anything. A later version-control or publication action requires a separate user request.

For backward compatibility, `privacy-report.json` retains `manual_asset_review_required`. V2.1 also writes `asset_review_gate: final_content` and `visual_review_at_content_gate: true` when images exist; this means the finished video or article is reviewed, not that every captured image needs pre-approval.

Only copy files under `exports/` into a public example after review. Raw evidence remains local unless the user explicitly selects individual files and passes the release gate.
