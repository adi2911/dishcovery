import re
from collections import defaultdict

def boolean_search(query_tokens, index, field_map, operator='AND'):
    """
        Create a main function which will call 
    """
    if operator not in ['AND', 'OR', 'NOT']:
        raise ValueError("Operator must be 'AND', 'OR', or 'NOT'.")

    results = defaultdict(lambda: defaultdict(list))  # {doc_id: {field_name: [positions]}}

    if operator == 'AND':
        first_token = query_tokens[0]
        if first_token not in index:
            return {}
        candidate_docs = index[first_token]
        
        for doc_id, field_positions in candidate_docs.items():
            for field_id, positions in field_positions.items():
                match_found = True
                for token in query_tokens[1:]:
                    if token not in index or doc_id not in index[token] or field_id not in index[token]:
                        match_found = False
                        break
                if match_found:
                    results[doc_id][field_map[field_id]].extend(positions)

    elif operator == 'OR':
        for token in query_tokens:
            if token not in index:
                continue
            candidate_docs = index[token]
            for doc_id, field_positions in candidate_docs.items():
                for field_id, positions in field_positions.items():
                    results[doc_id][field_map[field_id]].extend(positions)

    elif operator == 'NOT':
        candidate_docs = set(index.keys())  
        for token in query_tokens:
            if token in index:
                token_docs = set(index[token].keys())
                candidate_docs -= token_docs

        for doc_id in candidate_docs:
            for field_id in index[next(iter(index))]:  
                results[doc_id][field_map[field_id]] = []

    return results

