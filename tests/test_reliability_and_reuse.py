import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_digest.errors import DigestError
from youtube_digest.models import Transcript, Video
from youtube_digest.pipeline import run_digest
from youtube_digest.storage.artifacts import ArtifactStore
from youtube_digest.storage.sqlite import DigestStore


class FixtureDiscovery:
    def __init__(self, videos):
        self.videos = videos

    def discover(self, channels):
        return self.videos

    def get_video_from_url(self, url):
        return self.videos[0]


class NotFoundDiscovery:
    def get_video_from_url(self, url):
        raise ValueError("YouTube video not found: missing")


class CountingTranscriptProvider:
    def __init__(self, transcript=None, exc=None):
        self.transcript = transcript
        self.exc = exc
        self.calls = 0

    def fetch(self, video):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.transcript or Transcript(
            video_id=video.video_id,
            text="Fresh transcript",
            source="test",
            language="en",
        )


class RecordingWriter:
    model_name = "test-model"

    def __init__(self, exc=None):
        self.exc = exc
        self.prompts = []

    def write(self, prompt):
        self.prompts.append(prompt)
        if self.exc:
            raise self.exc
        if "editorial analyst preparing" in prompt:
            return "## Analysis\n\nFresh analysis"
        return "# Article\n\n" + ("word " * 600)


def sample_video():
    return Video(
        title="Fixture Video",
        video_id="vid",
        channel="Fixture Channel",
        url="https://www.youtube.com/watch?v=vid",
    )


def write_config(root, extra=None):
    data = {
        "default_mode": "magazine",
        "max_videos_per_run": 5,
        "youtube": {
            "channels": ["@fixture"],
            "api_key_env": "YOUTUBE_DIGEST_TEST_MISSING_KEY",
        },
        "output": {
            "artifacts_dir": str(root / "artifacts"),
            "archive_dir": str(root / "newsletters"),
        },
        "content": {
            "analysis_min_words": 500,
            "analysis_max_words": 600,
            "magazine_min_words": 500,
            "magazine_max_words": 700,
            "magazine_expansion_passes": 0,
        },
    }
    if extra:
        for key, value in extra.items():
            if isinstance(value, dict) and isinstance(data.get(key), dict):
                data[key].update(value)
            else:
                data[key] = value
    path = root / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def pipeline_kwargs(root, video, transcript_provider=None, writer=None):
    return {
        "discovery": FixtureDiscovery([video]),
        "transcript_provider": transcript_provider or CountingTranscriptProvider(),
        "writer": writer or RecordingWriter(),
        "store": DigestStore(str(root / "digest.sqlite3")),
        "artifacts": ArtifactStore(str(root / "artifacts")),
    }


