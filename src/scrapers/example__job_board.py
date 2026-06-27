from src.scrapers.base import BaseScraper


class ExampleJobBoardScraper(BaseScraper):
    def scrape(self):
        raw_items = [
            {
                "job_title": "Summer Engineering Internship",
                "company_name": "BuildTech",
                "location": "London",
                "deadline": "2026-09-01",
                "sector": "Technology",
                "description": "A practical engineering placement for students.",
                "href": "https://jobboard.example.com/eng-internship",
                "source_name": "example_job_board",
            },
            {
                "title": "Communications Assistant",
                "company": "Community Org",
                "location": "Manchester",
                "deadline": "2026-08-15",
                "sector": "Marketing",
                "description": "Support communication campaigns and learn workplace skills.",
                "link": "https://jobboard.example.com/comm-assistant",
                "source": "example_job_board",
            },
        ]
        return [self.build_opportunity(item) for item in raw_items]


def scrape_example_job_board():
    return ExampleJobBoardScraper().scrape()
