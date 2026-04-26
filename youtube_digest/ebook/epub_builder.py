"""EPUB generation."""

import html
from datetime import datetime
from pathlib import Path
from typing import Iterable

from youtube_digest.models import Article


def _metadata_value(value):
    return html.escape(str(value)) if value else "Unknown"


def build_source_notes(article: Article) -> str:
    source_title = _metadata_value(article.source_title or article.title)
    channel = _metadata_value(article.channel)
    source_url = html.escape(article.url)
    mode = _metadata_value(article.mode)
    model = _metadata_value(article.model)
    generated_at = _metadata_value(article.generated_at)
    transcript_source = _metadata_value(article.transcript_source)
    transcript_language = _metadata_value(article.transcript_language)
    published_at = _metadata_value(article.source_published_at)

    return f"""
    <section class="source-notes">
        <h2>Source Notes</h2>
        <dl>
            <dt>Original title</dt><dd>{source_title}</dd>
            <dt>Channel</dt><dd>{channel}</dd>
            <dt>Original video</dt><dd><a href="{source_url}">{source_url}</a></dd>
            <dt>Published at</dt><dd>{published_at}</dd>
            <dt>Digest mode</dt><dd>{mode}</dd>
            <dt>Model</dt><dd>{model}</dd>
            <dt>Transcript source</dt><dd>{transcript_source}</dd>
            <dt>Transcript language</dt><dd>{transcript_language}</dd>
            <dt>Generated at</dt><dd>{generated_at}</dd>
        </dl>
    </section>
    """


def create_epub(articles: Iterable[Article], output_path: str) -> str:
    import markdown
    from ebooklib import epub

    article_list = list(articles)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%B %d, %Y")
    book = epub.EpubBook()
    book.set_identifier(f"youtube-digest-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    book.set_title(f"YouTube Digest - {today}")
    book.set_language("en")
    book.add_author("YouTube Digest")

    style = """
    body { font-family: Georgia, serif; line-height: 1.65; padding: 1em; }
    h1 { font-size: 1.5em; border-bottom: 1px solid #ccc; padding-bottom: 0.3em; }
    h2 { font-size: 1.25em; margin-top: 1.2em; }
    h3 { font-size: 1.1em; margin-top: 1em; }
    .intro { background: #f5f5f5; padding: 1em; border-left: 3px solid #666; margin-bottom: 1.5em; }
    .watch-link { margin-top: 1.5em; padding: 0.5em; background: #f0f0f0; display: block; }
    .source-notes { margin-top: 2em; padding-top: 1em; border-top: 1px solid #ccc; font-size: 0.9em; color: #444; }
    .source-notes dl { display: block; }
    .source-notes dt { font-weight: bold; margin-top: 0.6em; }
    .source-notes dd { margin-left: 0; }
    """
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )
    book.add_item(nav_css)

    chapters = []
    for i, article in enumerate(article_list, start=1):
        article_html = markdown.markdown(article.markdown, extensions=["extra"])
        source_title = html.escape(article.title)
        source_channel = html.escape(article.channel)
        source_url = html.escape(article.url)

        chapter = epub.EpubHtml(
            title=article.title[:50],
            file_name=f"chapter_{i}.xhtml",
            lang="en",
        )
        chapter.content = f"""
        <html>
        <head><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
        <body>
            <div class="intro">
                <p><em>Based on "{source_title}" from <strong>{source_channel}</strong>.</em></p>
            </div>
            {article_html}
            {build_source_notes(article)}
        </body>
        </html>
        """
        chapter.add_item(nav_css)
        book.add_item(chapter)
        chapters.append(chapter)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters
    epub.write_epub(str(path), book)
    return str(path)
