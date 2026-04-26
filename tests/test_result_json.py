import json
import unittest

from youtube_digest.models import Article, DigestResult
from youtube_digest.pipeline import result_to_json


class ResultJsonTests(unittest.TestCase):
    def test_json_output_omits_article_markdown_by_default(self):
        result = DigestResult(
            job_id="job",
            mode="magazine",
            status="succeeded",
            videos_found=1,
            videos_selected=1,
            articles=[
                Article(
                    video_id="vid",
                    title="Title",
                    channel="Channel",
                    url="https://example.com",
                    mode="magazine",
                    markdown="# Full Article",
                )
            ],
        )

        data = json.loads(result_to_json(result))

        self.assertNotIn("markdown", data["articles"][0])

    def test_json_output_can_include_article_markdown(self):
        result = DigestResult(
            job_id="job",
            mode="magazine",
            status="succeeded",
            videos_found=1,
            videos_selected=1,
            articles=[
                Article(
                    video_id="vid",
                    title="Title",
                    channel="Channel",
                    url="https://example.com",
                    mode="magazine",
                    markdown="# Full Article",
                )
            ],
        )

        data = json.loads(result_to_json(result, include_article_markdown=True))

        self.assertEqual(data["articles"][0]["markdown"], "# Full Article")


if __name__ == "__main__":
    unittest.main()
