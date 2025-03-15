# ----- required imports -----

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import numpy as np
from scipy.spatial.distance import cdist
from datasketch import MinHash, MinHashLSH

# ----- helper functions -----


def cosine_search(search_string, corpus, threshold=0.5):
    all_texts = [search_string] + corpus
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    query_vector = tfidf_matrix[0]
    corpus_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(query_vector, corpus_vectors).flatten()
    results = [
        (corpus[i], similarities[i])
        for i in range(len(corpus))
        if similarities[i] >= threshold
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def fuzzy_match(search_string, corpus, threshold=70):
    results = [
        (text, fuzz.ratio(search_string.lower(), text.lower())) for text in corpus
    ]
    filtered_results = [(text, score) for text, score in results if score >= threshold]
    filtered_results.sort(key=lambda x: x[1], reverse=True)
    return filtered_results


def semantic_search(search_string, corpus_embeddings, query_embedding, threshold=0.5):
    similarities = cosine_similarity([query_embedding], corpus_embeddings).flatten()
    results = [
        (i, similarities[i])
        for i in range(len(corpus_embeddings))
        if similarities[i] >= threshold
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def lsh_search(search_string, corpus, threshold=0.5):
    lsh = MinHashLSH(threshold=threshold)
    minhashes = []
    for i, doc in enumerate(corpus):
        m = MinHash()
        for word in doc.split():
            m.update(word.encode("utf8"))
        lsh.insert(f"doc-{i}", m)
        minhashes.append(m)
    query_minhash = MinHash()
    for word in search_string.split():
        query_minhash.update(word.encode("utf8"))
    result_indices = lsh.query(query_minhash)
    return [corpus[int(idx.split("-")[1])] for idx in result_indices]


def search_wrapper(
    search_string, corpus, method="cosine", threshold=0.5, embeddings=None
):
    if method == "cosine":
        return find_similar_strings(search_string, corpus, threshold)
    elif method == "fuzzy":
        return fuzzy_match(search_string, corpus, int(threshold * 100))
    elif method == "semantic":
        if embeddings is None:
            raise ValueError("Embeddings must be provided for semantic search.")
        query_embedding = embeddings[0]
        return semantic_search(
            search_string, embeddings[1:], query_embedding, threshold
        )
    elif method == "lsh":
        return lsh_search(search_string, corpus, threshold)
