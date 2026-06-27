# src/services/dedupe.py
def dedupe_by_link(items):
    seen = set()
    out = []
    for it in items:
        link = it.get("link", "").strip()
        if not link:
            out.append(it)
            continue
        if link in seen:
            continue
        seen.add(link)
        out.append(it)
    return out
