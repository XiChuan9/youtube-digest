# VPS Deployment

This project does not need a GPU. A small VPS is enough because transcript
fetching and LLM generation happen through external APIs.

Recommended baseline:

- 1 vCPU
- 1 GB RAM
- 10 GB disk
- Python 3.9+
- systemd timer or cron

Example systemd command:

```bash
youtube-digest generate --mode magazine --json
```

Keep these files persistent:

- `.env`
- `config.json`
- `artifacts/`

Do not expose dashboard or artifact directories publicly without authentication.

## Docker

Prepare local config:

```bash
cp .env.example .env
cp config.example.json config.json
mkdir -p artifacts newsletters
```

Run once:

```bash
docker compose -f deploy/docker-compose.yml run --rm youtube-digest
```

Schedule with host cron:

```cron
0 7 * * 3 cd /opt/youtube-digest && docker compose -f deploy/docker-compose.yml run --rm youtube-digest
```

## systemd

Use the files in [deploy/systemd](../deploy/systemd/README.md). The timer runs
weekly on Wednesday at 07:00 local server time by default.

## Optional Real API Smoke Tests

Discovery only:

```bash
YOUTUBE_API_KEY=... python scripts/smoke_test.py --stage discovery
```

Transcript only:

```bash
SUPADATA_API_KEY=... python scripts/smoke_test.py --stage transcript --video-url "https://www.youtube.com/watch?v=..."
```

Full smoke test, including a short LLM summary generation:

```bash
SUPADATA_API_KEY=... OPENAI_API_KEY=... python scripts/smoke_test.py --stage full --video-url "https://www.youtube.com/watch?v=..."
```

These smoke tests are intentionally separate from CI because they call paid or
quota-limited external services.

For DeepSeek, Gemini, OpenRouter, or local OpenAI-compatible servers, see
[LLM Providers](llm-providers.md).
