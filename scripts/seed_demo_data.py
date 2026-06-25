from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import clear_opportunities, save_opportunities
from src.models import Opportunity

demo_items = [
    Opportunity(
        "Software Engineering Work Experience",
        "Northstar Digital",
        "London",
        "2026-07-15",
        "Technology",
        "One-week placement supporting a small engineering team with web app tasks.",
        "https://example.com/northstar-work-experience",
        "Demo Seed",
    ),
    Opportunity(
        "Hospitality Summer Placement",
        "Riverside Hotel Group",
        "Manchester",
        "2026-08-01",
        "Hospitality",
        "Front-of-house and operations placement for students exploring customer service roles.",
        "https://example.com/riverside-placement",
        "Demo Seed",
    ),
    Opportunity(
        "Healthcare Insight Day",
        "City General Hospital",
        "Birmingham",
        "2026-07-22",
        "Healthcare",
        "A one-day programme introducing clinical and non-clinical career paths.",
        "https://example.com/city-general-insight-day",
        "Demo Seed",
    ),
]

clear_opportunities()
save_opportunities(demo_items)
print(f"Seeded {len(demo_items)} opportunities.")