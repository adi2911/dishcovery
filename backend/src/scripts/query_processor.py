import pprint
import re
import Stemmer
import datetime
import time
import json
from collections import OrderedDict, defaultdict
import logging
import google.auth
import os
import lmdb
import json
import math
from collections import defaultdict
import os
import json
import google.cloud.secretmanager as secretmanager
from google.cloud.sql.connector import Connector
from cache_utils import QueryCache, DocCache
import numpy as np
import math
import pickle
from collections import defaultdict
import numba
import cProfile
import pstats
import heapq
import msgpack
from global_path import get_relative_path

profiler = cProfile.Profile()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Query Processing Module")
)



import queue
import threading

class ConnectionPool:
    def __init__(self, connection_factory, maxsize=5):
        self.connection_factory = connection_factory
        self.pool = queue.Queue(maxsize)
        self.maxsize = maxsize
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self.maxsize):
            self.pool.put(self.connection_factory())

    def get_connection(self):
        conn = self.pool.get()
        # Validate the connection using a simple query.
        if not self._is_valid(conn):
            conn = self.connection_factory()
        return conn

    def release_connection(self, conn):
        self.pool.put(conn)

    def _is_valid(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            return True
        except Exception:
            return False


class QueryProcessor:
    def __init__(self, stop_word_path=None, use_stopwords=True, use_stemming=True):
        """
        Initializes the QueryProcessor module

        Args:
            stop_word_path (str, optional): Path to stopwords file
            use_stopwords (bool, optional): Whether to remove stopwords (default: True)
            use_stemming (bool, optional): Whether to apply stemming (default: True)
        """
        self.stop_word_path = stop_word_path
        self.use_stopwords = use_stopwords
        self.use_stemming = use_stemming
        # Cache to avoid repeated LMDB lookups.
        self.token_cache = OrderedDict()
        self.cache_limit = 10000
        self.stop_words_set = self._load_stopwords() if use_stopwords and stop_word_path else set()
        self.stemmer = Stemmer.Stemmer("english")
        self.FIELD_WEIGHTS = {0: 1.5, 1: 1.2, 2: 1.0}
        self.k1 = 1.2
        self.b = 0.75
        self.N = 1029720  # Total number of documents
        self.avg_doc_length = 170  # Approximate average document length (assumed)
        self.lmdb_path = get_relative_path("data", "index_data_dishcovery/inverted_index_2.lmdb/data.mdb")
        self.env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)
        self.syn_path = get_relative_path("api", "ingredient_synonyms_mapping.json")


        self.PROJECT_ID = "dishcovery-449618"
        # self.conn = self.get_connection()
        self.db_pool = ConnectionPool(self.create_new_connection, maxsize=5)


    def _load_stopwords(self):
        """
        Loads stopwords from the stopword file
        """
        with open(self.stop_word_path, 'r') as file:
            return set(file.read().split())

    def text_cleaner(self, text):
        """
        Cleans the input text by removing special characters, performing case folding,
        replacing hyphens with spaces, and removing extra spaces.

        Args:
            text (str): The input text to be cleaned

        Returns:
            str: The cleaned text
        """
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s-]", '', text).lower().replace("\n", ' ').replace("  ", " ").replace('-',
                                                                                                                  ' ')
        cleaned_text = re.sub(' +', ' ', cleaned_text)
        return cleaned_text

    def text_tokenizer(self, text):
        """
        Tokenizes the input text by splitting it into a list of words.

        Args:
            text (str): The input string to be tokenized

        Returns:
            list: List of words obtained by splitting the input text
        """
        return text.split()

    def stopword_remover(self, tokens):
        """
        Removes stopwords from the given text.

        Args:
            tokens (list of str): List of tokenized words

        Returns:
            list of str: The text with stopwords removed
        """
        return [word for word in tokens if word not in self.stop_words_set]

    def text_stemmer(self, tokens):
        """
        Stems the words in the given text using the Advanced english porter stemming algorithm.

        Args:
            tokens (list of str): List of words to be stemmed

        Returns:
            list of str: List of stemmed words
        """
        return [self.stemmer.stemWord(word) for word in tokens]

    def extract_boolean_operators(self, query):
        """
        Extracts boolean operators (AND, OR, NOT) from the query

        Args:
            query (str): Input query

        Returns:
            list: List of extracted Boolean operators
        """
        ops = re.findall(r'\b(AND|OR|NOT)\b', query)
        return ops

    def extract_phrases(self, query):
        """
        Extracts phrases from the query enclosed in double quotes

        Args:
            query (str): Input query

        Returns:
            list: List of detected phrase queries
        """
        phrases_queries = re.findall(r'"(.*?)"|\'(.*?)\'', query)
        return phrases_queries

    def query_n_gram(self, processed_query):
        """
        Appends bigrams and trigrams of all words in the processed query (tokenised)

        Args:
            processed_query (dict): Processed query containing key 'processed_tokens' which is processed token list

        Returns:
            dict: Processed query with 'processed_tokens' appended with bigram and trigram tokens
        """
        logging.info("Generating n-grams for the processed query")
        start_time = datetime.datetime.now()

        tokens = processed_query['tokens']
        bigrams = [tokens[i] + " " + tokens[i + 1] for i in range(len(tokens) - 1)]
        trigrams = [tokens[i] + " " + tokens[i + 1] + " " + tokens[i + 2] for i in range(len(tokens) - 2)]

        processed_query['n_grams'].extend(bigrams)
        processed_query['n_grams'].extend(trigrams)

        logging.info("n-grams generation completed in {}".format(datetime.datetime.now() - start_time))
        # return processed_query

    def query_expansion_PRF(self, query):
        pass

    def process_query_text(self, query, exclude_tokens):
        """
        Processes query by running text cleaning,tokenisation and stemming and parsing query operators for boolean
        and phrase queries. Also implements query expansion.

        Args:
            query (str): The input search query

        Returns:
            dict: Processed query with parsed components for boolean, search etc
        """
        logging.info("Processing Query: {}".format(query))
        start_time = datetime.datetime.now()

        # Inititalise processed query dict
        processed_query = {"original_query": query,
                           # "processed_query": "", NOT REQUIRED
                           "n_grams": [],  # remove underscore
                           "synonyms": [],  # TO_DO
                           "tokens": [],
                           "exclude_tokens": exclude_tokens
                           }

        processed_query['phrase_queries'] = self.extract_phrases(query)
        # processed_query['boolean_operators'] = self.extract_boolean_operators(query) NOT REQUIRED

        # Clean and tokenize the query
        cleaned_query = self.text_cleaner(query)
        tokenised_query = self.text_tokenizer(cleaned_query)
        print("Initial exclude tokens: " + str(exclude_tokens))

        if self.use_stopwords:
            tokenised_query = self.stopword_remover(tokenised_query)

        if len(tokenised_query) == 0:
            return "No tokens found"

        # Store the pre-stemmed tokens for synonym expansion
        pre_stemmed_tokens = tokenised_query.copy()

        # Expand query with synonyms BEFORE stemming
        synonyms = self.get_synonyms_for_tokens(pre_stemmed_tokens)
        processed_query['synonyms'] = synonyms

        # Combine original tokens with synonyms for stemming
        all_tokens = tokenised_query + synonyms

        print("Query now:")
        print(synonyms)

        # Apply stemming to all tokens (original + synonyms) if enabled
        if self.use_stemming:
            stemmed_tokens = self.text_stemmer(tokenised_query)
            processed_query['synonyms'] = self.text_stemmer(synonyms)
            tokenized_exclusions = self.text_stemmer(exclude_tokens)
            processed_query['tokens'] = stemmed_tokens
            processed_query['exclude_tokens'] = tokenized_exclusions
        else:
            processed_query['tokens'] = tokenised_query
            processed_query['exclude_tokens'] = exclude_tokens

        # Generate n-grams
        self.query_n_gram(processed_query)

        processed_query['tokens']=processed_query['tokens']+processed_query['synonyms']

        logging.info("Query processing completed in {}".format(datetime.datetime.now() - start_time))
        return processed_query

    def get_synonyms_for_tokens(self, tokens):
        """
        Gets synonyms for tokens from ingredient_synonym_mapping.

        Args:
            tokens (list): List of tokens to find synonyms for

        Returns:
            list: List of synonym tokens (up to 3 per original token)
        """
        try:
            all_synonyms = []

            # Load the ingredient synonym mapping from JSON file
            with open(self.syn_path, 'r') as f:
                ingredient_synonyms = json.load(f)

            # For each token in the query, find synonyms
            for token in tokens:
                if token in ingredient_synonyms:
                    # Get top 3 synonyms (or fewer if less are available)
                    token_synonyms = ingredient_synonyms[token][:5]
                    all_synonyms.extend(token_synonyms)

            # Return unique synonyms
            return list(set(all_synonyms))

        except Exception as e:
            logging.error(f"Error getting synonyms: {str(e)}")
            # If there's an error, return empty list
            return []
    
    def preprocess_ingredient_query(self, ingredient):

        cleaned = ingredient.lower()
        cleaned = re.sub(r'\d+', '', cleaned)
        cleaned = re.sub(r'[^a-z\s]', '', cleaned)
        tokens = re.split(r'\W+', cleaned)
        tokens = [t for t in tokens if t]
        if self.use_stopwords:
            tokens = self.stopword_remover(tokens)
        if self.use_stemming:
            tokens = self.text_stemmer(tokens)
        phrase = " ".join(tokens)
        return phrase, tokens


    def process_query_ingredients(self, query, exclude_tokens):
        logging.info("Processing Ingredients Query: {}".format(query))
        processed_query = {
            "ingredient_phrases": [],
            "ingredient_tokens": [],
            "exclude_tokens": []
        }
        # Process each queried ingredient using the same preprocessing as indexing.
        for ing in query:
            phrase, tokens = self.preprocess_ingredient_query(ing)
            processed_query["ingredient_phrases"].append(phrase)
            # Optionally, you can also include individual tokens for ranking.
            processed_query["ingredient_tokens"].extend(tokens)
        # Process exclude tokens similarly.
        for ex in exclude_tokens:
            phrase, tokens = self.preprocess_ingredient_query(ex)
            processed_query["exclude_tokens"].extend(tokens)
        return processed_query

    def get_ranked_documents(self, processed_query, dietary_preference, isText):
        '''
        Takes the query details as JSON, processes the search and ranks the documents.
        Input: {
                "original_query": query,
                "processed_query": "", NOT REQUIRED
                "n_grams": []  ,  # List of n-grams (e.g., bigrams, trigrams)
                "synonyms":[],  # Synonyms to be considered (TO_DO)
                "tokens": [],   # Tokens from the query
                "exclude_tokens": exclude_tokens  # Tokens to exclude
            }

      '''
        # 1 - Get exclude tokens' document IDs
        exclude_docs = set()
        print(processed_query)
        
        with self.env.begin() as txn:
            for token in processed_query.get('exclude_tokens', []):
                token_results = self.search_index(token,txn)
                if token_results:
                    exclude_docs.update(token_results.keys())

        matching_docs = set()
        proximity_scores = defaultdict(float)

        if isText:
            print("Text-based search")
            start = time.time()
            ranked_docs = self.text_search(processed_query, exclude_docs, dietary_preference)
            print(f'RANKED DOCS| time to get ranked docs:  {time.time() - start}')
            return sorted(ranked_docs.items(), key=lambda x: x[1], reverse=True)[:1000]
        else:
            print("Ingredients-based search")
            doc_scores_bm25 = defaultdict(float)
            doc_scores_tfidf = defaultdict(float)
            
            exclude_docs = set()
            with self.env.begin() as txn:
                for token in processed_query.get('exclude_tokens', []):
                    token_results = self.search_index(token, txn)
                    if token_results:
                        exclude_docs.update(token_results.keys())
            
            phrase_docs = set()
            token_docs = set()
            PHRASE_WEIGHT = 1.5  # boost factor for full phrase matches

            with self.env.begin() as txn:
                for phrase in processed_query.get("ingredient_phrases", []):
                    token_data = self.get_token_result(phrase, txn)
                    if token_data:
                        phrase_docs.update(token_data.keys())
                        for doc_id, scores in token_data.items():
                            dietary_flags = scores.get('dietary_flags', 0)
                            if dietary_preference:
                                is_vegan = (dietary_flags & 0b100) >> 2
                                is_vegetarian = (dietary_flags & 0b010) >> 1
                                is_gluten_free = (dietary_flags & 0b001)
                                if dietary_preference == 1 and not is_vegan:
                                    continue
                                if dietary_preference == 2 and not is_vegetarian:
                                    continue
                                if dietary_preference == 3 and not is_gluten_free:
                                    continue
                            doc_scores_bm25[doc_id] += scores.get('bm25', 0) * PHRASE_WEIGHT
                            doc_scores_tfidf[doc_id] += scores.get('tfidf', 0) * PHRASE_WEIGHT

                for token in processed_query.get("ingredient_tokens", []):
                    token_data = self.get_token_result(token, txn)
                    if token_data:
                        token_docs.update(token_data.keys())
                        for doc_id, scores in token_data.items():
                            dietary_flags = scores.get('dietary_flags', 0)
                            if dietary_preference:
                                is_vegan = (dietary_flags & 0b100) >> 2
                                is_vegetarian = (dietary_flags & 0b010) >> 1
                                is_gluten_free = (dietary_flags & 0b001)
                                if dietary_preference == 1 and not is_vegan:
                                    continue
                                if dietary_preference == 2 and not is_vegetarian:
                                    continue
                                if dietary_preference == 3 and not is_gluten_free:
                                    continue
                            doc_scores_bm25[doc_id] += scores.get('bm25', 0)
                            doc_scores_tfidf[doc_id] += scores.get('tfidf', 0)

            matching_docs = (phrase_docs.union(token_docs)) - exclude_docs

            start = time.time()
            bm25_scores = self.get_top_n_scores(doc_scores_bm25, matching_docs, 10000)
            tfidf_scores = self.get_top_n_scores(doc_scores_tfidf, matching_docs, 10000)
            print(f'Ranking step: {time.time() - start} seconds')

            start = time.time()
            max_bm25 = max(bm25_scores.values(), default=1)
            min_bm25 = min(bm25_scores.values(), default=0)
            max_tfidf = max(tfidf_scores.values(), default=1)
            min_tfidf = min(tfidf_scores.values(), default=0)
            bm25_weight, tfidf_weight = 0.5, 0.3

            import numpy as np
            doc_ids = np.array(list(matching_docs))
            bm25_arr = np.array([bm25_scores.get(doc_id, min_bm25) for doc_id in doc_ids])
            tfidf_arr = np.array([tfidf_scores.get(doc_id, min_tfidf) for doc_id in doc_ids])
            norm_bm25 = (bm25_arr - min_bm25) / (max_bm25 - min_bm25 + 1e-9)
            norm_tfidf = (tfidf_arr - min_tfidf) / (max_tfidf - min_tfidf + 1e-9)
            weighted_scores = (bm25_weight * norm_bm25 + tfidf_weight * norm_tfidf)
            ranked_docs = dict(zip(doc_ids, weighted_scores))
            print(f'Merging ranks: {time.time() - start} seconds')
            print("Length of ranked_docs in ingredients search: " + str(len(ranked_docs)))
            return sorted(ranked_docs.items(), key=lambda x: x[1], reverse=True)[:1000]

    def compute_idf(self, df, N):
        """Compute Inverse Document Frequency (IDF)"""
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    def tfidf_search(self, doc_set, query_terms, top_n=10):
        # env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)
        doc_scores = defaultdict(float)

        with self.env.begin() as txn:
            for term in query_terms:
                key = term.encode('utf-8')
                data = txn.get(key)

                if data:
                    term_data = msgpack.unpackb(data, raw=False, strict_map_key=False)
                    df = term_data.pop('___', 0)
                    # Why are we iterating over every document, we can just iterate the doc_set adn get the doc from there.
                    for doc_id, fields in term_data.items():
                        if doc_id not in doc_set:
                            continue

                        for field_id, positions in fields.items():
                            tf = len(positions)
                            tfidf_score = self.compute_tfidf(tf, df, self.N)
                            weight = self.FIELD_WEIGHTS.get(field_id, 1.0)
                            doc_scores[doc_id] += tfidf_score * weight

        return sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def compute_tfidf(self, tf, df, N):
        if tf == 0 or df == 0:
            return 0
        return (1 + math.log10(tf)) * math.log10(N / df)

    def get_token_result(self, token, txn):
        # Try to get the token result from the cache.
        cached_result = self.token_cache.get(token)
        if cached_result is not None:
            # Move this token to the end to mark it as recently used.
            self.token_cache.move_to_end(token)
            return cached_result

        # If not cached, fetch the result.
        result = self.search_index(token, txn)
        if result:
            result.pop('___', None)  # Clean up if necessary.
        # Add the result to the cache.
        self.token_cache[token] = result

        # If the cache size exceeds the limit, remove the least recently used token.
        if len(self.token_cache) > self.cache_limit:
            self.token_cache.popitem(last=False)
        return result


    def text_search(self, processed_query, exclude_docs, dietary_preference):
        matching_docs = set()
        doc_scores_bm25 = defaultdict(float)
        doc_scores_tfidf = defaultdict(float)
        proximity_scores = defaultdict(float)
        diet_exclusions = []

        deserialisation_time = 0
        start = time.time()
        with self.env.begin() as txn:
            # Process individual tokens using the token cache.
            for token in processed_query.get('tokens', []):
                print(f'TOKENS | {token}')
                start_d = time.time()
                token_results = self.get_token_result(token, txn)
                deserialisation_time += time.time() - start_d
                if token_results:
                    matching_docs.update(token_results.keys())
                    for doc_id, scores in token_results.items():
                        dietary_flags = scores.get('dietary_flags', 0)

                        if dietary_preference:
                            is_vegan = (dietary_flags & 0b100) >> 2  # Extracts the third bit
                            is_vegetarian = (dietary_flags & 0b010) >> 1  # Extracts the second bit
                            is_gluten_free = (dietary_flags & 0b001)  # Extracts the first bit
                            if dietary_preference == 1 and not is_vegan:
                                diet_exclusions.append(doc_id)
                                continue
                            if dietary_preference == 2 and not is_vegetarian:
                                diet_exclusions.append(doc_id)
                                continue
                            if dietary_preference == 3 and not is_gluten_free:
                                diet_exclusions.append(doc_id)
                                continue

                        doc_scores_bm25[doc_id] += scores.get('bm25', 0)
                        doc_scores_tfidf[doc_id] += scores.get('tfidf', 0)

            # Process n-grams similarly...
            for ngram in processed_query.get('n_grams', []):
                ngram_tokens = list(ngram)
                threshold = 3 if len(ngram_tokens) == 2 else 5 if len(ngram_tokens) == 3 else None
                if threshold is None:
                    continue

                token_results_map = {}
                valid_ngram = True
                for token in ngram_tokens:
                    start_d = time.time()
                    result = self.get_token_result(token, txn)
                    deserialisation_time += time.time() - start_d
                    if not result:
                        valid_ngram = False
                        break
                    token_results_map[token] = result

                if not valid_ngram or len(token_results_map) != len(ngram_tokens):
                    continue

                docs_for_ngram = set.intersection(*(set(res.keys()) for res in token_results_map.values()))
                if not docs_for_ngram:
                    continue

                for doc_id in docs_for_ngram:
                    positions_lists = []
                    valid_doc = True
                    for token in ngram_tokens:
                        token_doc = token_results_map[token].get(doc_id)
                        if not token_doc:
                            valid_doc = False
                            break
                        pos_list = sorted(pos for positions in token_doc.values() for pos in positions)
                        positions_lists.append(pos_list)
                    if not valid_doc or len(positions_lists) != len(ngram_tokens):
                        continue

                    if self.tokens_in_proximity(positions_lists, threshold):
                        matching_docs.add(doc_id)
                        for token in ngram_tokens:
                            scores = token_results_map[token].get(doc_id, {})
                            doc_scores_bm25[doc_id] += scores.get('bm25', 0)
                            doc_scores_tfidf[doc_id] += scores.get('tfidf', 0)
                        proximity_scores[doc_id] = 1 / (1 + threshold)


            exclude_docs.update(diet_exclusions)
            final_docs = matching_docs - exclude_docs
            print(f'TEXT SEARCH | Searching: {time.time() - start}')
            print(f'TEXT SEARCH | Deserialisation: {deserialisation_time}')

            start = time.time()
            bm25_scores = self.get_top_n_scores(doc_scores_bm25, final_docs, 10000)
            tfidf_scores = self.get_top_n_scores(doc_scores_tfidf, final_docs, 10000)
            print(f'TEXT SEARCH | Ranking: {time.time() - start}')

        start = time.time()
        # Normalisation and merging of scores...
        max_prox = max(proximity_scores.values(), default=1)
        min_prox = min(proximity_scores.values(), default=0)
        max_bm25 = max(bm25_scores.values(), default=1)
        min_bm25 = min(bm25_scores.values(), default=0)
        max_tfidf = max(tfidf_scores.values(), default=1)
        min_tfidf = min(tfidf_scores.values(), default=0)

        bm25_weight, tfidf_weight, proximity_weight = 0.5, 0.3, 0.2

        # Convert the final_docs set to a NumPy array
        doc_ids = np.array(list(final_docs))
    
        # Create arrays of scores with fallback defaults.
        bm25_arr = np.array([bm25_scores.get(doc_id, min_bm25) for doc_id in doc_ids])
        tfidf_arr = np.array([tfidf_scores.get(doc_id, min_tfidf) for doc_id in doc_ids])
        prox_arr = np.array([proximity_scores.get(doc_id, min_prox) for doc_id in doc_ids])

        # Vectorized normalization (adding a small constant to avoid division by zero)
        norm_bm25 = (bm25_arr - min_bm25) / (max_bm25 - min_bm25 + 1e-9)
        norm_tfidf = (tfidf_arr - min_tfidf) / (max_tfidf - min_tfidf + 1e-9)
        norm_prox = (prox_arr - min_prox) / (max_prox - min_prox + 1e-9)

        # Compute the weighted sum for each document.
        weighted_scores = (bm25_weight * norm_bm25 +
                           tfidf_weight * norm_tfidf +
                           proximity_weight * norm_prox)

        # Convert the results back into a dictionary.
        ranked_docs = dict(zip(doc_ids, weighted_scores))
        print(f'TEXT SEARCH | Merging Ranks: {time.time() - start}')
        print("length of ranked_docs in text search: " + str(len(ranked_docs)))
        return ranked_docs



    def get_top_n_scores(self, doc_scores, doc_set, top_n):
        """Returns the top N document scores (from the docs in doc_set) sorted in descending order."""
        if not doc_scores:
            return {}

        # Filter doc_scores to only include documents in doc_set.
        filtered = {doc: score for doc, score in doc_scores.items() if doc in doc_set}
        if not filtered:
            return {}

        n = len(filtered)
        # Create NumPy arrays from the filtered dictionary.
        keys = np.fromiter(filtered.keys(), dtype=object, count=n)
        values = np.fromiter(filtered.values(), dtype=np.float64, count=n)
        
        # Get indices that would sort the scores in descending order.
        sorted_indices = np.argsort(-values)
        
        # Select only the top_n indices (ensure we don't go out of bounds).
        top_indices = sorted_indices[:min(top_n, n)]
        
        # Build the dictionary for the top N documents.
        top_keys = keys[top_indices]
        top_values = values[top_indices]
        return dict(zip(top_keys, top_values))

    
        # # Adjust top_n if it's larger than available scores
        # top_n = min(top_n, len(values))

        # top_indices = np.argpartition(-values, top_n)[:top_n]  # Partial sort (O(N))
        # sorted_indices = top_indices[np.argsort(-values[top_indices])]  # Sort only top_n (O(k log k))

        # return dict(zip(keys[sorted_indices], values[sorted_indices]))

    def bm25_tfidf_search(self, doc_set, query_terms, txn, top_n=100):
        """
        Optimized BM25 and TF-IDF search function
        """
        start = time.time()
        doc_scores_bm25 = defaultdict(float)
        doc_scores_tfidf = defaultdict(float)
        # You may replace this with a precomputed mapping of doc lengths.
        doc_lengths = {}
        doc_set.discard('___')

        for term in query_terms:
            start = time.time()
            key = term.encode('utf-8')
            data = txn.get(key)
            if data:
                term_data = msgpack.unpackb(data, raw=False, strict_map_key=False)
                # '___' holds the document frequency for the term.
                # df = term_data.pop('___', 0)
                # idf = self.compute_idf(df, self.N)

                # loop through doc_set only.
                print(f'BM25 | begin:  {time.time() - start}')
                start = time.time()
                for doc_id in doc_set:
                    # if doc_id == "___":
                    #     continue
                    if doc_id in term_data:
                        doc_scores_bm25[doc_id] += term_data[doc_id]['bm25']
                        doc_scores_tfidf[doc_id] += term_data[doc_id]['tfidf']
                print(f'BM25 | retrieving:  {time.time() - start}')

        start = time.time()
        # Get top N results for BM25 and TF-IDF
        ranked_bm25 = self.get_top_n_scores(doc_scores_bm25, top_n)
        ranked_tfidf = self.get_top_n_scores(doc_scores_tfidf, top_n)
        print(f'BM25 | sorting:  {time.time() - start}')
        return [ranked_bm25, ranked_tfidf]

    def tokens_in_proximity(self, positions_lists, threshold):
        """
        Check if there exists a combination of positions (one from each list in positions_lists)
        such that the difference between the smallest and largest position is within the threshold.
        """
        # We'll check all combinations from the first list against the min and max of subsequent lists.
        from itertools import product
        for combination in product(*positions_lists):
            if max(combination) - min(combination) <= threshold:
                return True
        return False

    def search_index(self, token, txn):
        """
        This method will read from the lmdb inverted index and return list of documents that have the token,
        the field_id and the position of the token in the inverted index.
        Format: {doc_id: {field_id: [pos1, pos2, ...]}}
        index is stored in lmdb
        """

        # env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)

        key = token.encode('utf-8')
        data = txn.get(key)

        if data:
            term_data = msgpack.unpackb(data, raw=False, strict_map_key=False)  # {doc_id: {field_id: [positions]}}
            return term_data
        else:
            return None

    def get_tfidf_score(self, token):
        """
        This method reads from the lmdb for tfidf and returns the tfidf for each document.
        term frequencies, inverse document frequencies, number of documents are stored in lmdb
        """
        pass

    def access_secret(self, secret_name: str) -> str:
        """
        Access the latest version of a secret from Secret Manager.
        """

        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{self.PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=secret_path)

        return response.payload.data.decode("UTF-8")

    def get_db_credentials(self):
        """
        Retrieve database credentials from Secret Manager.
        """

        db_user = "dishcovery-admin"
        db_pass = self.access_secret("postgres-key")
        db_name = "dishcovery"
        db_instance = "dishcovery-449618:europe-west2:dishcovery-database"  # Should be in format project:region:instance
        # db_instance = self.access_secret("instance-name")

        return db_user, db_pass, db_name, db_instance

    def get_connection(self):
        """
        Create a connection to the Cloud SQL PostgreSQL instance.
        """
        db_user, db_pass, db_name, db_instance = self.get_db_credentials()
        # db_user = get_db_credentials()

        # Cloud SQL Auth Proxy uses a Unix socket with the following pattern.

        db_host = f"/cloudsql/{db_instance}"
        connector = Connector()

        conn = connector.connect(
            db_instance,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name
        )

        return conn

    def create_new_connection(self):
            db_user, db_pass, db_name, db_instance = self.get_db_credentials()
            connector = Connector()
            return connector.connect(
                db_instance,
                "pg8000",
                user=db_user,
                password=db_pass,
                db=db_name
            )

    def get_recipe_from_store(self, paged_documents, diet_preference):
        document_ids = [str(doc[0]) for doc in paged_documents]
        # Fetch a connection from the pool
        conn = self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT document_id, recipe_id, title, url, ingredients, instructions "
                "FROM recipes_extended WHERE document_id = ANY(%s)", (document_ids,)
            )
            db_recipes = cursor.fetchall()
        finally:
            self.db_pool.release_connection(conn)
        recipe_dict_map = {r[0]: {
            "id": r[1],
            "url": r[3],
            "title": r[2],
            "ingredients": r[4],
            "instructions": r[5]
        } for r in db_recipes}
        final_recipes = [recipe_dict_map[doc_id] for doc_id in document_ids if doc_id in recipe_dict_map]
        return final_recipes

    def get_selected_recipe_from_store(self, recipe_id):
        conn = self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipe_details WHERE recipe_id = %s", (recipe_id,))
            recipe_details = cursor.fetchall()
        finally:
            self.db_pool.release_connection(conn)
        if recipe_details:
            row = recipe_details[0]
            recipe_dict = {
                "id": row[0],
                "url": row[2],
                "title": row[1],
                "ingredients": row[3],
                "instructions": row[4]
            }
            return recipe_dict
        else:
            return "No recipe found"

if __name__ == "__main__":
    pass
