"""Command line interface for YouTube Digest."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from youtube_digest.config import DigestConfig, init_config, load_config, save_config
from youtube_digest.errors import error_detail_from_exception
from youtube_digest.pipeline import result_to_json, run_digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="youtube-digest")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a starter config file")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing config")

    generate = subparsers.add_parser("generate", help="Generate a digest")
    generate.add_argument("--mode", choices=["faithful", "magazine", "summary"], help="Content mode")
    generate.add_argument("--video-url", help="Process a single YouTube video URL instead of configured channels")
    generate.add_argument("--dry-run", action="store_true", help="Discover and select videos without paid APIs")
    generate.add_argument("--force", action="store_true", help="Process videos even if already marked processed")
    generate.add_argument("--limit", type=int, help="Maximum videos to process in this run")
    generate.add_argument("--reuse-transcript", action="store_true", help="Reuse the latest transcript artifact for a video")
    generate.add_argument("--reuse-analysis", action="store_true", help="Reuse the latest analysis artifact for a video")
    generate.add_argument("--send-email", action="store_true", help="Send the generated EPUB by email")
    generate.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    generate.add_argument(
        "--include-content",
        action="store_true",
        help="Include full article markdown in JSON output. Artifact files always keep the content.",
    )

    channels = subparsers.add_parser("channels", help="Manage channels in config")
    channel_subparsers = channels.add_subparsers(dest="channels_command", required=True)
    channel_subparsers.add_parser("list", help="List configured channels")
    add = channel_subparsers.add_parser("add", help="Add a channel handle")
    add.add_argument("handle")
    remove = channel_subparsers.add_parser("remove", help="Remove a channel handle")
    remove.add_argument("handle")

    return parser


def normalize_handle(handle: str) -> str:
    value = handle.strip()
    if not value:
        raise ValueError("channel handle cannot be empty")
    if "youtube.com/channel/" in value:
        return value.split("youtube.com/channel/", 1)[1].split("/", 1)[0]
    if "youtube.com/@" in value:
        value = value.split("youtube.com/@", 1)[1].split("/", 1)[0]
    if value.startswith("UC"):
        return value
    return value if value.startswith("@") else f"@{value}"


def load_or_default_config(path: str) -> DigestConfig:
    if Path(path).exists():
        return load_config(path)
    return DigestConfig()


def handle_init(args: argparse.Namespace) -> int:
    path = Path(args.config)
    if path.exists() and args.force:
        save_config(DigestConfig(), str(path))
        print(f"Rewrote {path}")
        return 0

    created = init_config(str(path))
    if created:
        print(f"Created {path}")
    else:
        print(f"{path} already exists")
    return 0


def handle_channels(args: argparse.Namespace) -> int:
    config = load_or_default_config(args.config)

    if args.channels_command == "list":
        for channel in config.youtube.channels:
            print(channel)
        return 0

    handle = normalize_handle(args.handle)

    if args.channels_command == "add":
        if handle not in config.youtube.channels:
            config.youtube.channels.append(handle)
            save_config(config, args.config)
            print(f"Added {handle}")
        else:
            print(f"{handle} already exists")
        return 0

    if args.channels_command == "remove":
        if handle in config.youtube.channels:
            config.youtube.channels.remove(handle)
            save_config(config, args.config)
            print(f"Removed {handle}")
        else:
            print(f"{handle} was not configured")
        return 0

    return 1


def handle_generate(args: argparse.Namespace) -> int:
    logs: List[str] = []

    def log(message: str) -> None:
        logs.append(message)
        if not args.json:
            print(message)

    result = run_digest(
        config_path=args.config,
        mode=args.mode,
        video_url=args.video_url,
        dry_run=args.dry_run,
        force=args.force,
        limit=args.limit,
        send_email=args.send_email,
        reuse_transcript=args.reuse_transcript,
        reuse_analysis=args.reuse_analysis,
        log=log,
    )

    if args.json:
        print(result_to_json(result, include_article_markdown=args.include_content))
    else:
        print(f"Status: {result.status}")
        print(f"Videos found: {result.videos_found}")
        print(f"Videos selected: {result.videos_selected}")
        if result.artifacts.get("epub"):
            print(f"EPUB: {result.artifacts['epub']}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"- {error}")

    return 0 if result.status in {"succeeded", "partial_success", "dry_run", "no_new_videos"} else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return handle_init(args)
        if args.command == "channels":
            return handle_channels(args)
        if args.command == "generate":
            return handle_generate(args)
    except Exception as exc:
        if getattr(args, "json", False):
            detail = error_detail_from_exception(exc, stage="config", default_code="config_error")
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "errors": [str(exc)],
                        "error_details": [detail.to_dict()],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
