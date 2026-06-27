from src.scrapers.example_company import ExampleCompanyScraper, scrape_example_company
from src.scrapers.example__job_board import ExampleJobBoardScraper, scrape_example_job_board
from src.scrapers.base import BaseScraper

SCRAPER_FUNCTIONS = [
    scrape_example_company,
    scrape_example_job_board,
]

__all__ = [
    "BaseScraper",
    "ExampleCompanyScraper",
    "ExampleJobBoardScraper",
    "scrape_example_company",
    "scrape_example_job_board",
    "SCRAPER_FUNCTIONS",
]