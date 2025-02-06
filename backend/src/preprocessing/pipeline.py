#!/usr/bin/env python
import os
import json
import re

import Stemmer  
stemmer = Stemmer.Stemmer('english')

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

def process_recipes(input_path: str, output_path: str, stopwords_path: str) -> None:
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
    for recipe in recipes:
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
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(processed_output, out_f, indent=2, ensure_ascii=False)

def main():
    #Adjust paths as needed
    input_path = os.path.join('data', 'sample.json')
    output_path = os.path.join('data', 'sample_processed.json')
    stopwords_path = os.path.join('data', 'stopwords.txt')
    
    process_recipes(input_path, output_path, stopwords_path)

if __name__ == "__main__":
    main()
