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

## Public export

Only copy files under `exports/` into a public example after review. Raw evidence remains local unless the user explicitly selects individual files and passes the release gate.

