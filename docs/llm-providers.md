# LLM Providers

The LLM layer is configurable. The default provider is `openai_compatible`,
because many services implement the same `/chat/completions` interface.

## OpenAI

```json
{
  "llm": {
    "provider": "openai_compatible",
    "api_key_env": "OPENAI_API_KEY",
    "model": "gpt-4o-mini",
    "base_url": "https://api.openai.com/v1",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

OpenAI's Chat Completions API is available at `/v1/chat/completions`.

## DeepSeek

```json
{
  "llm": {
    "provider": "deepseek",
    "api_key_env": "DEEPSEEK_API_KEY",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

DeepSeek is handled through the OpenAI-compatible writer.

## OpenRouter

```json
{
  "llm": {
    "provider": "openrouter",
    "api_key_env": "OPENROUTER_API_KEY",
    "model": "openai/gpt-4o-mini",
    "base_url": "https://openrouter.ai/api/v1",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

OpenRouter uses `/api/v1/chat/completions`, with API key authentication through
the `Authorization: Bearer ...` header.

## Other OpenAI-Compatible Providers

```json
{
  "llm": {
    "provider": "openai_compatible",
    "api_key_env": "CUSTOM_LLM_API_KEY",
    "model": "provider/model-name",
    "base_url": "https://example.com/v1",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

Use this same pattern for local vLLM, LM Studio, Ollama OpenAI-compatible
servers, or hosted providers that expose `/chat/completions`.

## Gemini

```json
{
  "llm": {
    "provider": "gemini",
    "api_key_env": "GEMINI_API_KEY",
    "model": "gemini-2.5-flash",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

Gemini uses Google's `generateContent` REST endpoint and the `x-goog-api-key`
header.

## Anthropic

```json
{
  "llm": {
    "provider": "anthropic",
    "api_key_env": "ANTHROPIC_API_KEY",
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 8000,
    "temperature": 0.3
  }
}
```

Anthropic remains supported, but it is no longer the default.

## Smoke Testing a Provider

The full smoke test reads optional environment overrides:

```bash
YOUTUBE_DIGEST_LLM_PROVIDER=deepseek \
YOUTUBE_DIGEST_LLM_MODEL=deepseek-chat \
YOUTUBE_DIGEST_LLM_BASE_URL=https://api.deepseek.com \
YOUTUBE_DIGEST_LLM_API_KEY_ENV=DEEPSEEK_API_KEY \
DEEPSEEK_API_KEY=... \
SUPADATA_API_KEY=... \
python3 scripts/smoke_test.py --stage full --video-url 'https://www.youtube.com/watch?v=...'
```

For OpenRouter:

```bash
YOUTUBE_DIGEST_LLM_PROVIDER=openrouter \
YOUTUBE_DIGEST_LLM_MODEL=openai/gpt-4o-mini \
YOUTUBE_DIGEST_LLM_API_KEY_ENV=OPENROUTER_API_KEY \
OPENROUTER_API_KEY=... \
SUPADATA_API_KEY=... \
python3 scripts/smoke_test.py --stage full --video-url 'https://www.youtube.com/watch?v=...'
```

For Gemini:

```bash
YOUTUBE_DIGEST_LLM_PROVIDER=gemini \
YOUTUBE_DIGEST_LLM_MODEL=gemini-2.5-flash \
YOUTUBE_DIGEST_LLM_API_KEY_ENV=GEMINI_API_KEY \
GEMINI_API_KEY=... \
SUPADATA_API_KEY=... \
python3 scripts/smoke_test.py --stage full --video-url 'https://www.youtube.com/watch?v=...'
```
