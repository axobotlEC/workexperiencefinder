from typing import List

from src.models import Opportunity
from src.services.clean_text import clean_text


def scrape_futures_finder() -> List[dict]:
    """Scrape Futures For All finder site for opportunities.

    Returns a list of opportunity dicts. On error or missing deps, returns [].
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return []

    url = "https://finder.futuresforall.org/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Crawl site starting from index to find opportunity/event links.
    def crawl_links(starts, max_pages=400, max_depth=3):
        from urllib.parse import urljoin, urlparse
        visited = set()
        queue = []
        candidates = set()
        for s in starts:
            queue.append((s, 0))
        # use domain of the primary start
        domain = urlparse(starts[0]).netloc if starts else ''
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
            # collect anchors that look like listings
            for a in doc.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(" ", strip=True)
                if not href:
                    continue
                full = href if href.startswith("http") else urljoin(cur, href)
                parsed = urlparse(full)
                if parsed.netloc != domain:
                    continue
                # skip auth, policy, or search pages that are not content
                if any(x in parsed.path.lower() for x in ("sign-in", "signin", "login", "privacy", "terms", "cookie", "account")):
                    continue
                path = parsed.path.lower()
                if any(k in path for k in ("opportunity", "opportunities", "event", "events", "work-experience", "experience", "detail", "listing")) or any(k in text.lower() for k in ("opportunity", "event", "experience", "work experience", "apply", "register")):
                    candidates.add(full)
                # follow internal page for further discovery
                if depth < max_depth and full not in visited:
                    queue.append((full, depth + 1))
        return list(candidates)

    # expand seed start pages: include potential listing/search entry points
    starts = [
        url,
        "https://finder.futuresforall.org/opportunities",
        "https://finder.futuresforall.org/events",
        "https://finder.futuresforall.org/search",
        "https://finder.futuresforall.org/listings",
        "https://finder.futuresforall.org/activities",
        "https://finder.futuresforall.org/schools",
    ]

    # attempt sitemap discovery to get URLs not linked from the homepage
    try:
        from urllib.parse import urljoin
        s_url = urljoin(url, "sitemap.xml")
        r = requests.get(s_url, timeout=8)
        if r.status_code == 200 and "<urlset" in r.text:
            import re
            locs = re.findall(r"<loc>(.*?)</loc>", r.text, re.I)
            for l in locs:
                if l and l.startswith("http"):
                    starts.append(l)
    except Exception:
        pass

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
        full = link if link.startswith("http") else f"{url.rstrip('/')}{link}"
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
        company = "Futures For All"

        try:
            jsonld = _parse_jsonld(doc)
            if jsonld:
                title = jsonld.get("title") or title
                if jsonld.get("deadline"):
                    deadline = jsonld.get("deadline")
                if jsonld.get("location"):
                    location = jsonld.get("location")
                if jsonld.get("company"):
                    company = jsonld.get("company")
        except Exception:
            pass

        if not title:
            h1 = doc.find("h1")
            title = clean_text(h1.get_text(" ", strip=True)) if h1 else None

        if not title:
            return None

        # description
        desc = ""
        article = doc.find("article")
        if article:
            desc = clean_text(article.get_text(" ", strip=True))
        else:
            meta = doc.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                desc = clean_text(meta["content"]) 

        # date heuristics
        deadline = ""
        date_node = doc.find(string=re.compile(r"\bDate\b[:]?", re.I))
        if date_node:
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

        # location/company heuristics
        company = "Futures For All"
        location = ""
        whole_text = doc.get_text(" ", strip=True)
        if re.search(r"\bonline\b|ONLINE EVENT|ONLINE event", whole_text):
            location = "Online"
        else:
            loc = doc.find(lambda t: t.name in ("p", "div") and re.search(r"\b(Location|Venue|Place)[:]?", t.get_text(" ", ""), re.I))
            if loc:
                t = loc.get_text(" ", strip=True)
                mloc = re.search(r"(?:Location|Venue|Place)[:]?\s*(.+)", t, re.I)
                if mloc:
                    location = clean_text(mloc.group(1))

        # try to find organiser/company label
        org = doc.find(string=re.compile(r"(Organiser|Provider|Company|Host|Hosted by)[:]?", re.I))
        if org:
            parent = org.parent
            text = parent.get_text(" ", strip=True)
            mm = re.search(r"(?:Organiser|Provider|Company|Host|Hosted by)[:\s]*(.+)", text, re.I)
            if mm:
                company = clean_text(mm.group(1))
        else:
            # derive from title if possible
            if title and ":" in title:
                part = title.split(":", 1)[1]
                candidate = part.split(",")[0].split("-")[0].strip()
                if len(candidate) > 0 and any(c.isalpha() for c in candidate):
                    company = clean_text(candidate)

        # fallback: derive company from URL slug when still generic
        if company in ("Futures For All", ""):
            try:
                from urllib.parse import urlparse
                parts = [p for p in urlparse(full).path.split('/') if p]
                if parts:
                    # pick last segment as candidate
                    slug = parts[-1]
                    cand = slug.replace('-', ' ').title()
                    if cand:
                        company = cand
            except Exception:
                pass

        detail = {
            "title": title,
            "company": company,
            "location": location,
            "deadline": deadline,
            "sector": "",
            "description": desc,
            "link": full,
            "source": "futures_finder",
        }

        # Validate: ensure it's likely an opportunity listing
        if (not detail["description"] or len(detail["description"]) < 30) and not detail["deadline"] and not detail["location"] and company == "Futures For All":
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
