# Privacy and release safety

## Before capture

- Confirm the repository is the intended project.
- Keep `.haostory/` ignored by Git.
- Do not point `--asset` at a full desktop screenshot, private chat, analytics page with user data, browser profile, or credential screen.
- Do not run commands that print the environment, authentication state, remote URLs with credentials, or secret-manager output.
- Keep ordinary `--session` IDs and the configured story registry inside the current project's real, non-symlinked `.haostory/` directory.

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
