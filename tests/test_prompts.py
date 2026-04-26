import unittest

from youtube_digest.models import Transcript, Video
from youtube_digest.processing.prompts import build_article_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_mentions_selected_mode_behavior(self):
        video = Video(
            title="A talk",
            video_id="vid",
            channel="Channel",
            url="https://youtube.com/watch?v=vid",
            description="Description",
        )
        transcript = Transcript(video_id="vid", text="Hello world", source="test")

        prompt = build_article_prompt(video, transcript, "faithful")

        self.assertIn("Preserve all substantive claims", prompt)
        self.assertIn("Hello world", prompt)


if __name__ == "__main__":
    unittest.main()
