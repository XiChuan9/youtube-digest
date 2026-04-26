import tempfile
import unittest
from pathlib import Path

from youtube_digest.models import Transcript, Video
from youtube_digest.pipeline import expand_short_magazine_article
from youtube_digest.storage.artifacts import ArtifactStore


class FakeWriter:
    def write(self, prompt):
        return "# Expanded\n\n" + "word " * 2800


class ExpansionTests(unittest.TestCase):
    def test_short_article_triggers_expansion(self):
        video = Video(
            title="Interview",
            video_id="vid",
            channel="Channel",
            url="https://example.com",
        )
        transcript = Transcript(video_id="vid", text="Transcript", source="test")

        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp)
            video_dir = Path(tmp) / "job" / "vid"
            video_dir.mkdir(parents=True)

            article = expand_short_magazine_article(
                video=video,
                transcript=transcript,
                outline="## Core Arguments\nA",
                draft="# Short\n\nToo short.",
                writer=FakeWriter(),
                artifact_store=store,
                video_dir=video_dir,
                min_words=3000,
                max_words=5000,
                section_min_words=350,
                section_max_words=550,
                max_passes=1,
            )

            self.assertIn("# Expanded", article)
            self.assertTrue((video_dir / "expansion_prompt_1.md").exists())
            self.assertTrue((video_dir / "article_expanded_1.md").exists())


if __name__ == "__main__":
    unittest.main()
