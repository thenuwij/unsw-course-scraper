# UNSW Handbook Course Scraper

An async scraper that extracts structured course data from the UNSW Handbook by pairing Crawl4AI-powered crawling with an LLM extraction prompt. Built to support the data pipeline for [UniVise](https://github.com/thenuwij/UniVise), and reusable for any UNSW Handbook data collection task.

## Overview

The scraper accepts a list of course codes, constructs the corresponding Handbook URLs, fetches each page using a headless browser via Crawl4AI, and passes the extracted HTML region to an LLM for structured field extraction. Results are written to CSV with per-field completeness reporting. The pipeline is fully async and configurable without code changes via a YAML config file and CLI flags.

## Pipeline

```
loader → crawler → parser → writer
```

- `loader.py` — cleans raw course codes and constructs UNSW Handbook URLs
- `crawler.py` — manages the Crawl4AI browser lifecycle and fetches page content
- `parser.py` — builds the LLM extraction prompt, runs inference, and validates JSON output
- `writer.py` — writes CSV results and computes field completeness metrics

## Getting Started

1. **Create an environment**

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Provide credentials**

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

4. **Run the scraper**

```bash
python cli.py scrape --limit 5
```

Results are written to `data/output/courses.csv` by default.

## Configuration

Key settings live in `config/settings.yaml`:

- `handbook.base_url_template` — URL pattern used to build course links
- `handbook.css_selector` — page region passed to the LLM
- `handbook.input_file` — JSON file containing a `course_codes` array
- `crawler.*` — browser type, headless mode, verbosity, throttle delay
- `llm.*` — model alias and placeholder for missing fields

CLI flags (`--year`, `--level`, `--input`, `--output`, `--limit`) override the YAML when present.

## Sample Input

`data/samples/course_codes.json`:

```json
{
  "course_codes": ["COMP1511", "MATH1131", "ARTS1360"]
}
```

## Project Layout

```
.
├── cli.py
├── config/
│   └── settings.yaml
├── data/
│   └── samples/course_codes.json
├── handbook/
│   ├── __init__.py
│   ├── crawler.py
│   ├── loader.py
│   ├── parser.py
│   └── writer.py
├── logging.conf
├── requirements.txt
└── README.md
```

## Acknowledgements

This project follows ideas shared in bhancockio's tutorial "Deep Seek Crawler" on YouTube (https://www.youtube.com/watch?v=Osl4NgAXvRk) and on GitHub (https://github.com/bhancockio/deepseek-ai-web-crawler). Their walkthrough provided the conceptual foundation and structure that shaped this UNSW-specific version.
