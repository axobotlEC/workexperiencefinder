from typing import List

from src.models import Opportunity
from src.services.clean_text import clean_text


def scrape_uptree() -> List[dict]:
    """Scrape Uptree events page for opportunities.

    Returns a list of opportunity dicts. Network errors return an empty list.
    """
    # Import networking/parsing libraries lazily so the module can be
    # imported in environments without those dependencies.
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return []

    url = "https://uptree.co/events/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    import re

    candidates = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            if href.startswith("/"):
                full_href = f"https://uptree.co{href}"
            else:
                full_href = f"https://uptree.co/{href}"
        else:
            full_href = href
        full_href = full_href.rstrip("/")
        if full_href in seen:
            continue
        if re.match(r"^https?://uptree\.co/events/[^/]+/\d+$", full_href):
            text = a.get_text(" ", strip=True)
            if text and len(text) > 10 and "view" not in text.lower():
                candidates.append((a, full_href))
                seen.add(full_href)

    if not candidates:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(" ", strip=True)
            if "/events/" in href and len(text) > 5 and "view" not in text.lower():
                if not href.startswith("http"):
                    if href.startswith("/"):
                        href = f"https://uptree.co{href}"
                    else:
                        href = f"https://uptree.co/{href}"
                href = href.rstrip("/")
                if href not in seen:
                    candidates.append((a, href))
                    seen.add(href)

    STOP_TITLES = {"about us", "contact us", "find apprenticeships and jobs", "privacy", "terms", "home", "events"}

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

        full = link if link.startswith("http") else f"https://uptree.co{link}"
        # skip listing index pages
        if full.rstrip("/").endswith("/events") or full.rstrip("/").endswith("/events/uptree"):
            return None
        try:
            r = requests.get(full, timeout=10)
            r.raise_for_status()
        except Exception:
            return None

        doc = BeautifulSoup(r.text, "html.parser")

        title = None
        title_tag = doc.select_one("h2.listings-detail__title")
        if title_tag:
            for span in title_tag.find_all("span"):
                span.extract()
            title = clean_text(title_tag.get_text(" ", strip=True))
        else:
            title = clean_text(doc.title.string) if doc.title and doc.title.string else None

        location = ""
        location_tag = doc.select_one("span.listings-detail__where")
        if location_tag:
            loc_text = clean_text(location_tag.get_text(" ", strip=True))
            if "online" in loc_text.lower():
                location = "Online"
            else:
                location = loc_text

        desc = ""
        desc_block = doc.select_one("div.listings-detail__description")
        if desc_block:
            desc = clean_text(desc_block.get_text(" ", strip=True))
        else:
            article = doc.find("article")
            if article:
                desc = clean_text(article.get_text(" ", strip=True))
            else:
                meta = doc.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    desc = clean_text(meta["content"])

        deadline = ""
        date_node = doc.find(string=re.compile(r"\bDate\b[:]?"))
        if date_node:
            parent = date_node.parent
            text = parent.get_text(" ", strip=True)
            m = re.search(r"Date[:]?[\s]*(.+)", text, re.I)
            if m:
                deadline = clean_text(m.group(1))

        if not deadline:
            time_tag = doc.find("time")
            if time_tag and time_tag.get("datetime"):
                deadline = time_tag.get("datetime")
            elif time_tag:
                deadline = clean_text(time_tag.get_text(" ", strip=True))

        company = "Uptree"
        if title and ":" in title:
            part = title.split(":", 1)[1]
            candidate = part.split(",")[0].split("-")[0].strip()
            if len(candidate) > 0 and any(c.isalpha() for c in candidate):
                company = clean_text(candidate)

        if company in ("Uptree", ""):
            try:
                from urllib.parse import urlparse
                path = urlparse(full).path
                parts = [p for p in path.split("/") if p]
                if "events" in parts:
                    idx = parts.index("events")
                    if len(parts) > idx + 1:
                        slug = parts[idx + 1]
                        company_candidate = slug.replace("-", " ").title()
                        if company_candidate and company_candidate.lower() != "uptree":
                            company = company_candidate
            except Exception:
                pass

        if not title:
            return None
        if title.lower() in STOP_TITLES:
            return None

        detail = {
            "title": title,
            "company": company,
            "location": location,
            "deadline": deadline,
            "sector": "",
            "description": desc,
            "link": full,
            "source": "uptree",
        }

        if (not detail["description"] or len(detail["description"]) < 20) and not detail["deadline"] and not detail["location"]:
            return None

        return detail

    for a, href in candidates:
 re.I))
        if date_node:
            # get surrounding text
            parent = date_node.parent
            text = parent.get_text(" ", strip=True)
            m = re.search(r"Date[:]?\s*(.+)", text, re.I)
            if m:
                deadline = clean_text(m.group(1))

        if not deadline:
            time_tag = doc.find("time")
            if time_tag and time_tag.get("datetime"):
                deadline = time_tag.get("datetime")
            elif time_tag:
                deadline = clean_text(time_tag.get_text(" ", strip=True))

        if not deadline:
            # fallback: look for ISO dates in page text
            text_all = doc.get_text(" ", strip=True)
            m = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text_all)
            if m:
                deadline = m.group(0)

        # normalize obviously-bad deadline values
        if isinstance(deadline, str):
            if deadline.strip() == ":" or len(deadline) > 200 or "such as" in deadline.lower():
                deadline = ""

        # location: look for 'Online' label or common location labels
        location = ""
        whole_text = doc.get_text(" ", strip=True)
        if re.search(r"\bonline\b|ONLINE EVENT|ONLINE event", whole_text):
            location = "Online"
        else:
            addr = doc.find(lambda tag: tag.name in ("address", "p", "div") and re.search(r"\b(Location|Venue|Place)[:]?", tag.get_text(" ", ""), re.I))
            if addr:
                # extract after the label
                t = addr.get_text(" ", strip=True)
                mloc = re.search(r"(?:Location|Venue|Place)[:]?\s*(.+)", t, re.I)
                if mloc:
                    location = clean_text(mloc.group(1))

        # company/organiser heuristics
        company = "Uptree"
        # Pattern like: 'Find out more about Arm on their Company Page'
        m = re.search(r"Find out more about ([A-Z][A-Za-z0-9 &.-]+?) on their Company Page", whole_text)
        if m:
            company = clean_text(m.group(1))
        else:
            # check 'Hosted by' or 'Organiser' labels
            org = doc.find(lambda t: t.name in ("p", "div", "span") and re.search(r"(Hosted by|Organiser|Provider)[:]?", t.get_text(" ", ""), re.I))
            if org:
                mm = re.search(r"(?:Hosted by|Organiser|Provider)[:\s]*(.+)", org.get_text(" ", ""), re.I)
                if mm:
                    company = clean_text(mm.group(1))

        # fallback: derive company from URL slug if still generic
        if company in ("Uptree", ""):
            try:
                from urllib.parse import urlparse
                path = urlparse(full).path
                parts = [p for p in path.split("/") if p]
                # look for slug after 'events'
                if "events" in parts:
                    idx = parts.index("events")
                    if len(parts) > idx+1:
                        slug = parts[idx+1]
                        company_candidate = slug.replace('-', ' ').title()
                        if company_candidate and company_candidate.lower() != 'uptree':
                            company = company_candidate
            except Exception:
                pass

        # fallback: try to derive company from title if formatted like '...: Company, ...'
        if company in ("Uptree", "") and title and ":" in title:
            part = title.split(":", 1)[1]
            candidate = part.split(",")[0].split("-")[0].strip()
            if len(candidate) > 0 and any(c.isalpha() for c in candidate):
                company = clean_text(candidate)

        detail = {
            "title": title,
            "company": company,
            "location": location,
            "deadline": deadline,
            "sector": "",
            "description": desc,
            "link": full,
            "source": "uptree",
        }

        # Validate: require a meaningful description, deadline, or location.
        if (not detail["description"] or len(detail["description"]) < 20) and not detail["deadline"] and not detail["location"]:
            return None

        return detail

    for a, href in candidates:
        detail = fetch_detail(href)
        if detail:
            results.append(detail)

    # Deduplicate by link
    seen = set()
    out = []
    for r in results:
        if r.get("link") in seen:
            continue
        seen.add(r.get("link"))
        out.append(r)

    return out
