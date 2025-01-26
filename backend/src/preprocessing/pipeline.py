#!/usr/bin/env python
import os
import json
import re
import Stemmer  
stemmer = Stemmer.Stemmer('english')

def load_stopwords_from_txt(filepath):
    '''Reads data/stopwords.txt file and returns set of stopwords lowercased'''
    stopwords_set = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            # Skip comment lines or empty lines
            if line == "" or line.startswith('#'):
                continue
            stopwords_set.add(line)
    return stopwords_set

def clean_text(text: str) -> str:
    '''Lowercase and remove non-alphanumeric characters except whitespace.
    Note: adjust regex some punctuation or digits should be retained.'''
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def tokenize(text: str):
    '''Tokenize text by splitting on any sequence of non-word characters.'''
    tokens = re.split(r'\W+', text)
    tokens = [t for t in tokens if t]
    return tokens

def remove_stopwords(tokens, stopwords_set):
    '''Removes tokens present in stopwords.'''
    return [t for t in tokens if t not in stopwords_set]

def stem_tokens(tokens):
    '''Stem each token using PyStemmer's porter2 (english).'''
    return [stemmer.stemWord(t) for t in tokens]

def preprocess_text(document: str, stopwords_set) -> list:
    '''Full preprocessing pipeline:
    1. Clean text (lowercase, remove punctuation)
    2. Regex tokenize
    3. Remove stopwords
    4. Stem words
    '''
    doc_clean = clean_text(document)
    tokens = tokenize(doc_clean)
    tokens_no_sw = remove_stopwords(tokens, stopwords_set)
    tokens_stemmed = stem_tokens(tokens_no_sw)
    return tokens_stemmed

def process_recipes(input_path: str, output_path: str, stopwords_path: str) -> None:
    '''Read the data/sample.jason recipes from input_path, load the stopwords from stopwords_path,
    preprocesses them, and write json file to output_path.'''
    with open(input_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    stopwords_set = load_stopwords_from_txt(stopwords_path)    
    processed_output = []
    for recipe in recipes:
        recipe_id = recipe.get('id', 'unknown_id')
        title = recipe.get('title', '')
        #Combine ingredients
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join([ing.get('text', '') for ing in ingredients])
        #Combine instructions
        instructions = recipe.get('instructions', [])
        instructions_text = ' '.join([inst.get('text', '') for inst in instructions])
        #Combine all text fields
        combined_text = f"{title} {ingredients_text} {instructions_text}"
        #Preprocess
        tokens = preprocess_text(combined_text, stopwords_set)
        processed_str = ' '.join(tokens)
        processed_recipe = {
            "id": recipe_id,
            "title": title,
            "processed_tokens": tokens,
            "processed_text": processed_str
        }
        processed_output.append(processed_recipe)
    # Write results to output
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(processed_output, out_f, indent=2, ensure_ascii=False)

def main():
    #Adjust these file paths as and when needed
    input_path = os.path.join('data', 'sample.json')
    output_path = os.path.join('data', 'sample_processed.json')
    stopwords_path = os.path.join('data', 'stopwords.txt')
    process_recipes(input_path, output_path, stopwords_path)
if __name__ == "__main__":
    main()
