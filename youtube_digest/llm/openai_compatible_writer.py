"""OpenAI-compatible chat completions writer.

This covers OpenAI, DeepSeek, OpenRouter, local vLLM, Ollama OpenAI-compatible
servers, and many hosted providers that implement `/chat/completions`.
"""

from typing import Any, Dict

from youtube_digest.config import DigestConfig, require_env
from youtube_digest.llm.base import ArticleWriter


class OpenAICompatibleArticleWriter(ArticleWriter):
    provider_name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        max_tokens: int = 8000,
        request_timeout_seconds: int = 120,
        temperature: float = 0.3,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.request_timeout_seconds = request_timeout_seconds
        self.temperature = temperature

    @classmethod
    def from_config(cls, config: DigestConfig) -> "OpenAICompatibleArticleWriter":
        api_key = require_env(config.llm.api_key_env, f"{config.llm.provider} API key")
        base_url = config.llm.base_url
        if config.llm.provider == "deepseek" and base_url == "https://api.openai.com/v1":
            base_url = "https://api.deepseek.com"
        if config.llm.provider == "openrouter" and base_url == "https://api.openai.com/v1":
            base_url = "https://openrouter.ai/api/v1"
        return cls(
            api_key=api_key,
            model=config.llm.model,
            base_url=base_url,
            max_tokens=config.llm.max_tokens,
            request_timeout_seconds=config.llm.request_timeout_seconds,
            temperature=config.llm.temperature,
        )

    @property
    def model_name(self) -> str:
        return self.model

    def write(self, prompt: str) -> str:
        import requests

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.request_timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"LLM API error {response.status_code}: {response.text[:500]}")

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response did not include choices")
        content = choices[0].get("message", {}).get("content")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = "".join(text_parts)
        if not content:
            raise RuntimeError("LLM response did not include message content")
        return str(content).strip()
