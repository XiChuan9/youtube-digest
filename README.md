# YouTube Digest

Turn YouTube videos into auditable EPUB digests, with a stable CLI designed for
personal automation, VPS deployment, pluggable LLM providers, and agent
integrations.

This repository is a productized derivative of
[zarazhangrui/youtube-to-ebook](https://github.com/zarazhangrui/youtube-to-ebook).
The original idea remains intact: fetch videos, get transcripts, transform them
with an LLM, and package the result as an ebook. This version adds a core Python
package, structured artifacts, SQLite idempotency, content modes, and a
stable command surface for automation and agents.

## What It Does

- Fetches recent long-form videos from configured YouTube channels.
- Gets transcripts through Supadata, defaulting to `mode=native` to avoid paid AI
  transcription surprises.
- Produces one of three content modes:
  - `faithful`: cleaned reading edition that preserves substantive content.
  - `magazine`: polished long-form article.
  - `summary`: concise briefing.
- Saves raw transcripts, prompts, generated Markdown, metadata, and EPUB files
  under `artifacts/`.
- Magazine mode saves intermediate `analysis.md`, draft, and expansion artifacts
  so long-form outputs can be audited and improved.
- Tracks processed videos in SQLite so scheduled runs are idempotent.
- Supports Anthropic, Gemini, DeepSeek, OpenAI, OpenRouter, and other
  OpenAI-compatible providers.
- Exposes a stable CLI that can be called by cron, systemd, Hermes, or future MCP
  adapters.

## Quick Start

```bash
git clone https://github.com/XiChuan9/youtube-digest.git
cd youtube-digest
python -m pip install -r requirements.txt
cp .env.example .env
python -m youtube_digest init
```

Edit `.env` with:

```bash
YOUTUBE_API_KEY=...
SUPADATA_API_KEY=...
OPENAI_API_KEY=...
```

You can use OpenRouter, DeepSeek, Gemini, local OpenAI-compatible servers, or
Anthropic instead. See [LLM Providers](docs/llm-providers.md).

Generate a digest:

```bash
python -m youtube_digest generate --mode magazine
```

Generate from a specific video instead of configured channels:

```bash
python -m youtube_digest generate --video-url "https://www.youtube.com/watch?v=..." --mode magazine
```

Preview which videos would be processed without calling transcript or LLM APIs:

```bash
python -m youtube_digest generate --dry-run
```

Manage channels:

```bash
python -m youtube_digest channels list
python -m youtube_digest channels add @3blue1brown
python -m youtube_digest channels remove @a16z
```

## CLI Contract

Hermes and other agents should treat the CLI as the stable integration boundary.

```bash
youtube-digest generate --mode faithful --json
youtube-digest generate --mode magazine --limit 3 --send-email
youtube-digest generate --video-url "https://www.youtube.com/watch?v=..." --mode magazine --json
youtube-digest generate --video-url "https://www.youtube.com/watch?v=..." --mode magazine --reuse-transcript --reuse-analysis --json
youtube-digest channels add @ycombinator
```

`--json` returns a machine-readable result with job status, selected videos,
artifact paths, generated article metadata, string `errors`, and structured
`error_details`. It omits full article Markdown by default because the content
is saved in artifacts; add `--include-content` when stdout should contain the
full article text.

## Cost Controls

The default configuration is intentionally conservative:

- Supadata uses `mode=native`, which only fetches existing transcripts.
- AI-generated transcription is disabled unless you set
  `transcript.native_transcripts_only` to `false`.
- `max_videos_per_run` limits paid LLM calls.
- `--dry-run` checks selection logic before spending transcript or LLM credits.
- `--reuse-transcript` and `--reuse-analysis` explicitly copy the latest matching
  artifact for the same video into the current job and skip those paid steps.

See [Cost Control](docs/cost-control.md).

## Hermes Skill

A first-pass Hermes skill lives in
[skills/hermes-youtube-digest/SKILL.md](skills/hermes-youtube-digest/SKILL.md).
It calls the CLI instead of importing internal Python modules. That keeps Hermes
integration thin, inspectable, and easy to replace with MCP later.

See [Hermes Integration](docs/hermes-skill.md).

## Dashboard

The CLI is the stable product surface. `dashboard.py` is kept as an experimental
Streamlit interface for local exploration, but it should not be used to judge the
production readiness of the project.

## VPS Deployment

Docker and systemd templates are included:

```bash
docker compose -f deploy/docker-compose.yml run --rm youtube-digest
```

See [VPS Deployment](docs/deployment-vps.md).

## CI and Smoke Tests

Default CI runs syntax checks, unit tests, CLI help, and legacy wrapper import
checks. Real API smoke tests are manual and optional:

```bash
python scripts/smoke_test.py --stage discovery
python scripts/smoke_test.py --stage transcript --video-url "https://www.youtube.com/watch?v=..."
python scripts/smoke_test.py --stage full --video-url "https://www.youtube.com/watch?v=..."
```

## Project Structure

```text
youtube_digest/
  cli.py                  # Stable CLI boundary
  pipeline.py             # End-to-end orchestration
  config.py               # JSON + environment config
  discovery/youtube.py    # YouTube Data API
  transcripts/supadata.py # Transcript provider
  llm/anthropic_writer.py # Article generation
  ebook/epub_builder.py   # EPUB output
  storage/                # SQLite + artifact storage
skills/hermes-youtube-digest/
dashboard.py              # Experimental Streamlit UI
docs/
tests/
```

## Development

Run syntax checks and tests:

```bash
scripts/quality.sh
```

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for source attribution.
