"""Structured error helpers for the digest pipeline."""

from typing import Optional

from youtube_digest.models import ErrorDetail


class DigestError(RuntimeError):
    def __init__(
        self,
        message: str,
        code: str = "unknown_error",
        stage: Optional[str] = None,
        retryable: bool = False,
        provider: Optional[str] = None,
        video_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.retryable = retryable
        self.provider = provider
        self.video_id = video_id


class MissingApiKeyError(DigestError):
    def __init__(self, label: str, env_name: str):
        super().__init__(
            f"{label} is not configured. Set {env_name} in .env or the environment.",
            code="missing_api_key",
            retryable=False,
        )
        self.env_name = env_name


def error_detail_from_exception(
    exc: Exception,
    stage: str,
    video_id: Optional[str] = None,
    provider: Optional[str] = None,
    default_code: str = "unknown_error",
) -> ErrorDetail:
    message = str(exc)
    code = default_code
    retryable = False
    detail_stage = stage
    detail_video_id = video_id
    detail_provider = provider

    if isinstance(exc, DigestError):
        code = exc.code or code
        retryable = exc.retryable
        detail_stage = exc.stage or detail_stage
        detail_video_id = exc.video_id or detail_video_id
        detail_provider = exc.provider or detail_provider
    else:
        code, retryable = classify_error_message(message, stage, default_code)

    if detail_stage == "config" and code == "unknown_error":
        code = "config_error"

    return ErrorDetail(
        code=code,
        message=message,
        stage=detail_stage,
        video_id=detail_video_id,
        retryable=retryable,
        provider=detail_provider,
    )


def classify_error_message(message: str, stage: str, default_code: str = "unknown_error") -> tuple[str, bool]:
    lower = message.lower()

    if "is not configured. set " in lower:
        return "missing_api_key", False
    if "youtube video not found" in lower:
        return "youtube_video_not_found", False
    if "no transcript available" in lower or "did not include transcript content" in lower:
        return "no_native_transcript", False
    if "supadata rate limit" in lower or "supadata api error 429" in lower:
        return "supadata_rate_limit", True
    if "llm api error" in lower or "gemini api error" in lower or "anthropic api error" in lower:
        return "llm_provider_error", _looks_retryable_provider_error(lower)
    if stage == "epub":
        return "epub_generation_failed", False
    if stage == "config":
        return "config_error", False

    return default_code, False


def _looks_retryable_provider_error(lower_message: str) -> bool:
    retryable_markers = (" 408", " 409", " 429", " 500", " 502", " 503", " 504", "timeout", "temporarily")
    return any(marker in lower_message for marker in retryable_markers)
