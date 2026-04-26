# Changelog

All notable changes to this project will be documented in this file.

This project follows a pragmatic pre-1.0 changelog format. Dates use
YYYY-MM-DD.

## [Unreleased]

- Added a productized `youtube_digest` Python package and `youtube-digest` CLI.
- Added auditable artifact storage for transcripts, prompts, analysis, article
  drafts, final Markdown, EPUBs, HTML archives, and manifests.
- Added two-pass `magazine` mode with transcript analysis and optional expansion.
- Added provider support for Anthropic, Gemini, DeepSeek, OpenAI, OpenRouter, and
  generic OpenAI-compatible chat completion APIs.
- Added SQLite-backed processed-video tracking and job state.
- Added Docker, systemd, CI, smoke-test, and Hermes skill scaffolding.
- Added `generate --video-url` for explicit single-video runs.
- Improved config parsing errors with line, column, and strict JSON guidance.
- Removed legacy launchd plist, shell runner, root skill, and JSON tracker files
  from the main project surface.

## [0.1.0] - 2026-04-25

- Initial release-preparation baseline derived from
  `zarazhangrui/youtube-to-ebook`.
