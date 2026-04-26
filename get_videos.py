"""Backward-compatible video discovery helpers.

New code should use `youtube_digest.discovery.youtube.YouTubeDiscovery` or the
`youtube-digest` CLI. These functions keep the original script API available.
"""

from youtube_digest.config import DEFAULT_CHANNELS, load_config
from youtube_digest.discovery.youtube import YouTubeDiscovery


CHANNELS = list(DEFAULT_CHANNELS)


def _to_legacy(video):
    return video.to_dict()


def get_channel_info(youtube, channel_handle):
    discovery = YouTubeDiscovery(api_key="")
    discovery._youtube = youtube
    return discovery.get_channel_info(channel_handle)


def is_youtube_short(video_id):
    return YouTubeDiscovery(api_key="").is_youtube_short(video_id)


def get_latest_video(youtube, uploads_playlist_id, channel_name):
    discovery = YouTubeDiscovery(api_key="")
    discovery._youtube = youtube
    videos = discovery.get_latest_videos(uploads_playlist_id, channel_name)
    return _to_legacy(videos[0]) if videos else None


def main():
    config = load_config()
    discovery = YouTubeDiscovery.from_config(config)
    videos = discovery.discover(config.youtube.channels)

    print("Fetching latest LONG-FORM videos (skipping Shorts)...\n")
    print("=" * 60)
    for video in videos:
        print(f"  ✓ {video.channel}: {video.title}")
        print(f"    URL: {video.url}\n")
    print("=" * 60)
    print(f"Found {len(videos)} videos total!")
    return [_to_legacy(video) for video in videos]


if __name__ == "__main__":
    main()
