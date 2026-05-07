"""Parsing helpers for scoreboard OCR text."""

from __future__ import annotations

import re


SCORE_RE = re.compile(r"(?<!\d)(?P<home>\d{1,2})\s*-\s*(?P<away>\d{1,2})(?!\d)")
CLOCK_RE = re.compile(r"(?P<minute>\d{1,2})\s*[:.]\s*(?P<second>\d{2})")


def parse_score(text: str, max_score: int = 20) -> tuple[str, str]:
    """Parse football score text while avoiding clock values such as 80:30."""
    match = SCORE_RE.search(text)
    if not match:
        return "", ""

    home = int(match.group("home"))
    away = int(match.group("away"))
    if home > max_score or away > max_score:
        return "", ""
    return str(home), str(away)


def parse_clock(text: str) -> str:
    match = CLOCK_RE.search(text)
    if not match:
        return ""

    minute = int(match.group("minute"))
    second = int(match.group("second"))
    if second >= 60:
        return ""
    return f"{minute:02d}:{second:02d}"
