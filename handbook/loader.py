"""Utilities for sourcing the list of UNSW course codes to scrape.

Adjust `from_json` if you swap to another input format (e.g. CSV); the rest of
the pipeline can stay the same as long as `CourseList.codes` yields strings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(slots=True)
class CourseList:
    """Represents a set of course codes and provides helper utilities."""

    codes: List[str]

    @classmethod
    def from_json(cls, file_path: Path | str) -> "CourseList":
        """Load course codes from a JSON file with a `course_codes` array."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Course list file not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

        raw_codes = payload.get("course_codes")
        if not isinstance(raw_codes, Iterable) or isinstance(raw_codes, (str, bytes)):
            raise ValueError("JSON must include an array named 'course_codes'")

        cleaned = []
        for code in raw_codes:
            if not isinstance(code, str) or not code.strip():
                continue
            code_upper = code.strip().upper()
            if code_upper not in cleaned:
                cleaned.append(code_upper)

        if not cleaned:
            raise ValueError(f"No usable course codes found in {path}")

        return cls(cleaned)

    def build_urls(self, template: str, *, level: str, year: int) -> List[str]:
        """Create handbook URLs from the provided template string."""
        urls = []
        for code in self.codes:
            url = template.format(level=level, year=year, code=code)
            urls.append(url)
        return urls

    def __iter__(self):
        return iter(self.codes)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.codes)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"CourseList(size={len(self.codes)})"
