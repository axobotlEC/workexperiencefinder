# src/models.py
from dataclasses import dataclass, asdict

@dataclass
class Opportunity:
    title: str
    company: str
    location: str = ""
    deadline: str = ""
    sector: str = ""
    description: str = ""
    link: str = ""
    source: str = ""

    def to_dict(self):
        return asdict(self)
