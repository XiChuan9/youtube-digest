# Contributing

Thanks for helping make YouTube Digest sturdier.

## Development Setup

```bash
python -m pip install -r requirements.txt
python -m youtube_digest --help
```

For editable CLI installs:

```bash
python -m pip install -e .
```

## Quality Checks

Run the full local check before opening a pull request:

```bash
scripts/quality.sh
```

The default test suite must not call paid external APIs. Put real API checks in
`scripts/smoke_test.py` or manual workflow notes.

## Configuration and Secrets

Do not commit `.env`, `config.json`, generated artifacts, newsletters, SQLite
databases, EPUB files, or logs. Keep examples in `config.example.json` and
`.env.example`.

## Pull Request Guidelines

- Keep changes focused and explain user-visible behavior.
- Add or update tests for CLI contracts, artifact structure, provider behavior,
  and error handling.
- Preserve compatibility wrappers (`main.py`, `get_videos.py`,
  `get_transcripts.py`, `write_articles.py`, `send_email.py`) unless the change
  intentionally updates the compatibility surface.
- Treat `youtube_digest` and the CLI as the stable core. The Streamlit dashboard
  is experimental.

## Documentation

Update `README.md` for common workflows and add deeper notes under `docs/` when
the behavior needs operational detail.
