"""Command line interface for the UNSW Handbook scraper."""

from __future__ import annotations

import argparse
import asyncio
import logging
import logging.config
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from handbook import CourseList, CourseParser, HandbookCrawler, CourseWriter, CrawlSettings

LOGGER = logging.getLogger(__name__)


def configure_logging(logging_path: Path) -> None:
    if not logging_path.exists():
        logging.basicConfig(level=logging.INFO)
        LOGGER.warning("Logging configuration %s not found. Using basicConfig().", logging_path)
        return

    logging.config.fileConfig(logging_path, disable_existing_loggers=False, defaults={"sys": sys})


def read_settings(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape UNSW courses into CSV format.")
    parser.add_argument("command", choices=["scrape"], help="Operation to perform")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to YAML settings file")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of courses to scrape")
    parser.add_argument("--year", type=int, help="Override the handbook year from settings")
    parser.add_argument("--level", choices=["undergraduate", "postgraduate"], help="Override the study level")
    parser.add_argument("--output", help="Override the output CSV path")
    parser.add_argument("--input", help="Override the course list JSON path")
    return parser


def apply_overrides(settings: dict, args: argparse.Namespace) -> dict:
    handbook_cfg = settings.setdefault("handbook", {})

    if args.year is not None:
        handbook_cfg["year"] = args.year
    if args.level is not None:
        handbook_cfg["level"] = args.level
    if args.output is not None:
        handbook_cfg["output_file"] = args.output
    if args.input is not None:
        handbook_cfg["input_file"] = args.input
    if args.limit is not None:
        settings["limit"] = args.limit

    return settings


def create_crawler_components(settings: dict) -> tuple[CourseList, HandbookCrawler, CourseWriter, dict]:
    handbook_cfg = settings.get("handbook", {})
    crawler_cfg = settings.get("crawler", {})
    llm_cfg = settings.get("llm", {})

    course_list = CourseList.from_json(handbook_cfg.get("input_file"))

    parser = CourseParser(
        provider=llm_cfg.get("provider", "openai/gpt-4o-mini"),
        placeholder=llm_cfg.get("placeholder", "Not specified"),
    )

    crawl_settings = CrawlSettings(
        browser=crawler_cfg.get("browser", "chromium"),
        headless=bool(crawler_cfg.get("headless", True)),
        verbose=bool(crawler_cfg.get("verbose", False)),
        delay_seconds=float(crawler_cfg.get("delay_seconds", 0.5)),
        session_prefix=crawler_cfg.get("session_prefix", "unsw_handbook"),
    )

    crawler = HandbookCrawler(parser=parser, settings=crawl_settings)
    writer = CourseWriter()

    return course_list, crawler, writer, handbook_cfg


def format_summary(report: dict) -> str:
    lines = ["\nData completeness summary:"]
    total = report.get("total_courses", 0)
    lines.append(f"Total courses: {total}")
    for field, stats in report.get("fields", {}).items():
        lines.append(
            f"  - {field}: {stats['present']}/{total} present ({stats['percent_present']}% coverage)"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.command != "scrape":  # pragma: no cover - currently a single command
        parser.error("Unsupported command")

    settings_path = Path(args.config)
    settings = read_settings(settings_path)
    settings = apply_overrides(settings, args)

    configure_logging(Path("logging.conf"))

    course_list, crawler, writer, handbook_cfg = create_crawler_components(settings)

    selected_codes = course_list.codes
    limit = settings.get("limit")
    if limit is not None:
        selected_codes = selected_codes[: limit]

    urls = CourseList(selected_codes).build_urls(
        handbook_cfg.get("base_url_template"),
        level=handbook_cfg.get("level", "undergraduate"),
        year=int(handbook_cfg.get("year", 2025)),
    )

    async def orchestrate() -> int:
        records = await crawler.crawl(urls, css_selector=handbook_cfg.get("css_selector", "main"))
        if not records:
            LOGGER.warning("No course data captured")
            return 1

        output_path = handbook_cfg.get("output_file", "data/output/courses.csv")
        destination = writer.write_csv(records, output_path)
        report = writer.build_completeness_report(records)
        print(format_summary(report))
        LOGGER.info("Results stored at %s", destination)
        return 0

    return asyncio.run(orchestrate())


if __name__ == "__main__":
    raise SystemExit(main())
