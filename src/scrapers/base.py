from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.models import Opportunity


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def build_opportunity(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_item, dict):
            raise TypeError("Raw scraper item must be a dict.")

        raw = {str(k).lower(): v for k, v in raw_item.items() if k is not None}
        canonical = {field: raw.get(field, "") or "" for field in Opportunity.__annotations__.keys()}

        alt_names = {
            "name": "title",
            "job_title": "title",
            "employer": "company",
            "company_name": "company",
            "url": "link",
            "href": "link",
            "source_name": "source",
            "description_text": "description",
        }

        for alt_field, canonical_field in alt_names.items():
            if not canonical.get(canonical_field) and raw.get(alt_field) is not None:
                canonical[canonical_field] = raw[alt_field]

        missing = [field for field in ("title", "company", "link") if not str(canonical.get(field, "")).strip()]
        if missing:
            raise ValueError(f"Missing required opportunity fields: {', '.join(missing)}")

        return Opportunity(**{k: canonical.get(k, "") for k in Opportunity.__annotations__.keys()}).to_dict()
