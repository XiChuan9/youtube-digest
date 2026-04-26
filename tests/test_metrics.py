import unittest

from youtube_digest.processing.metrics import estimate_word_count


class MetricsTests(unittest.TestCase):
    def test_estimate_word_count_counts_english_words(self):
        self.assertEqual(estimate_word_count("Hello world, this is a test."), 6)

    def test_estimate_word_count_counts_cjk_chars(self):
        self.assertEqual(estimate_word_count("你好世界"), 4)


if __name__ == "__main__":
    unittest.main()
