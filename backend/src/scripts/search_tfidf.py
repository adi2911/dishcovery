import os
import lmdb
import pickle
import math
import json
from collections import defaultdict

# Global Stats (Should ideally be stored in LMDB)
N = 1029720  # Total number of documents (Update with actual value)

# Field Weights (Higher for title, medium for ingredients, low for instructions)
FIELD_WEIGHTS = {0: 1.5, 1: 1.2, 2: 1.0}

# Open LMDB environment
lmdb_path = os.path.join("data/inverted_index.lmdb", "inverted_index.lmdb_data.mdb")
env = lmdb.open(lmdb_path, readonly=True, subdir=False, lock=False)

# Compute TF-IDF weight
def compute_tfidf(tf, df, N):
    """Compute TF-IDF weight for a term in a document"""
    if tf == 0 or df == 0:
        return 0  # Avoid division by zero
    return (1 + math.log10(tf)) * math.log10(N / df)

# TF-IDF Search Function
def tfidf_search(query_terms, top_n=10):
    """Retrieve and rank documents using TF-IDF with field weighting."""
    doc_scores = defaultdict(float)  # Store TF-IDF scores per document

    with env.begin() as txn:
        for term in query_terms:
            key = term.encode('utf-8')
            data = txn.get(key)

            if data:
                term_data = pickle.loads(data)  # {doc_id: {field_id: [positions]}}
                df = len(term_data)  # Document Frequency (DF)

                for doc_id, fields in term_data.items():
                    for field_id, positions in fields.items():
                        tf = len(positions)  # Term Frequency (TF)

                        # Compute TF-IDF score
                        tfidf_score = compute_tfidf(tf, df, N)

                        # Apply Field Weighting
                        weight = FIELD_WEIGHTS.get(field_id, 1.0)
                        doc_scores[doc_id] += tfidf_score * weight  # Weighted score

    # Sort documents by final TF-IDF score
    ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    return ranked_docs[:top_n]  # Return top N results

# Example Query
query = ["chilli", "pasta"]
results = tfidf_search(query)

# Print Results
print("Top TF-IDF Results:")
for doc_id, score in results:
    print(f"Doc {doc_id}: TF-IDF Score = {score:.4f}")
