# src/scrapers/example_site.py
from src.models import Opportunity
from src.services.clean_text import clean_text

def scrape_site():
    """
    Demo scraper: returns a small list of opportunities.
    Replace with real scraping logic (requests/BeautifulSoup or Playwright).
    """
    demo = [
        Opportunity(
            title="Summer Work Experience - Software Engineering",
            company="ExampleTech",
            location="London, UK",
            deadline="2026-08-01",
            sector="Technology",
            description=clean_text("A 2-week placement for students interested in software engineering. Must be 16+."),
            link="https://example.org/opps/exampletech-summer",
            source="example_site"
        ),
        Opportunity(
            title="Marketing Placement (student)",
            company="BrightMedia",
            location="Remote",
            deadline="2026-07-15",
            sector="Marketing",
            description=clean_text("Paid placement for students studying marketing or communications."),
            link="https://example.org/opps/brightmedia-placement",
            source="example_site"
        ),
    ]
    return [o.to_dict() for o in demo]
