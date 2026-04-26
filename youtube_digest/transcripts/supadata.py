"""Supadata transcript provider."""

import time
from typing import Any, Dict, Optional

from youtube_digest.config import DigestConfig, require_env
from youtube_digest.models import Transcript, Video
from youtube_digest.transcripts.base import TranscriptProvider


SUPADATA_TRANSCRIPT_URL = "https://api.supadata.ai/v1/transcript"


class SupadataTranscriptProvider(TranscriptProvider):
    def __init__(
        self,
        api_key: str,
        native_transcripts_only: bool = True,
        request_timeout_seconds: int = 60,
        max_poll_seconds: int = 300,
        poll_interval_seconds: int = 5,
    ):
        self.api_key = api_key
        self.native_transcripts_only = native_transcripts_only
        self.request_timeout_seconds = request_timeout_seconds
        self.max_poll_seconds = max_poll_seconds
        self.poll_interval_seconds = poll_interval_seconds

    @classmethod
    def from_config(cls, config: DigestConfig) -> "SupadataTranscriptProvider":
        api_key = require_env(config.transcript.api_key_env, "Supadata API key")
        return cls(
            api_key=api_key,
            native_transcripts_only=config.transcript.native_transcripts_only,
            request_timeout_seconds=config.transcript.request_timeout_seconds,
            max_poll_seconds=config.transcript.max_poll_seconds,
            poll_interval_seconds=config.transcript.poll_interval_seconds,
        )

    def fetch(self, video: Video) -> Transcript:
        import requests

        params = {
            "url": video.url,
            "text": "true",
            "mode": "native" if self.native_transcripts_only else "auto",
        }
        response = requests.get(
            SUPADATA_TRANSCRIPT_URL,
            params=params,
            headers={"x-api-key": self.api_key},
            timeout=self.request_timeout_seconds,
        )

        if response.status_code == 202:
            data = response.json()
            job_id = data.get("jobId")
            if not job_id:
                raise RuntimeError("Supadata returned HTTP 202 without jobId")
            data = self._poll_job(job_id)
        elif response.status_code == 200:
            data = response.json()
            if "jobId" in data:
                data = self._poll_job(data["jobId"])
        elif response.status_code == 404:
            raise RuntimeError("No transcript available")
        elif response.status_code == 401:
            raise RuntimeError("Invalid Supadata API key")
        elif response.status_code == 429:
            raise RuntimeError("Supadata rate limit exceeded")
        else:
            raise RuntimeError(f"Supadata API error {response.status_code}: {response.text[:200]}")

        text = self._extract_text(data)
        if not text:
            raise RuntimeError("Supadata response did not include transcript content")

        return Transcript(
            video_id=video.video_id,
            text=text,
            source="supadata:native" if self.native_transcripts_only else "supadata:auto",
            language=data.get("lang"),
            is_generated=not self.native_transcripts_only,
        )

    def _poll_job(self, job_id: str) -> Dict[str, Any]:
        import requests

        deadline = time.time() + self.max_poll_seconds
        url = f"{SUPADATA_TRANSCRIPT_URL}/{job_id}"

        while time.time() < deadline:
            response = requests.get(
                url,
                headers={"x-api-key": self.api_key},
                timeout=self.request_timeout_seconds,
            )
            if response.status_code != 200:
                raise RuntimeError(f"Supadata job error {response.status_code}: {response.text[:200]}")

            data = response.json()
            status = data.get("status")
            if status == "completed" or self._extract_text(data):
                return data
            if status == "failed":
                error = data.get("error") or {}
                raise RuntimeError(f"Supadata transcript job failed: {error.get('message', error)}")

            time.sleep(self.poll_interval_seconds)

        raise RuntimeError(f"Supadata transcript job timed out after {self.max_poll_seconds}s")

    def _extract_text(self, data: Dict[str, Any]) -> str:
        content: Optional[Any] = data.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return " ".join(str(segment.get("text", "")).strip() for segment in content).strip()
        if "transcript" in data and isinstance(data["transcript"], list):
            return " ".join(str(segment.get("text", "")).strip() for segment in data["transcript"]).strip()
        return ""
