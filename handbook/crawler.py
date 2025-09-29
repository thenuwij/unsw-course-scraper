"""Async interaction with the UNSW Handbook via Crawl4AI.

Edit `CrawlSettings` defaults below if you need a different browser, delay,
or session prefix when adapting the scraper.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Iterable, List, Sequence
from uuid import uuid4

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)

from .parser import CourseParser, CourseRecord

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CrawlSettings:
    """Runtime options for the headless browser and crawl cadence."""

    browser: str = "chromium"  # Swap to "firefox"/"webkit" if required
    headless: bool = True
    verbose: bool = False
    delay_seconds: float = 0.5
    session_prefix: str = "unsw_handbook"


class HandbookCrawler:
    """Coordinates the Crawl4AI client and hands results to the parser."""

    def __init__(self, parser: CourseParser, settings: CrawlSettings | None = None) -> None:
        self.parser = parser
        self.settings = settings or CrawlSettings()
        self._browser_config = BrowserConfig(
            browser_type=self.settings.browser,
            headless=self.settings.headless,
            verbose=self.settings.verbose,
        )
        self._strategy = parser.build_strategy()

    async def crawl(self, urls: Sequence[str], *, css_selector: str) -> List[CourseRecord]:
        """Iterate through URLs and return the combined set of course records."""
        session_id = f"{self.settings.session_prefix}_{uuid4().hex[:8]}"
        harvested: List[CourseRecord] = []

        async with AsyncWebCrawler(config=self._browser_config) as crawler:
            for position, url in enumerate(urls, start=1):
                LOGGER.info("[%d/%d] Fetching %s", position, len(urls), url)

                try:
                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(
                            extraction_strategy=self._strategy,
                            css_selector=css_selector,
                            cache_mode=CacheMode.BYPASS,
                            session_id=session_id,
                        ),
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.error("Crawler failed for %s: %s", url, exc)
                    continue

                if not result.success:
                    LOGGER.warning("Extraction failed for %s: %s", url, result.error_message)
                    continue

                if not result.extracted_content:
                    LOGGER.warning("No content returned for %s", url)
                    continue

                records = self.parser.parse_payload(result.extracted_content)
                if not records:
                    LOGGER.warning("Parser produced no records for %s", url)
                else:
                    harvested.extend(records)
                    LOGGER.info("Captured %d course(s) from %s", len(records), url)

                if position < len(urls):
                    await asyncio.sleep(self.settings.delay_seconds)

        return harvested
