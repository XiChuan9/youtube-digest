import unittest

from youtube_digest.ebook.epub_builder import build_source_notes
from youtube_digest.models import Article


class SourceNotesTests(unittest.TestCase):
    def test_source_notes_include_processing_metadata(self):
        article = Article(
            video_id="vid",
            title="Generated Title",
            channel="Channel",
            url="https://youtube.com/watch?v=vid",
            mode="magazine",
            markdown="# Article",
            model="openrouter/model",
            source_title="Original Title",
            source_published_at="2026-01-01T00:00:00Z",
            transcript_source="supadata:native",
            transcript_language="en",
        )

        notes = build_source_notes(article)

        self.assertIn("Original Title", notes)
        self.assertIn("openrouter/model", notes)
        self.assertIn("supadata:native", notes)
        self.assertIn("Digest mode", notes)


if __name__ == "__main__":
    unittest.main()
