from typing import List

from src.models import Opportunity
from src.services.clean_text import clean_text


def scrape_springpod() -> List[dict]:
    """Scrape Springpod for virtual work experience opportunities.

    Returns a list of opportunity dicts. If the site requires JS, the scraper
    will gracefully return an empty list when requests/bs4 are insufficient.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return []

    url = "https://www.springpod.com/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Crawl the Springpod site to find experience/listing links
    def crawl_links(starts, max_pages=600, max_depth=3):
        from urllib.parse import urljoin, urlparse
        visited = set()
        queue = []
        candidates = set()
        for s in starts:
            queue.append((s, 0))
        allowed_domains = {urlparse(s).netloc for s in starts if s}
        while queue and len(visited) < max_pages:
            cur, depth = queue.pop(0)
            if cur in visited or depth > max_depth:
                continue
            visited.add(cur)
            try:
                r = requests.get(cur, timeout=10)
                r.raise_for_status()
            except Exception:
                continue
            doc = BeautifulSoup(r.text, "html.parser")
            for a in doc.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(" ", strip=True)
                if not href:
                    continue
                full = href if href.startswith("http") else urljoin(cur, href)
                parsed = urlparse(full)
                if parsed.netloc not in allowed_domains:
                    continue
                path = parsed.path.lower()
                if any(x in path for x in ("sign-in", "signin", "login", "privacy", "terms", "cookie", "account")):
                    continue
                if any(k in path for k in ("experience", "experiences", "virtual-work-experience", "work-experience", "opportunity", "opportunities", "listing", "search")) or any(k in text.lower() for k in ("experience", "work experience", "virtual work", "apply", "register", "open")):
                    candidates.add(full)
                if depth < max_depth and full not in visited:
                    queue.append((full, depth + 1))
        return list(candidates)

    # Add additional known entry points for better discovery
    starts = [
        url,
        "https://www.springpod.com/virtual-work-experience",
        "https://www.springpod.com/virtual-work-experience/search",
        "https://opportunities.springpod.com/",
        "https://space.springpod.com/",
    ]

    candidates = crawl_links(starts)

    def _parse_jsonld(doc):
        try:
            import json
        except Exception:
            return None
        for s in doc.find_all("script", type="application/ld+json"):
            try:
                payload = json.loads(s.string or "")
            except Exception:
                continue
            if isinstance(payload, list):
                items = payload
            else:
                items = [payload]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Event", "event"):
                    name = item.get("name")
                    start = item.get("startDate") or item.get("start")
                    loc = ""
                    location = item.get("location")
                    if isinstance(location, dict):
                        loc = location.get("name") or location.get("address", "")
                    elif isinstance(location, str):
                        loc = location
                    organizer = ""
                    org = item.get("organizer") or item.get("provider")
                    if isinstance(org, dict):
                        organizer = org.get("name")
                    elif isinstance(org, str):
                        organizer = org
                    return {"title": name, "deadline": start, "location": loc, "company": organizer}
        return None


    def fetch_detail(link):
        try:
            import requests
            from bs4 import BeautifulSoup
        except Exception:
            return None

        full = link if link.startswith("http") else f"https://www.springpod.com{link}"
        try:
            r = requests.get(full, timeout=10)
            r.raise_for_status()
        except Exception:
            return None
        doc = BeautifulSoup(r.text, "html.parser")

        import re
        title = None
        deadline = ""
        location = ""
        company = "Springpod"
        try:
            jsonld = _parse_jsonld(doc)
            if jsonld:
                title = jsonld.get("title")
                deadline = jsonld.get("deadline") or ""
                location = jsonld.get("location") or ""
                company = jsonld.get("company") or company
        except Exception:
            pass

        if not title:
            h1 = doc.find("h1")
            title = clean_text(h1.get_text(" ", strip=True)) if h1 else None

        if not title:
            return None

        def _find_card_value(doc, label):
            for wrapper in doc.select("div.card-job-category-wrapper"):
                title_node = wrapper.select_one("div.card-job-category-title-wrapper")
                if not title_node:
                    continue
                title_text = clean_text(title_node.get_text(" ", strip=True)).lower()
                if label.lower() in title_text:
                    value_node = wrapper.select_one("div.card-job-category-text")
                    if value_node:
                        return clean_text(value_node.get_text(" ", strip=True))
            return ""

        desc = ""
        desc_block = doc.select_one("div.job-description-title-wrapper + div.rich-text.w-richtext")
        if desc_block is None:
            desc_block = doc.select_one("section.section.job-post div.rich-text.w-richtext")
        if desc_block:
            desc = clean_text(desc_block.get_text(" ", strip=True))
        else:
            meta = doc.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                desc = clean_text(meta["content"])

        card_deadline = _find_card_value(doc, "Start date")
        if not card_deadline:
            card_deadline = _find_card_value(doc, "Closing")
        if card_deadline:
            deadline = card_deadline
        if not deadline:
            time_tag = doc.find("time")
            if time_tag and time_tag.get("datetime"):
                deadline = time_tag.get("datetime")
            elif time_tag:
                deadline = clean_text(time_tag.get_text(" ", strip=True))

        card_location = _find_card_value(doc, "Location")
        if card_location:
            location = card_location
        elif re.search(r"\bonline\b", doc.get_text(" ", strip=True), re.I):
            location = "Online"

        sector = _find_card_value(doc, "Job sector") or _find_card_value(doc, "Sector")

        def _parse_company(doc):
            for wrapper in doc.select("div.card-job-post-sidebar-title-about-company-wrapper"):
                headings = [h.get_text(" ", strip=True) for h in wrapper.find_all(["h3", "h4"])]
                if len(headings) >= 2 and headings[0].strip().lower() == "about":
                    candidate = headings[1].strip()
                    if candidate:
                        return clean_text(candidate)
            return ""

        company = _parse_company(doc) or company
        if company in ("Springpod", "") and title and ":" in title:
            part = title.split(":", 1)[1]
            candidate = part.split(",")[0].split("-")[0].strip()
            if len(candidate) > 0 and any(c.isalpha() for c in candidate):
                company = clean_text(candidate)

        if company in ("Springpod", ""):
            try:
                from urllib.parse import urlparse
                parts = [p for p in urlparse(full).path.split('/') if p]
                if parts:
                    slug = parts[-1]
                    cand = slug.replace('-', ' ').title()
                    if cand and cand.lower() != "springpod":
                        company = cand
            except Exception:
                pass
        detail = {
            "title": title,
            "company": company,
            "location": location,
            "deadline": deadline,
            "sector": sector,
            "description": desc,
            "link": full,
            "source": "springpod",
        }

        if (not detail["description"] or len(detail["description"]) < 40) and not detail["deadline"] and not detail["location"] and company == "Springpod":
            return None

        return detail

    for href in candidates:
        detail = fetch_detail(href)
        if detail:
            results.append(detail)

    # dedupe
    seen = set()
    out = []
    for r in results:
        if r.get("link") in seen:
            continue
        seen.add(r.get("link"))
        out.append(r)

    return out
