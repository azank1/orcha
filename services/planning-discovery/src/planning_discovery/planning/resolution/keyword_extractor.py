"""NLTK-based keyword extractor for the GIN inverted index filter."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_NLTK_READY = False


def _ensure_nltk() -> None:
    global _NLTK_READY  # noqa: PLW0603
    if _NLTK_READY:
        return
    try:
        import nltk

        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
        _NLTK_READY = True
    except LookupError:
        import nltk

        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        nltk.download("stopwords", quiet=True)
        _NLTK_READY = True


def extract_keywords(query: str) -> list[str]:
    """
    Extract meaningful keywords from *query* using NLTK.

    Filters out stop-words and single-character tokens.
    """
    _ensure_nltk()

    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize

    tokens = word_tokenize(query.lower())
    stop_words = set(stopwords.words("english"))

    keywords = [
        t
        for t in tokens
        if t.isalpha() and len(t) > 2 and t not in stop_words  # noqa: PLR2004
    ]
    logger.debug("Extracted keywords: %s", keywords)
    return keywords
