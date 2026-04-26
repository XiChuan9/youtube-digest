"""Shared data models for the digest pipeline."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Video:
    title: str
    video_id: str
    channel: str
    url: str
    description: str = ""
    published_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Transcript:
    video_id: str
    text: str
    source: str
    language: Optional[str] = None
    is_generated: bool = False
    fetched_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Article:
    video_id: str
    title: str
    channel: str
    url: str
    mode: str
    markdown: str
    model: Optional[str] = None
    source_title: Optional[str] = None
    source_published_at: Optional[str] = None
    transcript_source: Optional[str] = None
    transcript_language: Optional[str] = None
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorDetail:
    code: str
    message: str
    stage: str
    video_id: Optional[str] = None
    retryable: bool = False
    provider: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DigestResult:
    job_id: str
    mode: str
    status: str
    videos_found: int
    videos_selected: int
    articles: List[Article] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    error_details: List[ErrorDetail] = field(default_factory=list)

    def to_dict(self, include_article_markdown: bool = True) -> Dict[str, Any]:
        data = asdict(self)
        data["articles"] = []
        for article in self.articles:
            article_data = article.to_dict()
            if not include_article_markdown:
                article_data.pop("markdown", None)
            data["articles"].append(article_data)
        return data
