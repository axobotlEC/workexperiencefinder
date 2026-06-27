from src.scrapers.example_company import ExampleCompanyScraper, scrape_example_company
from src.scrapers.example__job_board import ExampleJobBoardScraper, scrape_example_job_board
from src.scrapers.base import BaseScraper
from src.scrapers.uptree import scrape_uptree
from src.scrapers.springpod import scrape_springpod
from src.scrapers.futures_finder import scrape_futures_finder

# Live scrapers that fetch real opportunities from external sites.
SCRAPER_FUNCTIONS = [
    scrape_uptree,
    scrape_springpod,
    scrape_futures_finder,
]

# Demo scrapers returning static sample data (useful for offline/dev runs).
EXAMPLE_SCRAPER_FUNCTIONS = [
    scrape_example_company,
    scrape_example_job_board,
]

__all__ = [
    "BaseScraper",
    "ExampleCompanyScraper",
    "ExampleJobBoardScraper",
    "scrape_example_company",
    "scrape_example_job_board",
    "scrape_uptree",
    "scrape_springpod",
    "scrape_futures_finder",
    "SCRAPER_FUNCTIONS",
    "EXAMPLE_SCRAPER_FUNCTIONS",
]