class ReliabilityAndReuseTests(unittest.TestCase):
    def test_bad_config_json_returns_config_error_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text('{\n  "default_mode": "magazine",\n}\n', encoding="utf-8")

            result = run_digest(config_path=str(config_path), dry_run=True)

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.error_details[0].code, "config_error")
            self.assertEqual(result.error_details[0].stage, "config")

    def test_missing_api_key_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = write_config(root)

            with patch.dict(os.environ, {"YOUTUBE_DIGEST_TEST_MISSING_KEY": ""}, clear=False):
                result = run_digest(config_path=str(config_path), dry_run=True)

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.error_details[0].code, "missing_api_key")
            self.assertEqual(result.error_details[0].stage, "discovery")
            self.assertEqual(result.error_details[0].provider, "youtube")

    def test_youtube_not_found_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = write_config(root)

            result = run_digest(
                config_path=str(config_path),
                video_url="https://www.youtube.com/watch?v=missing",
                discovery=NotFoundDiscovery(),
                store=DigestStore(str(root / "digest.sqlite3")),
                artifacts=ArtifactStore(str(root / "artifacts")),
            )

            detail = result.error_details[0]
            self.assertEqual(result.status, "failed")
            self.assertEqual(detail.code, "youtube_video_not_found")
            self.assertEqual(detail.stage, "discovery")
            self.assertEqual(detail.provider, "youtube")

    def test_supadata_rate_limit_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = sample_video()
            config_path = write_config(root)
            provider = CountingTranscriptProvider(
                exc=DigestError(
                    "Supadata rate limit exceeded",
                    code="supadata_rate_limit",
                    stage="transcript",
                    retryable=True,
                    provider="supadata",
                )
            )

            result = run_digest(
                config_path=str(config_path),
                **pipeline_kwargs(root, video, transcript_provider=provider),
            )

            detail = result.error_details[0]
            self.assertEqual(result.errors, ["vid: Supadata rate limit exceeded"])
            self.assertEqual(detail.code, "supadata_rate_limit")
            self.assertEqual(detail.stage, "transcript")
            self.assertEqual(detail.video_id, "vid")
            self.assertTrue(detail.retryable)
            self.assertEqual(detail.provider, "supadata")

    def test_llm_http_error_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = sample_video()
            config_path = write_config(root, {"default_mode": "summary"})
            writer = RecordingWriter(exc=RuntimeError("LLM API error 500: broken"))

            result = run_digest(
                config_path=str(config_path),
                **pipeline_kwargs(root, video, writer=writer),
            )

            detail = result.error_details[0]
            self.assertEqual(detail.code, "llm_provider_error")
            self.assertEqual(detail.stage, "writing")
            self.assertEqual(detail.video_id, "vid")
            self.assertTrue(detail.retryable)

    def test_reuse_transcript_copies_artifacts_and_skips_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = sample_video()
            config_path = write_config(root, {"default_mode": "summary"})
            old_dir = root / "artifacts" / "20260101T000000Z" / "vid"
            old_dir.mkdir(parents=True)
            old_dir.joinpath("raw_transcript.txt").write_text("Reused transcript", encoding="utf-8")
            old_dir.joinpath("transcript.json").write_text(
                json.dumps(
                    {
                        "video_id": "vid",
                        "text": "Reused transcript",
                        "source": "supadata:native",
                        "language": "en",
                        "is_generated": False,
                        "fetched_at": "2026-01-01T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            provider = CountingTranscriptProvider()

            result = run_digest(
                config_path=str(config_path),
                mode="summary",
                reuse_transcript=True,
                **pipeline_kwargs(root, video, transcript_provider=provider),
            )

            job_video_dir = Path(result.artifacts["job_dir"]) / "vid"
            reuse_manifest = json.loads(Path(result.artifacts["job_dir"]).joinpath("reuse.json").read_text())
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(provider.calls, 0)
            self.assertEqual(job_video_dir.joinpath("raw_transcript.txt").read_text(encoding="utf-8"), "Reused transcript")
            self.assertTrue(job_video_dir.joinpath("transcript.json").exists())
            self.assertEqual(reuse_manifest["reused"][0]["kind"], "transcript")
            self.assertEqual(reuse_manifest["reused"][0]["source_dir"], str(old_dir))

    def test_reuse_analysis_copies_artifact_and_skips_analysis_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = sample_video()
            config_path = write_config(root)
            old_dir = root / "artifacts" / "20260101T000000Z" / "vid"
            old_dir.mkdir(parents=True)
            old_dir.joinpath("analysis.md").write_text("## Reused Analysis\n\nUse this.", encoding="utf-8")
            writer = RecordingWriter()

            result = run_digest(
                config_path=str(config_path),
                reuse_analysis=True,
                **pipeline_kwargs(root, video, writer=writer),
            )

            job_video_dir = Path(result.artifacts["job_dir"]) / "vid"
            reuse_manifest = json.loads(Path(result.artifacts["job_dir"]).joinpath("reuse.json").read_text())
            self.assertEqual(result.status, "succeeded")
            self.assertFalse(any("editorial analyst preparing" in prompt for prompt in writer.prompts))
            self.assertEqual(job_video_dir.joinpath("analysis.md").read_text(encoding="utf-8"), "## Reused Analysis\n\nUse this.")
            self.assertEqual(reuse_manifest["reused"][0]["kind"], "analysis")

    def test_reuse_flags_fall_back_when_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = sample_video()
            config_path = write_config(root)
            provider = CountingTranscriptProvider()
            writer = RecordingWriter()

            result = run_digest(
                config_path=str(config_path),
                reuse_transcript=True,
                reuse_analysis=True,
                **pipeline_kwargs(root, video, transcript_provider=provider, writer=writer),
            )

            reuse_manifest = json.loads(Path(result.artifacts["job_dir"]).joinpath("reuse.json").read_text())
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(provider.calls, 1)
            self.assertTrue(any("editorial analyst preparing" in prompt for prompt in writer.prompts))
            self.assertEqual(reuse_manifest["reused"], [])


if __name__ == "__main__":
    unittest.main()
