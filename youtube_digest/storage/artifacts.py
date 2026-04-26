"""Filesystem artifact management."""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def safe_slug(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug[:80] or fallback


class ArtifactStore:
    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        path = self.base_dir / safe_slug(job_id, "job")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def video_dir(self, job_id: str, video_id: str) -> Path:
        path = self.job_dir(job_id) / safe_slug(video_id, "video")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, path: Path, content: str) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def write_json(self, path: Path, data: Dict[str, Any]) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return str(path)

    def latest_video_dir(
        self,
        video_id: str,
        required_files: Iterable[str],
        exclude_job_id: Optional[str] = None,
    ) -> Optional[Path]:
        video_slug = safe_slug(video_id, "video")
        candidates = []
        for job_dir in self.base_dir.iterdir():
            if not job_dir.is_dir():
                continue
            if exclude_job_id and job_dir.name == safe_slug(exclude_job_id, "job"):
                continue
            video_dir = job_dir / video_slug
            if not video_dir.is_dir():
                continue
            if all((video_dir / name).is_file() for name in required_files):
                candidates.append(video_dir)

        if not candidates:
            return None
        return max(candidates, key=lambda path: (path.parent.name, path.stat().st_mtime))

    def copy_files(self, source_dir: Path, destination_dir: Path, filenames: Iterable[str]) -> Dict[str, Dict[str, str]]:
        destination_dir.mkdir(parents=True, exist_ok=True)
        copied = {}
        for filename in filenames:
            source = source_dir / filename
            destination = destination_dir / filename
            shutil.copy2(source, destination)
            copied[filename] = {
                "source": str(source),
                "destination": str(destination),
            }
        return copied
