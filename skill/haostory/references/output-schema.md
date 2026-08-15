# Output package

Each task creates a local package:

```text
.haostory/YYYY-MM-DD-task-slug/
├── manifest.json
├── timeline.md
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
- `necessary_context` links a new phase to a minimal public-safe summary of the prior phase.
- `archive_only`, `archive_only_reason`, and `archive_only_at` record an explicit human decision to suppress publication recommendations.

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

Only copy files under `exports/` into a public example after review. Raw evidence remains local unless the user explicitly selects individual files and passes the release gate.
