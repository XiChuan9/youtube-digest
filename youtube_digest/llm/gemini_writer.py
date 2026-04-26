"""Gemini REST writer."""

from typing import Any, Dict, List

from youtube_digest.config import DigestConfig, require_env
from youtube_digest.errors import DigestError
from youtube_digest.llm.base import ArticleWriter


class GeminiArticleWriter(ArticleWriter):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        max_tokens: int = 8000,
        request_timeout_seconds: int = 120,
        temperature: float = 0.3,
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.request_timeout_seconds = request_timeout_seconds
        self.temperature = temperature

    @classmethod
    def from_config(cls, config: DigestConfig) -> "GeminiArticleWriter":
        api_key = require_env(config.llm.api_key_env, "Gemini API key")
        return cls(
            api_key=api_key,
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
            request_timeout_seconds=config.llm.request_timeout_seconds,
            temperature=config.llm.temperature,
        )

    @property
    def model_name(self) -> str:
        return self.model

    def write(self, prompt: str) -> str:
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.request_timeout_seconds,
        )
        if response.status_code >= 400:
            raise DigestError(
                f"Gemini API error {response.status_code}: {response.text[:500]}",
                code="llm_provider_error",
                retryable=response.status_code in {408, 409, 429, 500, 502, 503, 504},
                provider="gemini",
            )

        data = response.json()
        candidates: List[Dict[str, Any]] = data.get("candidates") or []
        if not candidates:
            feedback = data.get("promptFeedback") or data.get("prompt_feedback")
            raise RuntimeError(f"Gemini response did not include candidates: {feedback}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if not text:
            raise RuntimeError("Gemini response did not include text content")
        return text.strip()
