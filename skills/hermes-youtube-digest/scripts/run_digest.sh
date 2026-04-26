#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-magazine}"
VIDEO_URL="${2:-}"

if [[ -n "$VIDEO_URL" ]]; then
  youtube-digest generate --mode "$MODE" --video-url "$VIDEO_URL" --json
else
  youtube-digest generate --mode "$MODE" --json
fi
