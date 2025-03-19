#!/usr/bin/env python
import os
import json
import re
from collections import defaultdict
import sys
from itertools import batched

import lmdb
import pickle
import time 
import Stemmer  
import numba
import math
import msgpack
from tqdm import tqdm

stemmer = Stemmer.Stemmer('english')

k1 = 1.2
b = 0.75
N = 1029720  # Total number of documents
FIELD_WEIGHTS = {0: 1.5, 1: 1.2, 2: 1.0}
total_doc_length = 78383226
avg_doc_length = total_doc_length/N

field_map = {
    "title": 0,
    "ingredients": 1,
    "instructions": 2
}

def load_stopwords_from_txt(filepath):
    """
    Reads data/stopwords.txt file and returns set of stopwords lowercased.
    """
    stopwords_set = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            if line == "" or line.startswith('#'):
                continue
            stopwords_set.add(line)
    return stopwords_set

def clean_text(text: str) -> str:
    """
    Lowercase and remove non-alphanumeric characters except whitespace.
    Adjust regex to keep digits or certain punctuation.
    """
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return text

def tokenize(text: str):
    tokens = re.split(r'\W+', text)
    tokens = [t for t in tokens if t]  # remove empty
    return tokens

def remove_stopwords(tokens, stopwords_set):
    return [t for t in tokens if t not in stopwords_set]

def stem_tokens(tokens):
    return [stemmer.stemWord(t) for t in tokens]

def preprocess_text(document: str, stopwords_set) -> list:
    """
    Full preprocessing pipeline for a chunk of text:
      1. Clean text (lowercase, remove punctuation)
      2. Regex tokenize
      3. Remove stopwords
    Returns a list of final tokens.
    """
    doc_clean = clean_text(document)
    tokens = tokenize(doc_clean)
    tokens_no_sw = remove_stopwords(tokens, stopwords_set)
    #tokens_stemmed = stem_tokens(tokens_no_sw)
    return tokens_no_sw

def preprocess_ingredient_line(line: str, stopwords_set) -> str:
    """
    Preprocess a single ingredient line (e.g., 'extra virgin olive oil')
    and return a single token with underscores (e.g., 'extra_virgin_olive_oil').
    
    - Cleans, tokenizes, removes stopwords
    - Joins resulting tokens with underscores
    """
    # Clean and tokenize like normal
    doc_clean = clean_text(line)
    tokens = tokenize(doc_clean)
    tokens_no_sw = remove_stopwords(tokens, stopwords_set)
    #tokens_stemmed = stem_tokens(tokens_no_sw)
    # Join them with underscores
    return " ".join(tokens_no_sw)

def process_recipes(recipes: json, stopwords_path: str):
    """
    1. Reads the data/sample.json recipes from input_path
    2. Loads the stopwords from stopwords_path
    3. Processes the data and writes JSON to output_path
       in the format:
         {
           "id": recipe_id,
           "title": [...title tokens...],
           "ingredients": [...ingredient tokens...],
           "instructions": [...instructions tokens...]
         }
    """
    # Load stopwords
    stopwords_set = load_stopwords_from_txt(stopwords_path)
    processed_output = []
    global total_doc_length

    n = 1
    for recipe in recipes:
        # Logging time
        sys.stdout.write(f"\r\033[KProcessed recipes: {n}")
        sys.stdout.flush()
        n +=1

        recipe_id = recipe.get('id', 'unknown_id')
        title = recipe.get('title', '')
        title_tokens = preprocess_text(title, stopwords_set)
        ingredients = recipe.get('ingredients', [])
        ingredient_tokens = []
        for ing in ingredients:
            line = ing.get('text', '')
            pieces = line.split(',')
            for piece in pieces:
                piece = piece.strip()
                if not piece:
                    continue
                token = preprocess_ingredient_line(piece, stopwords_set)
                if token:  
                    ingredient_tokens.append(token)
        instructions = recipe.get('instructions', [])
        instructions_text = ' '.join([inst.get('text', '') for inst in instructions])
        instructions_tokens = preprocess_text(instructions_text, stopwords_set)
        # Build final output structure
        processed_recipe = {
            "id": recipe_id,
            "title": title_tokens,
            "ingredients": ingredient_tokens,
            "instructions": instructions_tokens,
            "is_vegan": recipe.get('is_vegan'),
            "is_vegetarian": recipe.get('is_vegetarian'),
            "is_gluten_free": recipe.get('is_gluten_free')
        }
        recipe_len = len(processed_recipe.get("title")) + len(processed_recipe.get("ingredients")) + len(processed_recipe.get("instructions"))
        total_doc_length += recipe_len
        processed_output.append((processed_recipe, recipe_len))
    
    return processed_output

