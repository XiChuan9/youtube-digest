import json
import tempfile
import unittest
from pathlib import Path

from youtube_digest.models import Video
from youtube_digest.pipeline import run_digest
from youtube_digest.storage.artifacts import ArtifactStore
from youtube_digest.storage.sqlite import DigestStore


class FixtureDiscovery:
    def __init__(self, videos):
        self.videos = videos

    def discover(self, channels):
        return self.videos


class SingleVideoDiscovery:
    def __init__(self, video):
        self.video = video

    def get_video_from_url(self, url):
        return self.video


class PipelineDryRunTests(unittest.TestCase):
    def test_dry_run_uses_fixture_and_writes_selected_videos(self):
        fixture_path = Path(__file__).parent / "fixtures" / "videos.json"
        fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
        videos = [Video(**item) for item in fixture_data]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "default_mode": "magazine",
                        "max_videos_per_run": 5,
                        "youtube": {"channels": ["@fixture"]},
                        "output": {
                            "artifacts_dir": str(root / "artifacts"),
                            "archive_dir": str(root / "newsletters"),
                        },
                    }
                ),
                encoding="utf-8",
            )

            store = DigestStore(str(root / "digest.sqlite3"))
            store.mark_processed(videos[1])

            result = run_digest(
                config_path=str(config_path),
                dry_run=True,
                discovery=FixtureDiscovery(videos),
                store=store,
                artifacts=ArtifactStore(str(root / "artifacts")),
            )

            self.assertEqual(result.status, "dry_run")
            self.assertEqual(result.videos_found, 2)
            self.assertEqual(result.videos_selected, 1)

            selected_path = Path(result.artifacts["job_dir"]) / "selected_videos.json"
            selected = json.loads(selected_path.read_text(encoding="utf-8"))
            self.assertEqual(selected["videos"][0]["video_id"], "video-new")

    def test_dry_run_can_select_explicit_video_url(self):
        video = Video(
            title="Explicit Video",
            video_id="explicit-id",
            channel="Fixture Channel",
            url="https://www.youtube.com/watch?v=explicit-id",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "default_mode": "magazine",
                        "output": {
                            "artifacts_dir": str(root / "artifacts"),
                            "archive_dir": str(root / "newsletters"),
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = run_digest(
                config_path=str(config_path),
                video_url="https://youtu.be/explicit-id",
                dry_run=True,
                discovery=SingleVideoDiscovery(video),
                store=DigestStore(str(root / "digest.sqlite3")),
                artifacts=ArtifactStore(str(root / "artifacts")),
            )

            self.assertEqual(result.status, "dry_run")
            self.assertEqual(result.videos_found, 1)
            self.assertEqual(result.videos_selected, 1)

            selected_path = Path(result.artifacts["job_dir"]) / "selected_videos.json"
            selected = json.loads(selected_path.read_text(encoding="utf-8"))
            self.assertEqual(selected["videos"][0]["video_id"], "explicit-id")


if __name__ == "__main__":
    unittest.main()
