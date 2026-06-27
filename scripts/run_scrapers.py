"""Run available scrapers and save opportunities to the database."""
from src.services.collect import collect_and_save
from src.scrapers import SCRAPER_FUNCTIONS


def run_all():
    processed = collect_and_save(SCRAPER_FUNCTIONS)
    if processed:
        print(f"Saved {len(processed)} opportunities.")
    else:
        print("No opportunities to save.")


if __name__ == "__main__":
    run_all()
