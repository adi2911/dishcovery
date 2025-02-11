#!/usr/bin/env python
import os
import json
import re
from collections import defaultdict
import sys

import Stemmer  
stemmer = Stemmer.Stemmer('english')

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
    return "_".join(tokens_no_sw)

def process_recipes(input_path: str, stopwords_path: str) -> None:
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
    # Load recipes
    with open(input_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    # Load stopwords
    stopwords_set = load_stopwords_from_txt(stopwords_path)
    processed_output = []

    n = 1
    for recipe in recipes:
        # Logging time
        sys.stdout.write(f"Processed recipes: {n}\n")
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
            "instructions": instructions_tokens
        }
        processed_output.append(processed_recipe)
    
    return processed_output


def build_inverted_idx(data):
    """
    Builds inverted idx from tokenized JSON file for title, ingredients and steps
    """
    inverted_idx = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    doc_map = defaultdict()
    n = 1
    for idx, doc in enumerate(data):
        doc_id = idx+1

        # Logging time
        sys.stdout.write(f"Indexed recipes: {n}\n")
        sys.stdout.flush()
        n +=1

        for field, field_id in field_map.items():
            tokens = doc[field]
            for pos, token in enumerate(tokens):
                inverted_idx[token][doc_id][field_id].append(pos+1)

        doc_map[doc_id] = doc["id"]
    
    with open(os.path.join('data', 'doc_map.json'), 'w') as map_file:
        json.dump(doc_map, map_file, indent=2)

    return inverted_idx

def main():
    #Adjust paths as needed
    input_path = os.path.join('data', 'layer1.json')
    output_path = os.path.join('data', 'indexed_processed.json')
    stopwords_path = os.path.join('data', 'stopwords.txt')
    
    data = process_recipes(input_path, stopwords_path)

    inverted_index = build_inverted_idx(data)

    with open(output_path, 'w') as file:
        json.dump(inverted_index, file, indent=4)

if __name__ == "__main__":
    main()

