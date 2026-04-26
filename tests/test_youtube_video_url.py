import unittest

from youtube_digest.discovery.youtube import parse_youtube_video_id


class YouTubeVideoUrlTests(unittest.TestCase):
    def test_parses_standard_watch_url(self):
        self.assertEqual(
            parse_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=abc"),
            "dQw4w9WgXcQ",
        )

    def test_parses_short_share_url(self):
        self.assertEqual(parse_youtube_video_id("https://youtu.be/dQw4w9WgXcQ?si=abc"), "dQw4w9WgXcQ")

    def test_parses_shorts_embed_live_and_raw_ids(self):
        self.assertEqual(parse_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertEqual(parse_youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertEqual(parse_youtube_video_id("https://www.youtube.com/live/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertEqual(parse_youtube_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_rejects_unparseable_url(self):
        with self.assertRaises(ValueError):
            parse_youtube_video_id("https://example.com/not-youtube")


if __name__ == "__main__":
    unittest.main()
