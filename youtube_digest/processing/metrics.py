"""Lightweight content metrics."""

import re


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?|[\u4e00-\u9fff]")


def estimate_word_count(text: str) -> int:
    """Estimate word count for validation.

    Latin-script text is counted by word-like tokens. CJK characters are counted
    individually so the function remains useful for multilingual outputs.
    """
    return len(WORD_RE.findall(text or ""))
