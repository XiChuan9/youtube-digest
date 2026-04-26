"""Filesystem artifact management."""

import json
import re
from pathlib import Path
from typing import Any, Dict


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
