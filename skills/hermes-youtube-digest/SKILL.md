---
name: hermes-youtube-digest
description: Generate auditable YouTube EPUB digests through the youtube-digest CLI
version: 0.1.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [youtube, epub, automation, digest]
    category: productivity
    requires_toolsets: [terminal]
required_environment_variables:
  - name: YOUTUBE_API_KEY
    prompt: YouTube Data API key
    help: Required to discover channel videos.
    required_for: video discovery
  - name: SUPADATA_API_KEY
    prompt: Supadata API key
    help: Required to fetch transcripts.
    required_for: transcript fetching
  - name: OPENAI_API_KEY
    prompt: OpenAI-compatible LLM API key
    help: Required by the default LLM provider. Users may configure another provider/key.
    required_for: article generation
---

# Hermes YouTube Digest

Use this skill when the user wants to turn YouTube channel videos into EPUB
digests, manage subscribed channels, preview processing costs, or retrieve
generated artifact paths.

## Operating Contract

Call the CLI. Do not import internal Python modules.

```bash
youtube-digest generate --mode magazine --json
youtube-digest generate --mode faithful --json
youtube-digest generate --video-url "https://www.youtube.com/watch?v=..." --mode magazine --json
youtube-digest generate --dry-run --json
youtube-digest channels list
youtube-digest channels add @channel
```

If the command is unavailable, ask the user to install the package in the active
environment:

```bash
python -m pip install -e .
```

## Modes

- `faithful`: cleaned reading edition, preserves substantive content.
- `magazine`: rewritten long-form article, not a verbatim transcript.
- `summary`: concise briefing.

When the user asks whether content is deleted, explain that raw transcripts are
saved under `artifacts/<job_id>/`, and the selected mode controls how much
compression happens.

## Safety and Cost

Before processing many videos, prefer:

```bash
youtube-digest generate --dry-run --json
```

When the user provides a specific YouTube video URL, pass it through with
`--video-url` instead of changing channel configuration.

Default config uses Supadata `mode=native`, which avoids AI transcription
fallback costs. Use `--limit 1` for first runs.

LLM provider is configurable. The default is OpenAI-compatible
`/chat/completions`, but users can switch to OpenRouter, DeepSeek, Gemini,
Anthropic, or local compatible servers in `config.json`.

## Result Handling

Parse the JSON result and report:

- `status`
- `videos_selected`
- `artifacts.epub`
- `artifacts.manifest`
- any `errors`

If status is `failed` or `no_articles`, summarize the error and suggest checking
API keys or transcript availability.

## Installation Notes

Hermes discovers skills from `~/.hermes/skills/` and configured external skill
directories. This repository can be symlinked into the local skill tree:

```bash
mkdir -p ~/.hermes/skills/productivity
ln -s "$PWD/skills/hermes-youtube-digest" ~/.hermes/skills/productivity/youtube-digest
```

Alternatively, add this repository's `skills/` directory to Hermes
`skills.external_dirs`.
