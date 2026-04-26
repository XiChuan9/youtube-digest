"""Digest pipeline orchestration."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from youtube_digest.config import DigestConfig, load_config
from youtube_digest.delivery.naming import digest_filename
from youtube_digest.discovery.youtube import YouTubeDiscovery
from youtube_digest.errors import error_detail_from_exception
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


def _append_error(
    result: DigestResult,
    exc: Exception,
    stage: str,
    video_id: Optional[str] = None,
    provider: Optional[str] = None,
    default_code: str = "unknown_error",
) -> None:
    detail = error_detail_from_exception(
        exc,
        stage=stage,
        video_id=video_id,
        provider=provider,
        default_code=default_code,
    )
    message = detail.message
    if detail.video_id:
        message = f"{detail.video_id}: {message}"
    result.errors.append(message)
    result.error_details.append(detail)


def _load_transcript_from_artifact(video_dir: Path, video: Video) -> Transcript:
    data = json.loads((video_dir / "transcript.json").read_text(encoding="utf-8"))
    text = data.get("text") or (video_dir / "raw_transcript.txt").read_text(encoding="utf-8")
    kwargs = {
        "video_id": data.get("video_id") or video.video_id,
        "text": text,
        "source": data.get("source") or "artifact",
        "language": data.get("language"),
        "is_generated": bool(data.get("is_generated", False)),
    }
    if data.get("fetched_at"):
        kwargs["fetched_at"] = data["fetched_at"]
    return Transcript(**kwargs)


def _record_reuse(
    artifact_store: ArtifactStore,
    job_dir: Path,
    reuse_manifest: Dict[str, List[Dict[str, object]]],
    video_id: str,
    kind: str,
    source_dir: Path,
    destination_dir: Path,
    files: Dict[str, Dict[str, str]],
) -> None:
    reuse_manifest["reused"].append(
        {
            "video_id": video_id,
            "kind": kind,
            "source_dir": str(source_dir),
            "destination_dir": str(destination_dir),
            "files": [
                {
                    "name": filename,
                    "source": paths["source"],
                    "destination": paths["destination"],
                }
                for filename, paths in files.items()
            ],
        }
    )
    artifact_store.write_json(job_dir / "reuse.json", reuse_manifest)


def run_digest(
    config_path: Optional[str] = None,
    mode: Optional[str] = None,
    video_url: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    limit: Optional[int] = None,
    send_email: bool = False,
    reuse_transcript: bool = False,
    reuse_analysis: bool = False,
    log: Optional[LogFn] = None,
    discovery: Optional[YouTubeDiscovery] = None,
    transcript_provider: Optional[SupadataTranscriptProvider] = None,
    writer: Optional[AnthropicArticleWriter] = None,
    store: Optional[DigestStore] = None,
    artifacts: Optional[ArtifactStore] = None,
) -> DigestResult:
    logger = log or _noop
    job_id = default_job_id()

    try:
        config = load_config(config_path)
    except Exception as exc:
        result = DigestResult(
            job_id=job_id,
            mode=mode or "unknown",
            status="failed",
            videos_found=0,
            videos_selected=0,
        )
        _append_error(result, exc, stage="config", default_code="config_error")
        return result

    selected_mode = mode or config.default_mode
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
    current_stage = "discovery"
    current_provider = "youtube"
    current_video_id = None

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
        reuse_manifest: Dict[str, List[Dict[str, object]]] = {"reused": []}
        artifact_store.write_json(job_dir / "reuse.json", reuse_manifest)

        if dry_run:
            result.status = "dry_run"
            digest_store.finish_job(job_id, "dry_run")
            return result

        if not new_videos:
            result.status = "no_new_videos"
            digest_store.finish_job(job_id, "no_new_videos")
            return result

        transcript_fetcher = transcript_provider
        article_writer = writer

        def get_transcript_fetcher():
            nonlocal transcript_fetcher
            if transcript_fetcher is None:
                transcript_fetcher = build_transcript_provider(config)
            return transcript_fetcher

        def get_article_writer():
            nonlocal article_writer
            if article_writer is None:
                article_writer = build_writer(config)
            return article_writer

        for video in new_videos:
            logger(f"Processing {video.channel}: {video.title}")
            current_video_id = video.video_id
            video_dir = artifact_store.video_dir(job_id, video.video_id)
            artifact_store.write_json(video_dir / "video.json", video.to_dict())
            video_stage = "transcript"
            video_provider = config.transcript.provider

            try:
                transcript: Optional[Transcript] = None
                if reuse_transcript:
                    source_dir = artifact_store.latest_video_dir(
                        video.video_id,
                        required_files=("raw_transcript.txt", "transcript.json"),
                        exclude_job_id=job_id,
                    )
                    if source_dir:
                        copied_files = artifact_store.copy_files(
                            source_dir,
                            video_dir,
                            ("raw_transcript.txt", "transcript.json"),
                        )
                        transcript = _load_transcript_from_artifact(video_dir, video)
                        _record_reuse(
                            artifact_store,
                            job_dir,
                            reuse_manifest,
                            video.video_id,
                            "transcript",
                            source_dir,
                            video_dir,
                            copied_files,
                        )

                if transcript is None:
                    transcript = get_transcript_fetcher().fetch(video)
                    artifact_store.write_text(video_dir / "raw_transcript.txt", transcript.text)
                    artifact_store.write_json(video_dir / "transcript.json", transcript.to_dict())

                if selected_mode == "magazine" and config.content.magazine_two_pass:
                    analysis: Optional[str] = None
                    if reuse_analysis:
                        source_dir = artifact_store.latest_video_dir(
                            video.video_id,
                            required_files=("analysis.md",),
                            exclude_job_id=job_id,
                        )
                        if source_dir:
                            copied_files = artifact_store.copy_files(source_dir, video_dir, ("analysis.md",))
                            analysis = (video_dir / "analysis.md").read_text(encoding="utf-8")
                            _record_reuse(
                                artifact_store,
                                job_dir,
                                reuse_manifest,
                                video.video_id,
                                "analysis",
                                source_dir,
                                video_dir,
                                copied_files,
                            )

                    if analysis is None:
                        video_stage = "analysis"
                        video_provider = config.llm.provider
                        analysis_prompt = build_transcript_analysis_prompt(
                            video,
                            transcript,
                            config.content.analysis_min_words,
                            config.content.analysis_max_words,
                        )
                        artifact_store.write_text(video_dir / "analysis_prompt.md", analysis_prompt)
                        analysis = get_article_writer().write(analysis_prompt)
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
                video_stage = "writing"
                video_provider = config.llm.provider
                article_markdown = get_article_writer().write(prompt)
                artifact_store.write_text(video_dir / "article_draft.md", article_markdown)

                if selected_mode == "magazine":
                    video_stage = "expansion"
                    article_markdown = expand_short_magazine_article(
                        video=video,
                        transcript=transcript,
                        outline=analysis,
                        draft=article_markdown,
                        writer=get_article_writer(),
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
                    model=getattr(get_article_writer(), "model_name", config.llm.model),
                    source_title=video.title,
                    source_published_at=video.published_at,
                    transcript_source=transcript.source,
                    transcript_language=transcript.language,
                )
                artifact_store.write_text(video_dir / "article.md", article.markdown)
                artifact_store.write_json(video_dir / "article.json", article.to_dict())
                result.articles.append(article)
            except Exception as exc:
                _append_error(result, exc, stage=video_stage, video_id=video.video_id, provider=video_provider)
                message = result.errors[-1]
                artifact_store.write_text(video_dir / "error.txt", message)

        if not result.articles:
            result.status = "no_articles"
            digest_store.finish_job(job_id, "no_articles", "; ".join(result.errors))
            return result

        from youtube_digest.ebook.epub_builder import create_epub

        current_stage = "epub"
        current_provider = None
        current_video_id = None
        epub_path = job_dir / digest_filename("youtube-digest", job_id, result.articles, "epub")
        result.artifacts["epub"] = create_epub(result.articles, str(epub_path))
        from youtube_digest.delivery.archive import save_newsletter_archive

        current_stage = "archive"
        result.artifacts["archive_manifest"] = save_newsletter_archive(
            config.output.archive_dir,
            result.articles,
            result.artifacts["epub"],
        )

        if send_email or config.delivery.email_enabled:
            from youtube_digest.delivery.email import send_email as send_digest_email

            current_stage = "email"
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
        _append_error(
            result,
            exc,
            stage=current_stage,
            video_id=current_video_id,
            provider=current_provider,
            default_code="epub_generation_failed" if current_stage == "epub" else "unknown_error",
        )
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
