import os
import lmdb
import pickle
import json
import math
from collections import defaultdict

# BM25 Hyperparameters
k1 = 1.2
b = 0.75

# Field Weights
FIELD_WEIGHTS = {0: 1.5, 1: 1.2, 2: 1.0}  # Title > Ingredients > Instructions

# Global Stats (Should ideally be stored in LMDB)
N = 1029720  # Total number of documents
avg_doc_length = 170  # Approximate average document length (assumed)


# Open LMDB environment
lmdb_path = os.path.join("data/inverted_index.lmdb", "inverted_index.lmdb_data.mdb")
env = lmdb.open(lmdb_path, readonly=True, subdir=False, lock=False)

# Compute IDF
def compute_idf(df, N):
    """Compute Inverse Document Frequency (IDF)"""
    return math.log((N - df + 0.5) / (df + 0.5) + 1)

# BM25 Search Function
def bm25_search(query_terms, top_n=1000):
    """Retrieve and rank documents using BM25 with field weighting."""
    doc_scores = defaultdict(float)  # Store BM25 scores per document
    doc_lengths = {}  # If document lengths were stored, retrieve them

    with env.begin() as txn:
        for term in query_terms:
            key = term.encode('utf-8')
            data = txn.get(key)

            if data:
                term_data = pickle.loads(data)  # {doc_id: {field_id: [positions]}}
                df = len(term_data)  # Document Frequency (DF)

                # Compute IDF
                idf = compute_idf(df, N)

                for doc_id, fields in term_data.items():
                    for field_id, positions in fields.items():
                        term_freq = len(positions)  # TF = Number of occurrences
                        doc_length = doc_lengths.get(doc_id, avg_doc_length)  # Use avg length if unknown

                        # Compute BM25 for this term in this field
                        bm25_score = idf * ((term_freq * (k1 + 1)) / 
                                            (term_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))))

                        # Apply Field Weighting
                        weight = FIELD_WEIGHTS.get(field_id, 1.0)
                        doc_scores[doc_id] += bm25_score * weight  # Weighted score

    # Sort documents by final BM25 score
    ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    return ranked_docs[:top_n]  # Return top N results

# Example Query
query = ["chilli", "pasta"]
results = bm25_search(query)

# Print Results
print("Top BM25 Results:")
for doc_id, score in results:
    print(f"Doc {doc_id}: BM25 Score = {score:.4f}")





