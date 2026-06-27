# src/services/clean_text.py
import html
import re


def clean_text(text: str) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # strip any simple HTML tags and decode common entities
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)

    # normalize whitespace and remove control characters
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    return text
