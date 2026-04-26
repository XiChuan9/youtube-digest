"""Backward-compatible article writing helpers.

New code should use `youtube_digest.processing` and `youtube_digest.llm`.
"""

from youtube_digest.config import load_config
from youtube_digest.models import Transcript, Video
from youtube_digest.pipeline import build_writer
from youtube_digest.processing.prompts import build_article_prompt


def _legacy_to_video(video):
    return Video(
        title=video.get("title", "Untitled"),
        video_id=video.get("video_id", video.get("url", "")),
        channel=video.get("channel", "Unknown"),
        url=video.get("url", ""),
        description=video.get("description", ""),
        published_at=video.get("published_at"),
    )


def write_article(video, mode=None):
    config = load_config()
    selected_mode = mode or config.default_mode
    writer = build_writer(config)
    video_model = _legacy_to_video(video)
    transcript = Transcript(
        video_id=video_model.video_id,
        text=video["transcript"],
        source=video.get("transcript_source", "legacy"),
        language=video.get("transcript_language"),
    )
    prompt = build_article_prompt(video_model, transcript, selected_mode)
    try:
        return writer.write(prompt)
    except Exception as exc:
        print(f"  ! Error generating article: {exc}")
        return None


def write_articles_for_videos(videos, mode=None):
    config = load_config()
    print(f"\nGenerating articles with {config.llm.provider}...\n")
    print("=" * 60)
    articles = []

    for video in videos:
        print(f"Writing article: {video['title'][:50]}...")
        article = write_article(video, mode=mode)
        if article:
            articles.append(
                {
                    "title": video["title"],
                    "channel": video["channel"],
                    "url": video["url"],
                    "article": article,
                    "video_id": video.get("video_id"),
                    "mode": mode or config.default_mode,
                    "model": config.llm.model,
                    "source_title": video.get("title"),
                    "source_published_at": video.get("published_at"),
                    "transcript_source": video.get("transcript_source"),
                    "transcript_language": video.get("transcript_language"),
                }
            )
            print("  ✓ Article generated!\n")
        else:
            print("  ! Failed to generate article\n")

    print("=" * 60)
    print(f"Generated {len(articles)} articles")
    return articles


if __name__ == "__main__":
    print("Use `python -m youtube_digest generate --mode magazine` to generate articles.")
