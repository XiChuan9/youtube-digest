"""Human-readable filenames for generated digest artifacts."""

from typing import Iterable, List

from youtube_digest.models import Article
from youtube_digest.storage.artifacts import safe_slug


def _slug(value: str, fallback: str) -> str:
    return safe_slug(value, fallback).lower()


def digest_descriptor(articles: Iterable[Article], max_length: int = 110) -> str:
    article_list = list(articles)
    if not article_list:
        return "digest"

    if len(article_list) == 1:
        article = article_list[0]
        channel = _slug(article.channel, "channel")
        title = _slug(article.source_title or article.title or article.video_id, article.video_id or "video")
        descriptor = f"{channel}_{title}"
    else:
        channels: List[str] = []
        for article in article_list:
            channel = _slug(article.channel, "channel")
            if channel not in channels:
                channels.append(channel)
            if len(channels) >= 3:
                break
        descriptor = f"{len(article_list)}-videos_{'-'.join(channels)}"

    return descriptor[:max_length].rstrip("-_.") or "digest"


def digest_filename(prefix: str, timestamp: str, articles: Iterable[Article], extension: str) -> str:
    clean_prefix = _slug(prefix, "youtube-digest")
    clean_timestamp = safe_slug(timestamp, "timestamp")
    clean_extension = extension.lstrip(".").lower()
    return f"{clean_prefix}_{clean_timestamp}_{digest_descriptor(articles)}.{clean_extension}"
