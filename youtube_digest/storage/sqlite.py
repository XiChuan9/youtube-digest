"""SQLite storage for idempotency and job status."""

import sqlite3
from pathlib import Path
from typing import Iterable, List

from youtube_digest.models import Video, utc_now_iso


class DigestStore:
    def __init__(self, db_path: str = "digest.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_videos (
                    video_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    url TEXT NOT NULL,
                    processed_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT
                )
                """
            )

    def start_job(self, job_id: str, mode: str) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (job_id, mode, status, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (job_id, mode, "running", now, now),
            )

    def finish_job(self, job_id: str, status: str, error: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, error = ?
                WHERE job_id = ?
                """,
                (status, utc_now_iso(), error or None, job_id),
            )

    def is_processed(self, video_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_videos WHERE video_id = ?",
                (video_id,),
            ).fetchone()
        return row is not None

    def filter_new(self, videos: Iterable[Video], force: bool = False) -> List[Video]:
        if force:
            return list(videos)
        return [video for video in videos if not self.is_processed(video.video_id)]

    def mark_processed(self, video: Video) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_videos
                    (video_id, title, channel, url, processed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (video.video_id, video.title, video.channel, video.url, utc_now_iso()),
            )