def convert_to_regular_dict(obj):
    """Recursively convert nested defaultdict objects into regular dicts."""
    if isinstance(obj, defaultdict):
        obj = dict(obj)  # convert top-level defaultdict to a dict
    if isinstance(obj, dict):
        for key, val in obj.items():
            obj[key] = convert_to_regular_dict(val)
    return obj

def build_inverted_idx(data, doc_id_start):
    """
    Builds inverted idx from tokenized JSON file for title, ingredients and steps
    """
    inverted_idx = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    doc_map = defaultdict()
    n = doc_id_start+1
    for idx, (doc, doc_len) in enumerate(data):
        doc_id = idx+doc_id_start+1
        if doc_id == 566321:
            continue

        # Logging time
        sys.stdout.write(f"\r\033[KIndexed recipes: {n}")
        sys.stdout.flush()
        n +=1

        # Compute dietary flags
        dietary_flags = (doc['is_vegan'] << 2) | (doc['is_vegetarian'] << 1) | doc['is_gluten_free']

        for field, field_id in field_map.items():
            tokens = doc[field]
            for pos, token in enumerate(tokens):
                inverted_idx[token][doc_id][field_id].append(pos+1)
                if 'doc_len' not in inverted_idx[token][doc_id]:
                    inverted_idx[token][doc_id]['doc_len'] = doc_len

                if 'dietary_flags' not in inverted_idx[token][doc_id]:
                    inverted_idx[token][doc_id]['dietary_flags'] = dietary_flags

                if '___' in inverted_idx[token]:
                    doc_frequency = len(inverted_idx[token]) -1
                    inverted_idx[token]['___'] = doc_frequency
                else:
                    doc_frequency = len(inverted_idx[token])
                    inverted_idx[token]['___'] = doc_frequency
        
        

        # doc_map[doc_id] = doc["id"]

    # with open(os.path.join('data', 'doc_map.json'), 'a') as map_file:
    #     json.dump(doc_map, map_file, indent=2)

    return inverted_idx

def merge_chunk_into_lmdb(chunk_idx, env):
    """
    Merge a partial inverted index chunk into the LMDB database.
    """
    with env.begin(write=True) as txn:
        for term, postings in chunk_idx.items():
            key = term.encode('utf-8')
            current_data = txn.get(key)
            if current_data is not None:
                # If key exists, load existing postings and merge with new ones
                existing_postings = msgpack.unpackb(current_data, raw=False, strict_map_key=False)

                for doc_id, field_dict in postings.items():
                    if doc_id == '___':
                        combined_freq = existing_postings[doc_id] + field_dict
                        existing_postings[doc_id] = combined_freq
                    elif doc_id in existing_postings:
                        for field_id, pos_list in field_dict.items():
                            existing_postings[doc_id].setdefault(field_id, [])
                            # Check for duplicates before merging:
                            combined = existing_postings[doc_id][field_id] + pos_list
                            unique = set(combined)
                            if len(combined) != len(unique):
                                print(f"Duplicate detected for term '{term}', doc {doc_id}, field {field_id}, combined {len(combined)}, unique {len(unique)}")
                            # Merge the new positions
                            existing_postings[doc_id][field_id].extend(pos_list)
                    else:
                        existing_postings[doc_id] = field_dict
                merged_postings = existing_postings
            else:
                merged_postings = postings

            regular_index = convert_to_regular_dict(merged_postings)
            txn.put(key, msgpack.packb(regular_index, use_bin_type=True))


# JIT-compiled helper function for computing BM25 and TF-IDF scores.
@numba.njit
def compute_scores(tf, doc_length, idf, k1, b, avg_doc_length, N, df):
    # Compute BM25 score
    bm25_score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avg_doc_length))))
    # Compute TF-IDF score (avoid log10(0) by ensuring tf > 0)
    tfidf_score = (1 + math.log10(tf)) * math.log10(N / df) if tf > 0 else 0.0
    return bm25_score, tfidf_score

def compute_idf(df, N):
        """Compute Inverse Document Frequency (IDF)"""
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

