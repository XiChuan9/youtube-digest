"""Anthropic article writer."""

from youtube_digest.config import DigestConfig, require_env
from youtube_digest.llm.base import ArticleWriter


class AnthropicArticleWriter(ArticleWriter):
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str, max_tokens: int = 8000):
        import anthropic

        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self.model

    @classmethod
    def from_config(cls, config: DigestConfig) -> "AnthropicArticleWriter":
        api_key = require_env(config.llm.api_key_env, "Anthropic API key")
        return cls(
            api_key=api_key,
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
        )

    def write(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
