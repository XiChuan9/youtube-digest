"""Optional smoke tests for real external APIs.

This script is intentionally not part of the default unit test suite. It calls
real services when the corresponding environment variables are present.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from youtube_digest.config import save_config, DigestConfig, load_dotenv_if_available
from youtube_digest.discovery.youtube import YouTubeDiscovery, parse_youtube_video_id
from youtube_digest.models import Transcript, Video
from youtube_digest.processing.prompts import build_article_prompt
from youtube_digest.pipeline import build_writer
from youtube_digest.transcripts.supadata import SupadataTranscriptProvider


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"SKIP: {name} is not set")
        raise SystemExit(0)
    return value


def video_from_url(url: str) -> Video:
    video_id = parse_youtube_video_id(url)
    return Video(
        title="Smoke test video",
        video_id=video_id,
        channel="Smoke",
        url=url,
        description="Smoke test fixture for external API verification.",
    )


def run_discovery() -> None:
    api_key = require_env("YOUTUBE_API_KEY")
    discovery = YouTubeDiscovery(api_key=api_key, lookback_items_per_channel=3, videos_per_channel=1)
    videos = discovery.discover(["UCYO_jab_esuFRV4b17AJtAw"])
    print(json.dumps({"stage": "discovery", "videos_found": len(videos), "videos": [v.to_dict() for v in videos]}, indent=2))


def run_transcript(video_url: str) -> Transcript:
    api_key = require_env("SUPADATA_API_KEY")
    provider = SupadataTranscriptProvider(api_key=api_key, native_transcripts_only=True)
    transcript = provider.fetch(video_from_url(video_url))
    print(json.dumps({"stage": "transcript", "word_count": len(transcript.text.split()), "language": transcript.language}, indent=2))
    return transcript


def run_full(video_url: str) -> None:
    config = DigestConfig()
    apply_llm_env_overrides(config)
    require_env(config.llm.api_key_env)

    video = video_from_url(video_url)
    transcript = run_transcript(video_url)
    # Keep the smoke prompt small. This validates provider wiring without making
    # an expensive long-read generation call.
    short_transcript = Transcript(
        video_id=transcript.video_id,
        text=" ".join(transcript.text.split()[:800]),
        source=transcript.source,
        language=transcript.language,
        is_generated=transcript.is_generated,
    )
    writer = build_writer(config)
    prompt = build_article_prompt(video, short_transcript, "summary")
    article = writer.write(prompt)
    print(json.dumps({"stage": "full", "provider": config.llm.provider, "model": config.llm.model, "article_chars": len(article), "preview": article[:240]}, indent=2))


def apply_llm_env_overrides(config: DigestConfig) -> None:
    provider = os.getenv("YOUTUBE_DIGEST_LLM_PROVIDER")
    model = os.getenv("YOUTUBE_DIGEST_LLM_MODEL")
    base_url = os.getenv("YOUTUBE_DIGEST_LLM_BASE_URL")
    api_key_env = os.getenv("YOUTUBE_DIGEST_LLM_API_KEY_ENV")

    if provider:
        config.llm.provider = provider
    if model:
        config.llm.model = model
    if base_url:
        config.llm.base_url = base_url
    if api_key_env:
        config.llm.api_key_env = api_key_env


def main() -> int:
    load_dotenv_if_available()

    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["discovery", "transcript", "full"], default="discovery")
    parser.add_argument("--video-url", default="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        config = DigestConfig()
        apply_llm_env_overrides(config)
        config.output.artifacts_dir = str(Path(tmp) / "artifacts")
        config.output.archive_dir = str(Path(tmp) / "newsletters")
        save_config(config, str(Path(tmp) / "config.json"))

        if args.stage == "discovery":
            run_discovery()
        elif args.stage == "transcript":
            run_transcript(args.video_url)
        else:
            run_full(args.video_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
