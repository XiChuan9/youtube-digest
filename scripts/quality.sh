#!/usr/bin/env bash
set -euo pipefail

export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/youtube-digest-pycache}"
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m compileall -q \
  youtube_digest \
  tests \
  main.py \
  get_videos.py \
  get_transcripts.py \
  write_articles.py \
  send_email.py \
  dashboard.py

"$PYTHON" -m unittest discover -s tests
"$PYTHON" -m youtube_digest --help >/dev/null
"$PYTHON" -c "import get_videos, get_transcripts, write_articles, send_email; print('legacy wrappers import ok')"
