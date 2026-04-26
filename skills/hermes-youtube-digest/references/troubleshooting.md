# Troubleshooting

`YouTube Data API key is not configured`

Set `YOUTUBE_API_KEY` in `.env`.

`Supadata API key is not configured`

Set `SUPADATA_API_KEY` in `.env`.

`No transcript available`

The video likely has no native transcript. By default the project does not fall
back to generated transcripts to avoid surprise costs.

`openai_compatible API key is not configured`

The default config expects `OPENAI_API_KEY`. If the user wants DeepSeek, Gemini,
OpenRouter, or Anthropic, update `config.json` and set the matching key.

`No new videos`

The SQLite store already marks the selected videos as processed. Use `--force`
only when the user explicitly wants regeneration.

`Invalid JSON in config.json at line ...`

Fix the reported line and column. Config files are strict JSON: keys and strings
need double quotes, trailing commas are not allowed, and comments are not
allowed.
