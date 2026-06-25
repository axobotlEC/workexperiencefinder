from src.database import init_db, save_opportunities
from src.scrapers.example_site import scrape_site
from src.categoriser.rules import categorise_opportunity

init_db()
items = scrape_site()

for item in items:
    item = categorise_opportunity(item)

save_opportunities(items)
