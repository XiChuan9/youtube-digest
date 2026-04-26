# Security Policy

## Supported Versions

This project is pre-1.0. Security fixes target the current `main` branch until
versioned releases are established.

## Reporting a Vulnerability

Please report vulnerabilities privately when possible through GitHub Security
Advisories. If private reporting is not available, open a GitHub issue with a
minimal description and avoid posting secrets, exploit payloads, API keys, or
private transcript data.

Useful reports include:

- Affected version or commit.
- Steps to reproduce.
- Impact and likely severity.
- Whether external services, local files, generated artifacts, or secrets are
  involved.

## Secret Handling

Never include API keys in issues, pull requests, logs, screenshots, artifacts, or
test fixtures. `.env`, `config.json`, `artifacts/`, `newsletters/`, `logs/`, and
SQLite databases should remain local and ignored by git.

## Generated Content and Data

Transcripts and generated articles may contain copyrighted or sensitive material
from source videos. Treat `artifacts/` and `newsletters/` as private by default,
especially on shared machines and VPS deployments.
