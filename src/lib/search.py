from __future__ import annotations

from typing import Iterable

from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _normalize_strings(corpus: Iterable[str]) -> list[str]:
    return [text.strip() for text in corpus if isinstance(text, str) and text.strip()]


def cosine_search(search_string: str, corpus: Iterable[str], threshold: float = 0.15):
    texts = _normalize_strings(corpus)
    if not search_string or not texts:
      return []

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([search_string] + texts)
    query_vector = tfidf_matrix[0]
    corpus_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(query_vector, corpus_vectors).flatten()

    ranked = [
        {"text": texts[index], "score": float(similarities[index])}
        for index in range(len(texts))
        if similarities[index] >= threshold
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def fuzzy_match(search_string: str, corpus: Iterable[str], threshold: int = 60):
    texts = _normalize_strings(corpus)
    if not search_string or not texts:
        return []

    ranked = [
        {"text": text, "score": fuzz.token_set_ratio(search_string.lower(), text.lower())}
        for text in texts
        if fuzz.token_set_ratio(search_string.lower(), text.lower()) >= threshold
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def hybrid_search(
    search_string: str,
    corpus: Iterable[str],
    cosine_threshold: float = 0.15,
    fuzzy_threshold: int = 60,
    limit: int | None = None,
):
    texts = _normalize_strings(corpus)
    if not search_string or not texts:
        return []

    cosine_hits = {
        item["text"]: item["score"]
        for item in cosine_search(search_string, texts, threshold=cosine_threshold)
    }
    fuzzy_hits = {
        item["text"]: item["score"] / 100
        for item in fuzzy_match(search_string, texts, threshold=fuzzy_threshold)
    }

    ranked = []
    for text in texts:
        score = max(cosine_hits.get(text, 0), fuzzy_hits.get(text, 0))
        if score:
            ranked.append({"text": text, "score": float(score)})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit] if limit else ranked


def search_wrapper(
    search_string: str,
    corpus: Iterable[str],
    method: str = "hybrid",
    threshold: float = 0.15,
    limit: int | None = None,
):
    if method == "cosine":
        return cosine_search(search_string, corpus, threshold=threshold)
    if method == "fuzzy":
        return fuzzy_match(search_string, corpus, threshold=int(threshold * 100))
    if method == "hybrid":
        return hybrid_search(search_string, corpus, cosine_threshold=threshold, limit=limit)
    raise ValueError(f"Unsupported search method: {method}")
