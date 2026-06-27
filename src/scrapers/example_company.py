from src.scrapers.base import BaseScraper


class ExampleCompanyScraper(BaseScraper):
    def scrape(self):
        raw_items = [
            {
                "name": "Virtual Marketing Internship",
                "employer": "Marketing Co",
                "location": "Remote",
                "deadline": "2026-12-15",
                "sector": "Marketing",
                "description": "Hands-on virtual marketing internship for students.",
                "url": "https://example.com/opps/marketing-intern",
                "source": "example_company",
            },
            {
                "title": "Data Science Placement",
                "company": "DataCorp",
                "location": "Online",
                "deadline": "2026-11-30",
                "sector": "Technology",
                "description": "A student-focused data science work experience.",
                "link": "https://example.com/opps/data-science",
                "source": "example_company",
            },
        ]
        return [self.build_opportunity(item) for item in raw_items]


def scrape_example_company():
    return ExampleCompanyScraper().scrape()
