import unittest

from youtube_digest.delivery.naming import digest_descriptor, digest_filename
from youtube_digest.models import Article


def article(title, channel, video_id):
    return Article(
        video_id=video_id,
        title=title,
        channel=channel,
        url=f"https://youtube.com/watch?v={video_id}",
        mode="magazine",
        markdown="# Article",
    )


class DigestNamingTests(unittest.TestCase):
    def test_single_video_filename_includes_channel_and_title(self):
        result = digest_filename(
            "youtube-digest",
            "20260426T024252Z",
            [article("How to Run with Perfect Form | Athlete Analysis", "Steve Magness", "MHRLeiGGsG0")],
            "epub",
        )

        self.assertEqual(
            result,
            "youtube-digest_20260426T024252Z_steve-magness_how-to-run-with-perfect-form-athlete-analysis.epub",
        )

    def test_multi_video_descriptor_includes_count_and_channels(self):
        descriptor = digest_descriptor(
            [
                article("One", "Latent Space", "one"),
                article("Two", "Y Combinator", "two"),
                article("Three", "Steve Magness", "three"),
                article("Four", "Another Channel", "four"),
            ]
        )

        self.assertEqual(descriptor, "4-videos_latent-space-y-combinator-steve-magness")


if __name__ == "__main__":
    unittest.main()
