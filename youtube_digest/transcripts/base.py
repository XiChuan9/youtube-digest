"""Transcript provider interface."""

from youtube_digest.models import Transcript, Video


class TranscriptProvider:
    def fetch(self, video: Video) -> Transcript:
        raise NotImplementedError
