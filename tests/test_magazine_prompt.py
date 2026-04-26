import unittest

from youtube_digest.models import Transcript, Video
from youtube_digest.processing.prompts import (
    build_article_expansion_prompt,
    build_article_from_outline_prompt,
    build_article_prompt,
    build_transcript_analysis_prompt,
)


class MagazinePromptTests(unittest.TestCase):
    def test_magazine_prompt_requests_long_read_and_rejects_pr_copy(self):
        video = Video(
            title="Interview",
            video_id="vid",
            channel="Channel",
            url="https://example.com",
            description="Description",
        )
        transcript = Transcript(video_id="vid", text="Transcript", source="test")

        prompt = build_article_prompt(video, transcript, "magazine")

        self.assertIn("3000-5000 words", prompt)
        self.assertIn("Adapt to the subject matter", prompt)
        self.assertIn("Avoid corporate blog language", prompt)
        self.assertIn("Keep the texture of the source", prompt)

    def test_analysis_prompt_is_cross_domain_and_structured(self):
        video = Video(
            title="Interview",
            video_id="vid",
            channel="Channel",
            url="https://example.com",
            description="Description",
        )
        transcript = Transcript(video_id="vid", text="Transcript", source="test")

        prompt = build_transcript_analysis_prompt(video, transcript)

        self.assertIn("1800-2500 words", prompt)
        self.assertIn("Do not assume the topic is technology", prompt)
        self.assertIn("## Core Arguments", prompt)
        self.assertIn("## Article Architecture", prompt)
        self.assertIn("## Editorial Risks", prompt)

    def test_outline_to_article_prompt_enforces_length_and_fidelity(self):
        video = Video(
            title="Interview",
            video_id="vid",
            channel="Channel",
            url="https://example.com",
            description="Description",
        )
        transcript = Transcript(video_id="vid", text="Transcript", source="test")

        prompt = build_article_from_outline_prompt(video, transcript, "## Core Arguments\nA", 3000, 5000)

        self.assertIn("Target 3000-5000 words", prompt)
        self.assertIn("Each major section should be 350-550 words", prompt)
        self.assertIn("The editorial brief controls structure; the transcript controls facts", prompt)
        self.assertIn("Do not add new arguments", prompt)

    def test_expansion_prompt_requires_body_expansion(self):
        video = Video(
            title="Interview",
            video_id="vid",
            channel="Channel",
            url="https://example.com",
            description="Description",
        )
        transcript = Transcript(video_id="vid", text="Transcript", source="test")

        prompt = build_article_expansion_prompt(
            video=video,
            transcript=transcript,
            outline="## Core Arguments\nA",
            draft="# Short\n\nToo short.",
            current_words=2,
            min_words=3000,
            max_words=5000,
        )

        self.assertIn("too short", prompt)
        self.assertIn("Do not merely add a conclusion", prompt)
        self.assertIn("complete revised article", prompt)


if __name__ == "__main__":
    unittest.main()
