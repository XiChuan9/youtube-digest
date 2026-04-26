"""YouTube discovery using the Data API."""

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from youtube_digest.config import DigestConfig, require_env
from youtube_digest.models import Video


def parse_youtube_video_id(value: str) -> str:
    """Extract a YouTube video ID from a URL or return a raw video ID."""
    candidate = value.strip()
    if not candidate:
        raise ValueError("video URL cannot be empty")

    if "://" not in candidate and ("youtube.com" in candidate or "youtu.be" in candidate):
        candidate = f"https://{candidate}"

    if "://" not in candidate and "/" not in candidate and "?" not in candidate:
        return candidate

    parsed = urlparse(candidate)
    query = parse_qs(parsed.query)
    if query.get("v") and query["v"][0].strip():
        return query["v"][0].strip()

    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host.endswith("youtu.be") and path_parts:
        return path_parts[0]

    if "youtube.com" in host and len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
        return path_parts[1]

    raise ValueError(f"Could not parse a YouTube video ID from: {value}")


class YouTubeDiscovery:
    def __init__(
        self,
        api_key: str,
        lookback_items_per_channel: int = 15,
        videos_per_channel: int = 1,
        skip_shorts: bool = True,
    ):
        self.api_key = api_key
        self.lookback_items_per_channel = lookback_items_per_channel
        self.videos_per_channel = videos_per_channel
        self.skip_shorts = skip_shorts
        self._youtube = None

    @classmethod
    def from_config(cls, config: DigestConfig) -> "YouTubeDiscovery":
        api_key = require_env(config.youtube.api_key_env, "YouTube Data API key")
        return cls(
            api_key=api_key,
            lookback_items_per_channel=config.youtube.lookback_items_per_channel,
            videos_per_channel=config.youtube.videos_per_channel,
            skip_shorts=config.youtube.skip_shorts,
        )

    @property
    def youtube(self):
        if self._youtube is None:
            from googleapiclient.discovery import build

            self._youtube = build("youtube", "v3", developerKey=self.api_key)
        return self._youtube

    def get_channel_info(self, channel_handle: str) -> Optional[Dict[str, str]]:
        handle = self._normalize_channel_ref(channel_handle)
        request_kwargs = {"part": "snippet,contentDetails"}
        if handle.startswith("UC"):
            request_kwargs["id"] = handle
        else:
            request_kwargs["forHandle"] = handle.lstrip("@")

        response = self.youtube.channels().list(**request_kwargs).execute()

        if not response.get("items"):
            return None

        channel = response["items"][0]
        return {
            "channel_id": channel["id"],
            "channel_name": channel["snippet"]["title"],
            "uploads_playlist_id": channel["contentDetails"]["relatedPlaylists"]["uploads"],
        }

    def _normalize_channel_ref(self, channel_ref: str) -> str:
        value = channel_ref.strip()
        if "youtube.com/channel/" in value:
            return value.split("youtube.com/channel/", 1)[1].split("/", 1)[0]
        if "youtube.com/@" in value:
            return value.split("youtube.com/@", 1)[1].split("/", 1)[0].lstrip("@")
        return value

    def is_youtube_short(self, video_id: str) -> bool:
        if not self.skip_shorts:
            return False

        import requests

        shorts_url = f"https://www.youtube.com/shorts/{video_id}"
        try:
            response = requests.head(shorts_url, allow_redirects=True, timeout=5)
            return "/shorts/" in response.url
        except Exception:
            return False

    def get_latest_videos(self, uploads_playlist_id: str, channel_name: str) -> List[Video]:
        response = self.youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=self.lookback_items_per_channel,
        ).execute()

        videos = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]

            if self.is_youtube_short(video_id):
                continue

            videos.append(
                Video(
                    title=snippet["title"],
                    video_id=video_id,
                    description=snippet.get("description", ""),
                    channel=channel_name,
                    published_at=snippet.get("publishedAt"),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                )
            )

            if len(videos) >= self.videos_per_channel:
                break

        return videos

    def get_video_from_url(self, video_url: str) -> Video:
        video_id = parse_youtube_video_id(video_url)
        response = self.youtube.videos().list(part="snippet", id=video_id).execute()

        if not response.get("items"):
            raise ValueError(f"YouTube video not found: {video_id}")

        snippet = response["items"][0]["snippet"]
        return Video(
            title=snippet["title"],
            video_id=video_id,
            description=snippet.get("description", ""),
            channel=snippet.get("channelTitle", "Unknown channel"),
            published_at=snippet.get("publishedAt"),
            url=f"https://www.youtube.com/watch?v={video_id}",
        )

    def discover(self, channels: List[str]) -> List[Video]:
        videos = []
        for channel_handle in channels:
            channel_info = self.get_channel_info(channel_handle)
            if not channel_info:
                continue
            videos.extend(
                self.get_latest_videos(
                    channel_info["uploads_playlist_id"],
                    channel_info["channel_name"],
                )
            )
        return videos
