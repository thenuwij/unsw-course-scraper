"""Toolkit for acquiring and normalising UNSW Handbook course data."""

from .loader import CourseList
from .crawler import HandbookCrawler, CrawlSettings
from .parser import CourseRecord, CourseParser
from .writer import CourseWriter

__all__ = [
    "CourseList",
    "HandbookCrawler",
    "CrawlSettings",
    "CourseRecord",
    "CourseParser",
    "CourseWriter",
]
