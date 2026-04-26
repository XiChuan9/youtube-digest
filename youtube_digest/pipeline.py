"""Digest pipeline orchestration."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from youtube_digest.config import DigestConfig, load_config
from youtube_digest.discovery.youtube import YouTubeDiscovery
from youtube_digest.llm.anthropic_writer import AnthropicArticleWriter
from youtube_digest.models import Article, DigestResult, Transcript, Video
from youtube_digest.processing.prompts import (
    build_article_expansion_prompt,
    build_article_from_outline_prompt,
    build_article_prompt,
    build_transcript_analysis_prompt,
)
from youtube_digest.processing.metrics import estimate_word_count
from youtube_digest.storage.artifacts import ArtifactStore
from youtube_digest.storage.sqlite import DigestStore
from youtube_digest.transcripts.supadata import SupadataTranscriptProvider


LogFn = Callable[[str], None]


def default_job_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _noop(_: str) -> None:
    return None


def build_discovery(config: DigestConfig) -> YouTubeDiscovery:
    return YouTubeDiscovery.from_config(config)


def build_transcript_provider(config: DigestConfig) -> SupadataTranscriptProvider:
    if config.transcript.provider != "supadata":
        raise ValueError(f"Unsupported transcript provider: {config.transcript.provider}")
    return SupadataTranscriptProvider.from_config(config)


def build_writer(config: DigestConfig):
    if config.llm.provider == "anthropic":
        return AnthropicArticleWriter.from_config(config)
    if config.llm.provider in {"openai", "openai_compatible", "openrouter", "deepseek"}:
        from youtube_digest.llm.openai_compatible_writer import OpenAICompatibleArticleWriter

        return OpenAICompatibleArticleWriter.from_config(config)
    if config.llm.provider == "gemini":
        from youtube_digest.llm.gemini_writer import GeminiArticleWriter

        return GeminiArticleWriter.from_config(config)
    raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")


def run_digest(
    config_path: Optional[str] = None,
    mode: Optional[str] = None,
    video_url: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    limit: Optional[int] = None,
    send_email: bool = False,
    log: Optional[LogFn] = None,
    discovery: Optional[YouTubeDiscovery] = None,
    transcript_provider: Optional[SupadataTranscriptProvider] = None,
    writer: Optional[AnthropicArticleWriter] = None,
    store: Optional[DigestStore] = None,
    artifacts: Optional[ArtifactStore] = None,
) -> DigestResult:
    logger = log or _noop
    config = load_config(config_path)
    selected_mode = mode or config.default_mode
    job_id = default_job_id()

    artifact_store = artifacts or ArtifactStore(config.output.artifacts_dir)
    db_path = Path(config.output.artifacts_dir) / "digest.sqlite3"
    digest_store = store or DigestStore(str(db_path))
    result = DigestResult(
        job_id=job_id,
        mode=selected_mode,
        status="running",
        videos_found=0,
        videos_selected=0,
    )

    digest_store.start_job(job_id, selected_mode)

    try:
        video_discovery = discovery or build_discovery(config)
        if video_url:
            logger("Selecting explicit video...")
            videos = [video_discovery.get_video_from_url(video_url)]
        else:
            logger("Discovering videos...")
            videos = video_discovery.discover(config.youtube.channels)
        result.videos_found = len(videos)

        new_videos: List[Video] = digest_store.filter_new(videos, force=force)
        max_items = limit or config.max_videos_per_run
        new_videos = new_videos[:max_items]
        result.videos_selected = len(new_videos)

        job_dir = artifact_store.job_dir(job_id)
        result.artifacts["job_dir"] = str(job_dir)
        artifact_store.write_json(job_dir / "selected_videos.json", {"videos": [v.to_dict() for v in new_videos]})

        if dry_run:
            result.status = "dry_run"
            digest_store.finish_job(job_id, "dry_run")
            return result

        if not new_videos:
            result.status = "no_new_videos"
            digest_store.finish_job(job_id, "no_new_videos")
            return result

        transcript_fetcher = transcript_provider or build_transcript_provider(config)
        article_writer = writer or build_writer(config)

        for video in new_videos:
            logger(f"Processing {video.channel}: {video.title}")
            video_dir = artifact_store.video_dir(job_id, video.video_id)
            artifact_store.write_json(video_dir / "video.json", video.to_dict())

            try:
                transcript: Transcript = transcript_fetcher.fetch(video)
                artifact_store.write_text(video_dir / "raw_transcript.txt", transcript.text)
                artifact_store.write_json(video_dir / "transcript.json", transcript.to_dict())

                if selected_mode == "magazine" and config.content.magazine_two_pass:
                    analysis_prompt = build_transcript_analysis_prompt(
                        video,
                        transcript,
                        config.content.analysis_min_words,
                        config.content.analysis_max_words,
                    )
                    artifact_store.write_text(video_dir / "analysis_prompt.md", analysis_prompt)
                    analysis = article_writer.write(analysis_prompt)
                    artifact_store.write_text(video_dir / "analysis.md", analysis)
                    prompt = build_article_from_outline_prompt(
                        video,
                        transcript,
                        analysis,
                        config.content.magazine_min_words,
                        config.content.magazine_max_words,
                        config.content.magazine_section_min_words,
                        config.content.magazine_section_max_words,
                        config.content.magazine_min_sections,
                        config.content.magazine_max_sections,
                    )
                else:
                    analysis = ""
                    prompt = build_article_prompt(
                        video,
                        transcript,
                        selected_mode,
                        config.content.magazine_min_words,
                        config.content.magazine_max_words,
                    )
                artifact_store.write_text(video_dir / "prompt.md", prompt)
                article_markdown = article_writer.write(prompt)
                artifact_store.write_text(video_dir / "article_draft.md", article_markdown)

                if selected_mode == "magazine":
                    article_markdown = expand_short_magazine_article(
                        video=video,
                        transcript=transcript,
                        outline=analysis,
                        draft=article_markdown,
                        writer=article_writer,
                        artifact_store=artifact_store,
                        video_dir=video_dir,
                        min_words=config.content.magazine_min_words,
                        max_words=config.content.magazine_max_words,
                        section_min_words=config.content.magazine_section_min_words,
                        section_max_words=config.content.magazine_section_max_words,
                        max_passes=config.content.magazine_expansion_passes,
                    )
                article = Article(
                    video_id=video.video_id,
                    title=video.title,
                    channel=video.channel,
                    url=video.url,
                    mode=selected_mode,
                    markdown=article_markdown,
                    model=getattr(article_writer, "model_name", config.llm.model),
                    source_title=video.title,
                    source_published_at=video.published_at,
                    transcript_source=transcript.source,
                    transcript_language=transcript.language,
                )
                artifact_store.write_text(video_dir / "article.md", article.markdown)
                artifact_store.write_json(video_dir / "article.json", article.to_dict())
                result.articles.append(article)
            except Exception as exc:
                message = f"{video.video_id}: {exc}"
                result.errors.append(message)
                artifact_store.write_text(video_dir / "error.txt", message)

        if not result.articles:
            result.status = "no_articles"
            digest_store.finish_job(job_id, "no_articles", "; ".join(result.errors))
            return result

        from youtube_digest.ebook.epub_builder import create_epub

        epub_path = job_dir / f"youtube_digest_{job_id}.epub"
        result.artifacts["epub"] = create_epub(result.articles, str(epub_path))
        from youtube_digest.delivery.archive import save_newsletter_archive

        result.artifacts["archive_manifest"] = save_newsletter_archive(
            config.output.archive_dir,
            result.articles,
            result.artifacts["epub"],
        )

        if send_email or config.delivery.email_enabled:
            from youtube_digest.delivery.email import send_email as send_digest_email

            logger("Sending email...")
            send_digest_email(config, result.articles, result.artifacts["epub"])

        for article in result.articles:
            matching_video = next((video for video in new_videos if video.video_id == article.video_id), None)
            if matching_video:
                digest_store.mark_processed(matching_video)

        result.status = "succeeded" if not result.errors else "partial_success"
        manifest_path = job_dir / "manifest.json"
        result.artifacts["manifest"] = artifact_store.write_json(manifest_path, result.to_dict())
        digest_store.finish_job(job_id, result.status, "; ".join(result.errors))
        return result
    except Exception as exc:
        result.status = "failed"
        result.errors.append(str(exc))
        digest_store.finish_job(job_id, "failed", str(exc))
        return result


def result_to_json(result: DigestResult, include_article_markdown: bool = False) -> str:
    return json.dumps(
        result.to_dict(include_article_markdown=include_article_markdown),
        indent=2,
        ensure_ascii=False,
    )


def expand_short_magazine_article(
    video: Video,
    transcript: Transcript,
    outline: str,
    draft: str,
    writer,
    artifact_store: ArtifactStore,
    video_dir: Path,
    min_words: int,
    max_words: int,
    section_min_words: int,
    section_max_words: int,
    max_passes: int,
) -> str:
    article = draft
    threshold = int(min_words * 0.85)

    for pass_number in range(1, max_passes + 1):
        current_words = estimate_word_count(article)
        artifact_store.write_text(video_dir / f"word_count_pass_{pass_number - 1}.txt", str(current_words))
        if current_words >= threshold:
            return article

        expansion_prompt = build_article_expansion_prompt(
            video=video,
            transcript=transcript,
            outline=outline,
            draft=article,
            current_words=current_words,
            min_words=min_words,
            max_words=max_words,
            section_min_words=section_min_words,
            section_max_words=section_max_words,
        )
        artifact_store.write_text(video_dir / f"expansion_prompt_{pass_number}.md", expansion_prompt)
        article = writer.write(expansion_prompt)
        artifact_store.write_text(video_dir / f"article_expanded_{pass_number}.md", article)

    artifact_store.write_text(video_dir / "word_count_final.txt", str(estimate_word_count(article)))
    return article
