# src/categoriser/ml_classifier.py
# Optional: requires sentence-transformers and scikit-learn
import json
import os
from typing import Any, List

import requests

# Import dependencies individually so import failures are isolated and
# clearly reported (don't hide unrelated runtime errors).
SentenceTransformer = None
LogisticRegression = None
np = None
missing_deps = []
try:
    from sentence_transformers import SentenceTransformer
except (ImportError, ModuleNotFoundError):
    SentenceTransformer = None
    missing_deps.append("sentence-transformers")

try:
    from sklearn.linear_model import LogisticRegression
except (ImportError, ModuleNotFoundError):
    LogisticRegression = None
    missing_deps.append("scikit-learn")

try:
    import numpy as np
except (ImportError, ModuleNotFoundError):
    np = None
    missing_deps.append("numpy")


class SimpleEmbeddingClassifier:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        missing = []
        if SentenceTransformer is None:
            missing.append("sentence-transformers")
        if LogisticRegression is None:
            missing.append("scikit-learn")
        if np is None:
            missing.append("numpy")
        if missing:
            raise RuntimeError(
                "Missing dependencies: {}. Install required packages to use SimpleEmbeddingClassifier.".format(
                    ", ".join(missing)
                )
            )

        self.model = SentenceTransformer(model_name)
        self.clf = LogisticRegression(max_iter=1000)

    def fit(self, texts: List[str], labels: List[int]):
        X = self.model.encode(texts, show_progress_bar=False)
        self.clf.fit(X, labels)

    def predict(self, texts: List[str]):
        X = self.model.encode(texts, show_progress_bar=False)
        return self.clf.predict(X).tolist()


class LLMOpportunityValidator:
    DEFAULT_MODEL = "gpt-3.5-turbo"

    def __init__(self, api_key: str | None = None, model: str | None = None, api_base: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.available = bool(self.api_key)

    def validate_item(self, item: dict) -> bool:
        if not self.available:
            raise RuntimeError("OpenAI API key is required for LLM validation.")

        prompt = (
            "You are an assistant that checks scraped opportunity listings. "
            "Review the title, company, location, and description and decide whether this data is a valid student/work experience listing with natural listing phrasing. "
            "Return only a JSON object with keys 'valid' (true/false) and 'reason'."
            "\n\n"
            f"Title: {item.get('title', '').strip()}\n"
            f"Company: {item.get('company', '').strip()}\n"
            f"Location: {item.get('location', '').strip()}\n"
            f"Description: {item.get('description', '').strip()}\n"
            f"Source: {item.get('source', '').strip()}\n"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a data quality assistant for scraped opportunity listings."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 150,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        return self._parse_response(raw_text)

    @staticmethod
    def _parse_response(raw_text: str) -> bool:
        import re

        match = re.search(r"\{[\s\S]*\}", raw_text)
        if not match:
            return False

        def _valid_token(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("true", "yes", "1")
            return False

        try:
            parsed = json.loads(match.group(0))
            return _valid_token(parsed.get("valid", False))
        except json.JSONDecodeError:
            try:
                cleaned = raw_text.replace("'", '"')
                parsed = json.loads(cleaned)
                return _valid_token(parsed.get("valid", False))
            except Exception:
                return "true" in raw_text.lower() and "false" not in raw_text.lower()


class EmbeddingOpportunityValidator:
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    POSITIVE_EXAMPLES = [
        "Apply now for a virtual work experience placement in marketing, including live tasks and mentor feedback.",
        "This apprenticeship opportunity offers real-world business experience for students with a structured application process.",
        "A paid summer internship for school leavers with training, project work, and professional development.",
        "Join a virtual work experience program designed for students interested in technology and career exploration.",
    ]
    NEGATIVE_EXAMPLES = [
        "Click here to learn more about our privacy policy and cookie settings.",
        "Sign in to your account to manage your profile and billing information.",
        "This landing page contains marketing text about a product and a newsletter signup.",
        "Welcome to our website. Browse our services and contact us for more details.",
    ]

    def __init__(self, model_name: str | None = None):
        if SentenceTransformer is None or np is None:
            raise RuntimeError("Missing dependencies for embedding validation.")

        self.model = SentenceTransformer(model_name or self.DEFAULT_MODEL)
        self.positive_embs = self.model.encode(self.POSITIVE_EXAMPLES, show_progress_bar=False)
        self.negative_embs = self.model.encode(self.NEGATIVE_EXAMPLES, show_progress_bar=False)

    @staticmethod
    def _cosine(a: Any, b: Any) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom else 0.0

    def validate_item(self, item: dict) -> bool:
        text = " ".join([item.get("title", ""), item.get("description", ""), item.get("company", "")]).strip()
        if not text:
            return False

        emb = self.model.encode(text, show_progress_bar=False)
        pos_scores = [self._cosine(emb, e) for e in self.positive_embs]
        neg_scores = [self._cosine(emb, e) for e in self.negative_embs]
        return max(pos_scores, default=0.0) > max(neg_scores, default=0.0) + 0.08


class HeuristicOpportunityValidator:
    """Fallback validator when ML dependencies are not installed."""

    REQUIRED_FIELDS = ["title", "description", "company"]
    MIN_DESCRIPTION_LENGTH = 40
    MAX_TITLE_LENGTH = 260
    ALLOWED_SOURCE_KEYS = {"springpod", "uptree", "futures_finder"}

    @classmethod
    def is_valid(cls, item: dict) -> bool:
        if not isinstance(item, dict):
            return False

        if item.get("source") not in cls.ALLOWED_SOURCE_KEYS:
            return False

        for field in cls.REQUIRED_FIELDS:
            value = item.get(field)
            if not value or not isinstance(value, str) or len(value.strip()) < 5:
                return False

        if len(item["description"]) < cls.MIN_DESCRIPTION_LENGTH:
            return False

        if len(item["title"]) > cls.MAX_TITLE_LENGTH:
            return False

        if any(token in item["title"].lower() for token in ["click here", "read more", "learn more"]):
            return False

        # block pages that look like landing page content or tracking injections
        bad_phrases = ["gtag('config'", "window.dataLayer", "partner", "cookie notice"]
        if any(phrase in item.get("description", "").lower() for phrase in bad_phrases):
            return False

        return True


class OpportunityValidator:
    """Validates scraped opportunities and uses ML/LLM when available."""

    def __init__(self, llm_model: str | None = None, embed_model: str | None = None):
        self.llm_validator = None
        self.embedding_validator = None
        self.strategy = None

        try:
            self.llm_validator = LLMOpportunityValidator(model=llm_model)
            if self.llm_validator.available:
                self.strategy = self.llm_validator
        except Exception:
            self.llm_validator = None

        if self.strategy is None:
            try:
                self.embedding_validator = EmbeddingOpportunityValidator(model_name=embed_model)
                self.strategy = self.embedding_validator
            except Exception:
                self.embedding_validator = None

    def validate(self, items: list[dict]) -> list[dict]:
        if not items:
            return []

        validated = []
        for item in items:
            if HeuristicOpportunityValidator.is_valid(item):
                item["scrape_validation_passed"] = True
                if self.strategy is not None:
                    try:
                        item["scrape_validation_passed"] = self.strategy.validate_item(item)
                    except Exception:
                        item["scrape_validation_passed"] = True
                if item["scrape_validation_passed"]:
                    validated.append(item)
            else:
                item["scrape_validation_passed"] = False

        return validated
