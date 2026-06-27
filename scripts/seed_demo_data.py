# scripts/seed_demo_data.py
from src.models import Opportunity
from src.database import save_opportunities, init_db
from src.categoriser.rules import categorise_opportunity

def seed():
    init_db()
    demo = [
        Opportunity(
            title="Intro to Data Science Placement",
            company="Data4Good",
            location="Manchester, UK",
            deadline="2026-09-01",
            sector="Data",
            description="A short placement for students to learn data analysis.",
            link="https://example.org/opps/data4good",
            source="seed"
        ),
        Opportunity(
            title="Engineering Work Experience",
            company="BuildIt Ltd",
            location="Bristol, UK",
            deadline="2026-08-15",
            sector="Engineering",
            description="Hands-on placement for school students.",
            link="https://example.org/opps/buildit",
            source="seed"
        ),
    ]
    # Ensure demo records are passed through the categorisation logic
    # so fields like `sector` and `is_student_opportunity` are populated.
    processed = [categorise_opportunity(d) for d in demo]
    save_opportunities(processed)
    print("Seeded demo data.")

if __name__ == "__main__":
    seed()
