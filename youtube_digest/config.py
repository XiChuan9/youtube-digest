"""Configuration loading and validation."""

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from youtube_digest.errors import MissingApiKeyError


DEFAULT_CHANNELS = [
    "@LatentSpacePod",
    "@ycombinator",
    "@a16z",
    "@RedpointAI",
    "@EveryInc",
    "@DataDrivenNYC",
    "@NoPriorsPodcast",
    "@DwarkeshPatel",
]


class ConfigError(ValueError):
    """Raised when a config file cannot be parsed or validated."""


@dataclass
class YouTubeConfig:
    api_key_env: str = "YOUTUBE_API_KEY"
    channels: List[str] = field(default_factory=lambda: list(DEFAULT_CHANNELS))
    lookback_items_per_channel: int = 15
    videos_per_channel: int = 1
    skip_shorts: bool = True


@dataclass
class TranscriptConfig:
    provider: str = "supadata"
    api_key_env: str = "SUPADATA_API_KEY"
    native_transcripts_only: bool = True
    request_timeout_seconds: int = 60
    max_poll_seconds: int = 300
    poll_interval_seconds: int = 5


@dataclass
class LLMConfig:
    provider: str = "openai_compatible"
    api_key_env: str = "OPENAI_API_KEY"
    model: str = "gpt-4o-mini"
    max_tokens: int = 8000
    base_url: str = "https://api.openai.com/v1"
    request_timeout_seconds: int = 120
    temperature: float = 0.3


@dataclass
class OutputConfig:
    artifacts_dir: str = "artifacts"
    archive_dir: str = "newsletters"


@dataclass
class DeliveryConfig:
    email_enabled: bool = False
    gmail_address_env: str = "GMAIL_ADDRESS"
    gmail_app_password_env: str = "GMAIL_APP_PASSWORD"
    recipient_email_env: str = "GMAIL_ADDRESS"


@dataclass
class ContentConfig:
    analysis_min_words: int = 1800
    analysis_max_words: int = 2500
    magazine_min_words: int = 3000
    magazine_max_words: int = 5000
    magazine_section_min_words: int = 350
    magazine_section_max_words: int = 550
    magazine_min_sections: int = 8
    magazine_max_sections: int = 10
    magazine_two_pass: bool = True
    magazine_expansion_passes: int = 1


@dataclass
class DigestConfig:
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    transcript: TranscriptConfig = field(default_factory=TranscriptConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    default_mode: str = "magazine"
    max_videos_per_run: int = 8

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _merge_dataclass(instance: Any, data: Dict[str, Any]) -> Any:
    for key, value in data.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
    return instance


def _format_json_error(path: Path, exc: json.JSONDecodeError) -> str:
    return (
        f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}. "
        "Config files must be strict JSON: use double quotes, remove trailing commas, "
        "and do not include comments."
    )


def load_config(path: Optional[str] = None) -> DigestConfig:
    """Load config from JSON. Missing files use defaults."""
    load_dotenv_if_available()

    config = DigestConfig()
    config_path = Path(path or "config.json")

    if not config_path.exists():
        return config

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(_format_json_error(config_path, exc)) from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Invalid config in {config_path}: top-level value must be a JSON object.")

    if "youtube" in raw:
        _merge_dataclass(config.youtube, raw["youtube"])
    if "transcript" in raw:
        _merge_dataclass(config.transcript, raw["transcript"])
    if "llm" in raw:
        _merge_dataclass(config.llm, raw["llm"])
    if "output" in raw:
        _merge_dataclass(config.output, raw["output"])
    if "delivery" in raw:
        _merge_dataclass(config.delivery, raw["delivery"])
    if "content" in raw:
        _merge_dataclass(config.content, raw["content"])

    for key in ("default_mode", "max_videos_per_run"):
        if key in raw:
            setattr(config, key, raw[key])

    validate_config(config)
    return config


def save_config(config: DigestConfig, path: str) -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
        f.write("\n")


def init_config(path: str = "config.json") -> bool:
    """Create a config file from the example. Returns True when created."""
    destination = Path(path)
    if destination.exists():
        return False

    example = Path(__file__).resolve().parent.parent / "config.example.json"
    if example.exists():
        shutil.copyfile(example, destination)
    else:
        save_config(DigestConfig(), path)
    return True


def resolve_env(name: str) -> Optional[str]:
    return os.getenv(name)


def require_env(name: str, label: str) -> str:
    value = resolve_env(name)
    if not value or value.startswith("your_"):
        raise MissingApiKeyError(label, name)
    return value


def validate_config(config: DigestConfig) -> None:
    valid_modes = {"faithful", "magazine", "summary"}
    if config.default_mode not in valid_modes:
        raise ValueError(f"default_mode must be one of {sorted(valid_modes)}")
    if config.max_videos_per_run < 1:
        raise ValueError("max_videos_per_run must be at least 1")
    if config.youtube.videos_per_channel < 1:
        raise ValueError("youtube.videos_per_channel must be at least 1")
    if config.youtube.lookback_items_per_channel < config.youtube.videos_per_channel:
        raise ValueError("youtube.lookback_items_per_channel must be >= youtube.videos_per_channel")
    if config.transcript.poll_interval_seconds < 1:
        raise ValueError("transcript.poll_interval_seconds must be at least 1")
    if config.content.magazine_min_words < 500:
        raise ValueError("content.magazine_min_words must be at least 500")
    if config.content.magazine_max_words < config.content.magazine_min_words:
        raise ValueError("content.magazine_max_words must be >= content.magazine_min_words")
    if config.content.analysis_min_words < 500:
        raise ValueError("content.analysis_min_words must be at least 500")
    if config.content.analysis_max_words < config.content.analysis_min_words:
        raise ValueError("content.analysis_max_words must be >= content.analysis_min_words")
    if config.content.magazine_min_sections < 1:
        raise ValueError("content.magazine_min_sections must be at least 1")
    if config.content.magazine_max_sections < config.content.magazine_min_sections:
        raise ValueError("content.magazine_max_sections must be >= content.magazine_min_sections")
    if config.content.magazine_section_max_words < config.content.magazine_section_min_words:
        raise ValueError("content.magazine_section_max_words must be >= content.magazine_section_min_words")
    if config.content.magazine_expansion_passes < 0:
        raise ValueError("content.magazine_expansion_passes must be >= 0")
    valid_llm_providers = {"anthropic", "openai_compatible", "openai", "openrouter", "deepseek", "gemini"}
    if config.llm.provider not in valid_llm_providers:
        raise ValueError(f"llm.provider must be one of {sorted(valid_llm_providers)}")
