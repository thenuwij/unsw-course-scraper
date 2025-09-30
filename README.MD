# UNSW Handbook Course Scraper

A data scraper that gathers structured UNSW Handbook course data by pairing Crawl4AI-powered crawling with an OpenAI extraction prompt. Everything is wired through a single CLI entrypoint and a modular, YAML-driven configuration layer.

## Highlights

- Async scraping pipeline powered by Crawl4AI
- LLM extraction prompt tuned for UNSW course pages
- Configurable via `config/settings.yaml` or CLI overrides
- CSV exports with field completeness reporting
- Clear separation between loading, crawling, parsing, and writing stages

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
   Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. You can also export the variable directly in your shell.

4. **Run the scraper**
   ```bash
   python cli.py scrape --limit 5
   ```
   Results are written to `data/output/courses.csv` by default.

## Configuration

Key settings live in `config/settings.yaml`:

- `handbook.base_url_template`: URL pattern used to build course links
- `handbook.css_selector`: Page region passed to the LLM
- `handbook.input_file`: JSON file containing a `course_codes` array
- `crawler.*`: Browser type, headless mode, verbosity, throttle delay
- `llm.*`: Model alias and placeholder for missing fields

CLI flags (`--year`, `--level`, `--input`, `--output`, `--limit`) override the YAML when present.

## Adapting for other UNSW data

- **Change input format**: Update `handbook/loader.py` if you prefer CSV or database-driven course lists.
- **Modify fields**: Adjust `CourseRecord` and `EXTRACTION_PROMPT` inside `handbook/parser.py`, then mirror any new fields in `handbook/writer.py`.
- **Tweak crawling behaviour**: Edit `CrawlSettings` defaults in `handbook/crawler.py` or override them via the YAML/CLI if you need a different Playwright browser or throttle.
- **Keep the pipeline**: The CLI + loader → crawler → parser → writer flow remains unchanged; only swap the pieces above to suit your project.

## Project Layout

```
.
├── cli.py                    # CLI entrypoint that wires up the pipeline
├── config/
│   └── settings.yaml         # Default handbook, crawler, and LLM settings
├── data/
│   └── samples/course_codes.json
├── handbook/
│   ├── __init__.py           # Export shortcuts for library usage
│   ├── crawler.py            # Handles Crawl4AI browser lifecycle and page fetches
│   ├── loader.py             # Loads + cleans course codes and constructs URLs
│   ├── parser.py             # Builds the LLM strategy and validates JSON output
│   └── writer.py             # Persists CSV results and computes completeness stats
├── logging.conf              # fileConfig definition for console logging
├── requirements.txt          # Runtime dependencies
└── README.MD
```

### File Glossary

- `cli.py`: Parses CLI arguments, loads configuration, and orchestrates the scrape run.
- `config/settings.yaml`: Houses default handbook/crawler/LLM options that the CLI reads.
- `data/samples/course_codes.json`: Example list of course codes for quick tests.
- `handbook/crawler.py`: Wraps Crawl4AI’s async browser to fetch page content safely.
- `handbook/loader.py`: Cleans raw course codes and generates UNSW Handbook URLs.
- `handbook/parser.py`: Defines the extraction prompt, runs the LLM, and validates JSON output.
- `handbook/writer.py`: Writes CSV results and produces completeness metrics for the dataset.
- `logging.conf`: Configures console logging via Python’s `logging.config.fileConfig`.
- `requirements.txt`: Python packages required to run the scraper.

## Sample Input

`data/samples/course_codes.json`:
```json
{
  "course_codes": ["COMP1511", "MATH1131", "ARTS1360"]
}
```
Provide your own course list when running larger batches.

## Acknowledgements

This project follows ideas shared in bhancockio’s tutorial “Deep Seek Crawler” on YouTube (https://www.youtube.com/watch?v=Osl4NgAXvRk) and on GitHub (https://github.com/bhancockio/deepseek-ai-web-crawler). Their walkthrough provided the conceptual foundation and structure that shaped this UNSW-specific version.
