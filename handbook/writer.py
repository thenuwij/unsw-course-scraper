"""Output helpers for the UNSW handbook scraper.

Change `self.field_order` if you add/remove fields from `CourseRecord`; the CSV
writer will follow whatever order you set here.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from pathlib import Path
from typing import Iterable, List

from .parser import CourseRecord

LOGGER = logging.getLogger(__name__)


class CourseWriter:
    """Persist course data and produce lightweight quality reports."""

    def __init__(self, *, encoding: str = "utf-8", newline: str = "") -> None:
        self.encoding = encoding
        self.newline = newline
        self.field_order = list(CourseRecord.model_fields.keys())

    def write_csv(self, records: Iterable[CourseRecord], destination: Path | str) -> Path:
        records = list(records)
        if not records:
            raise ValueError("No course records were provided for export")

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding=self.encoding, newline=self.newline) as handle:
            writer = csv.DictWriter(handle, fieldnames=self.field_order)
            writer.writeheader()
            for record in records:
                writer.writerow(record.model_dump())

        LOGGER.info("Wrote %d course rows to %s", len(records), path)
        return path

    @staticmethod
    def build_completeness_report(records: Iterable[CourseRecord]) -> dict:
        """Calculate how frequently each field was populated."""
        records = list(records)
        total = len(records)
        summary = {"total_courses": total, "fields": {}}

        if total == 0:
            return summary

        counters = Counter()
        for record in records:
            data = record.model_dump()
            for key, value in data.items():
                if isinstance(value, str) and value.strip():
                    counters[key] += 1

        for key in CourseRecord.model_fields.keys():
            present = counters.get(key, 0)
            summary["fields"][key] = {
                "present": present,
                "missing": total - present,
                "percent_present": round((present / total) * 100, 1),
            }

        return summary
