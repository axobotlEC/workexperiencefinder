# src/services/collect.py
from typing import Any, Callable, Dict, List

from src.database import save_opportunities
from src.models import Opportunity
from src.scrapers import SCRAPER_FUNCTIONS
from src.services.clean_text import clean_text
from src.services.dedupe import dedupe_by_link
from src.categoriser.rules import categorise_opportunity


def _canonicalise_item(raw_item: Any) -> Dict[str, Any] | None:
    if hasattr(raw_item, "to_dict"):
        item = raw_item.to_dict()
    elif isinstance(raw_item, dict):
        item = dict(raw_item)
    else:
        return None

    alternate_map = {
        "name": "title",
        "employer": "company",
        "url": "link",
        "href": "link",
        "source_name": "source",
    }

    for alt, canonical in alternate_map.items():
        if canonical not in item and item.get(alt) is not None:
            item[canonical] = item.pop(alt)

    normalized: Dict[str, Any] = {}
    for field in Opportunity.__annotations__.keys():
        value = item.get(field, "")
        normalized[field] = clean_text(value) if isinstance(value, str) else value or ""

    if not normalized["title"] or not normalized["company"] or not normalized["link"]:
        print("Warning: skipping opportunity with missing required fields", {
            "title": normalized.get("title"),
            "company": normalized.get("company"),
            "link": normalized.get("link"),
            "source": normalized.get("source"),
        })
        return None

    return normalized


def collect_opportunities(scraper_funcs: List[Callable[[], List[Any]]] | None = None) -> List[Dict[str, Any]]:
    if scraper_funcs is None:
        scraper_funcs = SCRAPER_FUNCTIONS

    raw_items: List[Any] = []
    for fn in scraper_funcs:
        try:
            raw_items.extend(fn())
        except Exception as e:
            print("scraper error:", e)

    canonical_items = [_canonicalise_item(it) for it in raw_items]
    canonical_items = [it for it in canonical_items if it is not None]
    canonical_items = dedupe_by_link(canonical_items)
    canonical_items = [categorise_opportunity(it) for it in canonical_items]
    return canonical_items


def collect_and_save(scraper_funcs: List[Callable[[], List[Any]]] | None = None) -> List[Dict[str, Any]]:
    items = collect_opportunities(scraper_funcs)
    save_opportunities(items)
    return items
