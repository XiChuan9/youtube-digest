"""LLM interface."""


class ArticleWriter:
    provider_name = "unknown"

    @property
    def model_name(self) -> str:
        return "unknown"

    def write(self, prompt: str) -> str:
        raise NotImplementedError
