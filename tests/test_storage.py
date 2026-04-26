import tempfile
import unittest
from pathlib import Path

from youtube_digest.models import Video
from youtube_digest.storage.sqlite import DigestStore


class StorageTests(unittest.TestCase):
    def test_marks_processed_videos(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = DigestStore(str(Path(tmp) / "digest.sqlite3"))
            video = Video(
                title="Test",
                video_id="abc123",
                channel="Example",
                url="https://youtube.com/watch?v=abc123",
            )

            self.assertEqual(store.filter_new([video]), [video])
            store.mark_processed(video)
            self.assertEqual(store.filter_new([video]), [])
            self.assertEqual(store.filter_new([video], force=True), [video])


if __name__ == "__main__":
    unittest.main()
