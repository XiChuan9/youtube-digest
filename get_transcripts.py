"""Backward-compatible transcript helpers.

New code should use `youtube_digest.transcripts.supadata.SupadataTranscriptProvider`.
"""

import time

from youtube_digest.config import load_config
from youtube_digest.models import Video
from youtube_digest.transcripts.supadata import SupadataTranscriptProvider


def _legacy_to_video(video):
    return Video(
        title=video.get("title", video.get("video_id", "Untitled")),
        video_id=video["video_id"],
        channel=video.get("channel", "Unknown"),
        url=video.get("url", f"https://www.youtube.com/watch?v={video['video_id']}"),
        description=video.get("description", ""),
        published_at=video.get("published_at"),
    )


def get_transcript(video_id):
    config = load_config()
    provider = SupadataTranscriptProvider.from_config(config)
    video = Video(
        title=video_id,
        video_id=video_id,
        channel="Unknown",
        url=f"https://www.youtube.com/watch?v={video_id}",
    )
    try:
        return provider.fetch(video).text
    except Exception as exc:
        print(f"  ! Error getting transcript: {exc}")
        return None


def get_transcripts_for_videos(videos):
    config = load_config()
    provider = SupadataTranscriptProvider.from_config(config)

    print("\nExtracting transcripts via Supadata API...\n")
    print("=" * 60)
    result = []

    for i, video in enumerate(videos):
        print(f"Getting transcript: {video['title'][:50]}...")
        try:
            transcript = provider.fetch(_legacy_to_video(video))
            video["transcript"] = transcript.text
            video["transcript_source"] = transcript.source
            video["transcript_language"] = transcript.language
            print(f"  ✓ Got {len(transcript.text.split())} words\n")
            result.append(video)
        except Exception as exc:
            video["transcript"] = None
            print(f"  ! No transcript available: {exc}\n")

        if i < len(videos) - 1:
            time.sleep(1)

    print("=" * 60)
    print(f"Got transcripts for {len(result)} of {len(videos)} videos")
    return result


if __name__ == "__main__":
    print("Use `python -m youtube_digest generate --dry-run` to preview a run.")
