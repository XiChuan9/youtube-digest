# Hermes Integration

The Hermes skill is intentionally thin. It should call:

```bash
youtube-digest generate --mode magazine --json
youtube-digest generate --mode faithful --json
youtube-digest generate --video-url "https://www.youtube.com/watch?v=..." --mode magazine --json
youtube-digest channels add @example
youtube-digest channels list
```

By default, `--json` omits full article Markdown to keep Hermes responses
compact. Full content is saved under the artifact directory. Use
`--include-content` only when the caller explicitly needs article text in stdout.

Why CLI first:

- It can be tested independently of Hermes.
- It gives stable JSON for agent parsing.
- It can be reused by cron, systemd, Docker, or manual shell use.
- It leaves room for a future MCP server without rewriting the core pipeline.

## Install

Install the CLI in the same environment Hermes can execute:

```bash
python -m pip install -e .
youtube-digest --help
```

Install the skill by symlinking it into Hermes' local skill tree:

```bash
mkdir -p ~/.hermes/skills/productivity
ln -s "$PWD/skills/hermes-youtube-digest" ~/.hermes/skills/productivity/youtube-digest
```

Hermes also supports external skill directories. Add this repository's `skills/`
directory to `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - /opt/youtube-digest-hermes/skills
```

Hermes documents `~/.hermes/skills/` as the primary skill directory and supports
additional `skills.external_dirs` for shared repositories.

## Verify

```bash
youtube-digest generate --dry-run --json
youtube-digest generate --video-url "https://www.youtube.com/watch?v=..." --dry-run --json
```

Then ask Hermes:

```text
/youtube-digest generate my next magazine digest
```

The skill should report the generated EPUB path or any missing API key.

Future MCP tools could map directly to CLI-backed operations:

- `add_channel(handle)`
- `list_channels()`
- `generate_digest(mode, limit, send_email, video_url)`
- `list_archive()`
- `get_digest(job_id)`

References:

- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills/
