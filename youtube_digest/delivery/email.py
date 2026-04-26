"""Email delivery."""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable, Optional

from youtube_digest.config import DigestConfig, require_env, resolve_env
from youtube_digest.ebook.html_builder import create_newsletter_html
from youtube_digest.models import Article


def send_email(
    config: DigestConfig,
    articles: Iterable[Article],
    epub_path: str,
    recipient_email: Optional[str] = None,
) -> None:
    gmail_address = require_env(config.delivery.gmail_address_env, "Gmail address")
    gmail_password = require_env(config.delivery.gmail_app_password_env, "Gmail app password")
    recipient = recipient_email or resolve_env(config.delivery.recipient_email_env) or gmail_address

    article_list = list(articles)
    msg = MIMEMultipart("mixed")
    msg["Subject"] = "Your YouTube Digest"
    msg["From"] = gmail_address
    msg["To"] = recipient

    body = MIMEMultipart("alternative")
    text_content = "Your YouTube Digest\n\n"

    for article in article_list:
        text_content += f"{article.channel}: {article.title}\n{article.url}\n\n{article.markdown}\n\n"
    body.attach(MIMEText(text_content, "plain"))
    body.attach(MIMEText(create_newsletter_html(article_list), "html"))
    msg.attach(body)

    path = Path(epub_path)
    with path.open("rb") as attachment:
        part = MIMEBase("application", "epub+zip")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(epub_path)}")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())