def bm25_tfidf_into_lmdb(lmdb_path, map_size):
    # Add BM25 and TF-IDF scores into the LMDB database.

    global total_doc_length
    env = lmdb.open(lmdb_path, map_size=map_size, subdir=True, create=True)

    with env.begin(write=True) as txn:
        cursor = txn.cursor()  # Create a cursor to iterate over key-value pairs
        total_keys = txn.stat()["entries"]

        for term, postings in tqdm(cursor.iternext(keys=True, values=True), total=total_keys, desc="Processing Keys", unit="key"):  # Iterate over all key-value pairs
            nested_dict = msgpack.unpackb(postings, raw=False, strict_map_key=False)  # Deserialize data

            # '___' holds the document frequency for the term.
            df = nested_dict.get('___', 0)
            idf = compute_idf(df, N)

            # loop through doc_set only.
            for doc_id, inner_dict in nested_dict.items():
                bm25 = 0
                tfidf = 0
                if isinstance(inner_dict, dict):
                    for field_id, positions in inner_dict.items():
                        if isinstance(positions, list):
                            tf = len(positions)
                            weight = FIELD_WEIGHTS.get(field_id, 1.0)
                            # Get the document length; default to avg_doc_length if unknown.
                            doc_length = inner_dict.get('doc_len')
                            
                            # Compute the BM25 and TF-IDF scores using the JIT-compiled helper.
                            bm25_score, tfidf_score = compute_scores(tf, doc_length=doc_length, idf=idf, k1=k1, b=b, avg_doc_length=(total_doc_length/N), N=N, df=df)

                            bm25 += bm25_score * weight
                            tfidf += tfidf_score * weight
                
                if isinstance(inner_dict, dict):  # Ensure it's a nested dictionary
                    inner_dict['bm25'] = bm25
                    inner_dict['tfidf'] = tfidf

            # Re-pickle the updated dictionary
            updated_value = msgpack.packb(nested_dict, use_bin_type=True)

            # Put the updated value back into LMDB
            txn.put(term, updated_value)

# Main batch Processing function with progress bars
def process_and_index_in_batches(raw_data_path, stopwords_path, lmdb_path, map_size, chunk_size=10000):
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    # Open LMDB environment for writing.
    env = lmdb.open(lmdb_path, map_size=map_size, subdir=True, create=True)

    total_recipes = len(recipes)
    print(f"Total recipes: {total_recipes}\n")

    # Outer progress bar for batches
    for i in tqdm(range(0, total_recipes, chunk_size), desc="Processing Batches"):
        batch = recipes[i:i+chunk_size]
        print(f"\nProcessing batch: {i} to {i + len(batch)}\n")

        # --- Pre-processing Batch ---
        start_time = time.perf_counter()
        # If process_recipes processes one recipe at a time, you can add a progress bar there.
        # Here we assume process_recipes returns the entire processed batch.
        processed_batch = process_recipes(batch, stopwords_path)
        end_time = time.perf_counter()
        print(f"\nPre-Processing execution time: {end_time - start_time:.2f} seconds\n")

        # --- Indexing Batch ---
        start_time = time.perf_counter()
        # Wrap the call to build_inverted_idx with a tqdm progress bar if desired.
        # For example, if build_inverted_idx iterates over documents, you can modify that function to use tqdm.
        partial_index = build_inverted_idx(processed_batch, i)
        end_time = time.perf_counter()
        print(f"\nIndexing execution time: {end_time - start_time:.2f} seconds\n")

        # --- Merging LMDB file ---
        start_time = time.perf_counter()
        merge_chunk_into_lmdb(partial_index, env)
        end_time = time.perf_counter()
        print(f"LMDB update execution time: {end_time - start_time:.2f} seconds\n")

        # Clear variables to free memory
        del processed_batch, partial_index

    env.close()
    print("\nLMDB database created at:", lmdb_path)

def main():
    global total_doc_length
    #Raw data_file path
    input_path = r'D:\Desk\UoE\TTDS_project\dishcovery\backend\src\data\label_layer1.json'
    # LMDB key-value db
    lmdb_path = r'D:\Desk\UoE\TTDS_project\dishcovery\backend\src\data\test.lmdb'
    # Stop words path
    stopwords_path = r'D:\Desk\UoE\TTDS_project\dishcovery\backend\src\data\stop_words_english.txt'
    # Adjust map_size based on your expected database size.
    map_size = int(10 * (1024 ** 3))

    start_time = time.perf_counter()
    process_and_index_in_batches(input_path, stopwords_path, lmdb_path, chunk_size=100000, map_size=map_size)
    end_time = time.perf_counter()
    print(f"Total processing and indexing time: {end_time - start_time:.2f} seconds")
    print(f'Total Documents length: {total_doc_length}')

    start_time = time.perf_counter()
    bm25_tfidf_into_lmdb(lmdb_path=lmdb_path, map_size=map_size)
    end_time = time.perf_counter()
    print(f"Total update time: {end_time - start_time:.2f} seconds")

    # with open(output_path, 'w') as file:
    #     json.dump(inverted_index, file, indent=4)

if __name__ == "__main__":
    main()

