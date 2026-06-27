# src/categoriser/rules.py
from src.services.clean_text import clean_text

STUDENT_KEYWORDS = [
    "intern", "internship", "work experience", "placement", "student", "graduate scheme", "vacation scheme"
]
SECTOR_KEYWORDS = {
    "technology": ["tech", "software", "developer", "engineering"],
    "marketing": ["marketing", "digital marketing", "social media", "brand"],
    "finance": ["finance", "financial", "accounting", "investment"],
    "healthcare": ["health", "medical", "nursing", "wellbeing"],
    "education": ["education", "learning", "teaching", "school"],
}


def categorise_opportunity(item):
    """
    Adds or refines 'sector', sets 'is_student_opportunity', and returns the updated dict.
    """
    if hasattr(item, "to_dict"):
        data = item.to_dict()
    else:
        data = dict(item)

    text = " ".join([data.get("title", ""), data.get("description", ""), data.get("company", "")])
    text = clean_text(text).lower()

    is_student = any(keyword in text for keyword in STUDENT_KEYWORDS)
    data["is_student_opportunity"] = bool(is_student)

    if not data.get("sector") or data.get("sector") == "General":
        assigned = "General"
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                assigned = sector.capitalize()
                break
        data["sector"] = assigned

    data["scrape_validation_passed"] = True
    return data
