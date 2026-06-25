class Opportunity:
    def __init__(self, title, company, location, deadline, sector, description, link, source):      
        self.title = title
        self.company = company
        self.location = location
        self.deadline = deadline
        self.sector = sector
        self.description = description
        self.link = link
        self.source = source

    def to_dict(self): #Converts the Opportunity object to a dictionary for easier storage and retrieval
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "deadline": self.deadline,
            "sector": self.sector,
            "description": self.description,
            "link": self.link,
            "source": self.source,
        }


job = Opportunity(
    "Software Internship",
    "ABC Ltd",                      
    "London",
    "2026-07-15",
    "Technology",
    "Help build websites and apps",
    "https://example.com",
    "Company Careers Page"
)

print(job.title)
print(job.to_dict())


