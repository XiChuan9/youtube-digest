"""Backward-compatible EPUB, archive, and email helpers."""

from datetime import datetime
from pathlib import Path

from youtube_digest.config import load_config
from youtube_digest.delivery.archive import save_newsletter_archive as save_core_archive
from youtube_digest.delivery.email import send_email
from youtube_digest.ebook.epub_builder import create_epub as create_core_epub
from youtube_digest.ebook.html_builder import create_newsletter_html as create_core_html
from youtube_digest.models import Article


def _legacy_to_article(article):
    return Article(
        video_id=article.get("video_id") or article.get("url", ""),
        title=article["title"],
        channel=article["channel"],
        url=article["url"],
        mode=article.get("mode", "magazine"),
        markdown=article.get("article", article.get("markdown", "")),
        model=article.get("model"),
        source_title=article.get("source_title", article.get("title")),
        source_published_at=article.get("source_published_at"),
        transcript_source=article.get("transcript_source"),
        transcript_language=article.get("transcript_language"),
    )


def _legacy_articles(articles):
    return [_legacy_to_article(article) for article in articles]


def create_epub(articles):
    filename = f"youtube_digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub"
    path = Path(filename)
    return create_core_epub(_legacy_articles(articles), str(path))


def create_newsletter_html(articles):
    return create_core_html(_legacy_articles(articles))


def save_newsletter_archive(html_content, epub_path, articles):
    config = load_config()
    return save_core_archive(config.output.archive_dir, _legacy_articles(articles), epub_path)


def send_newsletter(articles, recipient_email=None):
    if not articles:
        print("No articles to send!")
        return False

    config = load_config()
    article_models = _legacy_articles(articles)

    try:
        epub_path = create_core_epub(
            article_models,
            f"youtube_digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub",
        )
        save_core_archive(config.output.archive_dir, article_models, epub_path)
        send_email(config, article_models, epub_path, recipient_email=recipient_email)
        print("✓ Newsletter sent successfully with EPUB attachment!")
        return True
    except Exception as exc:
        print(f"! Failed to send email: {exc}")
        return False


if __name__ == "__main__":
    print("Use `python -m youtube_digest generate --send-email` to send a digest.")
