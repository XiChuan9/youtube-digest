import unittest

from youtube_digest.config import DigestConfig
from youtube_digest.llm.openai_compatible_writer import OpenAICompatibleArticleWriter


class LLMProviderConfigTests(unittest.TestCase):
    def test_openrouter_provider_uses_openrouter_base_url_default(self):
        config = DigestConfig()
        config.llm.provider = "openrouter"
        config.llm.api_key_env = "OPENROUTER_API_KEY"
        config.llm.model = "openai/gpt-4o-mini"

        # Avoid requiring a real environment variable in this unit test.
        writer = OpenAICompatibleArticleWriter(
            api_key="test",
            model=config.llm.model,
            base_url="https://openrouter.ai/api/v1",
        )

        self.assertEqual(writer.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(writer.model_name, "openai/gpt-4o-mini")


if __name__ == "__main__":
    unittest.main()
