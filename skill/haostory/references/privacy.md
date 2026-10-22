# Privacy and release safety

## Before capture

- Confirm the repository is the intended project.
- Confirm the user explicitly enabled HaoStory for this named project, or explicitly requested this one manual session. `setup` alone is not consent to capture.
- Keep `.haostory/` ignored by Git.
- Do not point `--asset` at a full desktop screenshot, private chat, analytics page with user data, browser profile, or credential screen.
- Do not run commands that print the environment, authentication state, remote URLs with credentials, or secret-manager output.
- Keep ordinary `--session` IDs and the configured story registry inside the current project's real, non-symlinked `.haostory/` directory.

## Assisted visual capture

- Capture only the current task's meaningful visual state at `failure`, `recovery`, `before_after`, `milestone`, or `demo` events.
- Wait for loading and entrance animations to settle. Recapture transparent, blank, clipped, or spinner frames instead of storing them.
- Store valid screenshots directly with `remember --asset`; do not create candidate queues or require per-image confirmation.
- Label each saved visual as `real`, `demo`, or `mixed`; do not infer the classification from appearance.
- Never capture private chats, credential or account screens, browser profiles, production user data, unrelated windows, or full-desktop views that expose other applications.
- Local asset capture does not authorize content production or publication. Review generated content before release.

## Project-record gate

- Treat `.haostory/` as private working material.
- Ask for one phase-level confirmation before `share-stage`; do not ask for every ordinary image.
- `--confirmed` means the user reviewed the phase for placement in the local project record. It does not authorize a Git commit, push, upload, publication, or reuse in another project.
- The text audit cannot inspect image pixels. Before confirmation, inspect selected screenshots for credentials, children or third parties, private messages, account details, server addresses, unpublished business data, and unrelated windows.
- Keep the project record concise: one progress block and no more than three images needed to support it. Do not include private photos, credentials, household storage, identifiable third parties, or unrelated project details.

## Explicit external audit/export paths

The optional positional path accepted by `audit` and `export` is a separate, human-authorized compatibility mechanism for reviewing an existing session directory. Use it only when the user explicitly selected that directory. It does not relax ordinary `--session` or registry containment, and it must never be inferred from project data.

## Files never to read

Skip files whose name or path contains:

```text
.env
credentials
credential
secrets
secret
id_rsa
id_ed25519
.pem
.p12
.key
cookies
browser profile
```

## Sanitization

The CLI replaces common instances of:

- the current home directory;
- URLs containing `username:password@host`;
- API keys, access tokens, bearer tokens, JWTs and private-key blocks;
- email addresses, likely phone numbers, and non-local IPv4 addresses.

Sanitization is best-effort. A secret may use an unknown format, appear inside an image, or be inferable from context.

## Release gate

Before publishing:

1. Run `haostory.py audit`.
2. Open `privacy-report.json`.
3. Manually inspect every asset.
4. Search the public repository and its Git history for personal paths and secret patterns.
5. Use a clean repository history for the first public release.
6. Rotate any credential that has appeared in a terminal, diff, screenshot, Git remote, or earlier commit.
