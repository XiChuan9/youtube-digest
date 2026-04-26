"""Backward-compatible entrypoint.

The original project used `python main.py`. The new productized pipeline lives
in `youtube_digest`, but this file keeps the old command working.
"""

import sys

from youtube_digest.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["generate"]))
