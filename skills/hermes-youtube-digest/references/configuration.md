# Configuration

Primary files:

- `.env`: API keys and mail credentials.
- `config.json`: channels, output paths, model choices, and limits.

Required environment variables for default generation:

- `YOUTUBE_API_KEY`
- `SUPADATA_API_KEY`
- `OPENAI_API_KEY`

Alternative LLM keys depend on `config.json`:

- `DEEPSEEK_API_KEY`
- `OPENROUTER_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- any custom `api_key_env` used by an OpenAI-compatible provider

Optional email variables:

- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
