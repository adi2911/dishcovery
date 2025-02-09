import math
from collections import defaultdict


def phrase_search(query_tokens, index, field_map):
    if len(query_tokens) < 2:
        return {}

    results = defaultdict(lambda: defaultdict(list))  # {doc_id: {field_id: [start_pos]}}

    first_token = query_tokens[0]
    if first_token not in index:
        return {}

    candidate_docs = index[first_token]

    for doc_id, field_positions in candidate_docs.items():
        for field_id, positions in field_positions.items():
            for pos in positions:
                match_found = True
                for i, token in enumerate(query_tokens[1:], start=1):
                    if token not in index or doc_id not in index[token] or field_id not in index[token]:
                        match_found = False
                        break
                    if (pos + i) not in index[token][doc_id][field_id]:
                        match_found = False
                        break
                if match_found:
                    results[doc_id][field_map[field_id]].append(pos)

    return results


def proximity_search(query_tokens, index, field_map, max_distance=None):
    if len(query_tokens) < 2:
        return {}

    if max_distance is None:
        max_distance = len(query_tokens) + 2

    results = defaultdict(lambda: defaultdict(list))  # {doc_id: {field_id: [matched_positions]}}
    first_token = query_tokens[0]

    if first_token not in index:
        return {}

    candidate_docs = index[first_token]

    for doc_id, field_positions in candidate_docs.items():
        for field_id, positions in field_positions.items():
            for pos in positions:
                match_positions = {pos}
                for token in query_tokens[1:]:
                    if token not in index or doc_id not in index[token] or field_id not in index[token]:
                        break
                    token_positions = set(index[token][doc_id][field_id])
                    new_matches = set()
                    for p in match_positions:
                        valid_positions = {p + i for i in range(-max_distance, max_distance + 1)}
                        new_matches.update(token_positions.intersection(valid_positions))
                    if not new_matches:
                        break
                    match_positions = new_matches
                else:
                    results[doc_id][field_map[field_id]].extend(sorted(match_positions))

    return results


def compute_tfidf(search_results, total_docs):
    tfidf_scores = defaultdict(lambda: defaultdict(float))  # {doc_id: {field_name: score}}

    doc_freq = defaultdict(int)
    for doc_id, fields in search_results.items():
        for field_name in fields:
            doc_freq[field_name] += 1

    for doc_id, fields in search_results.items():
        for field_name, positions in fields.items():
            tf = len(positions)
            idf = math.log10(total_docs / doc_freq[field_name])
            tfidf_scores[doc_id][field_name] = tf * idf  # {doc_id: {field_name: score}}

    return tfidf_scores


def compute_document_score(tfidf_scores):
    weights = {"title": 0.5, "ingredients": 0.3, "steps": 0.2}

    document_scores = defaultdict(float)  # {doc_id: combined_score}

    for doc_id, fields in tfidf_scores.items():
        for field_name, score in fields.items():
            document_scores[doc_id] += score * weights.get(field_name, 0)

    return document_scores