# Security Policy

## Supported Versions

This project is maintained as a local/offline desktop + mobile tool.
Security updates are applied to the latest release on `main`; older releases
are not actively patched.

## Reporting a Vulnerability

Please do **not** open a public issue for security problems.

If you find a vulnerability related to:

- secrets or personal data leaking into the repository,
- dependency or supply-chain issues,
- unsafe handling of untrusted input in the web/desktop UI,

report it privately through GitHub's **Private vulnerability reporting** on
this repository. If that is not available, open a normal issue with a minimal
reproduction and label it `security`; avoid including real credentials or
other sensitive data in the issue body.

## Project Privacy Note

This project is designed to run fully locally and does not call remote AI or
data APIs at runtime. Contributions should not add telemetry, external font
loads, analytics, or hidden network calls unless clearly documented and
opt-in.
