"""Archive generated newsletters for later inspection."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable

from youtube_digest.delivery.naming import digest_filename
from youtube_digest.ebook.html_builder import create_newsletter_html
from youtube_digest.models import Article


def save_newsletter_archive(archive_dir: str, articles: Iterable[Article], epub_path: str) -> str:
    article_list = list(articles)
    path = Path(archive_dir)
    path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_name = digest_filename("youtube-digest", timestamp, article_list, "html")
    epub_name = digest_filename("youtube-digest", timestamp, article_list, "epub")
    metadata_name = digest_filename("youtube-digest", timestamp, article_list, "json")

    html_path = path / html_name
    epub_archive_path = path / epub_name
    metadata_path = path / metadata_name

    html_path.write_text(create_newsletter_html(article_list), encoding="utf-8")
    shutil.copy(epub_path, epub_archive_path)

    metadata = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "timestamp": timestamp,
        "article_count": len(article_list),
        "channels": [article.channel for article in article_list],
        "titles": [article.title for article in article_list],
        "html_file": html_name,
        "epub_file": epub_name,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(metadata_path)
