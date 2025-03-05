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
import pickle
import json
import math
from collections import defaultdict
import os
import json
import google.cloud.secretmanager as secretmanager
from google.cloud.sql.connector import Connector
from cache_utils import QueryCache, DocCache

from global_path import get_relative_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Query Processing Module")
)


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
        self.stop_words_set = self._load_stopwords() if use_stopwords and stop_word_path else set()
        self.stemmer = Stemmer.Stemmer("english")
        self.FIELD_WEIGHTS = {0: 1.5, 1: 1.2, 2: 1.0}
        self.k1 = 1.2
        self.b = 0.75
        self.N = 1029720  # Total number of documents
        self.avg_doc_length = 170  # Approximate average document length (assumed)
        self.lmdb_path = get_relative_path("data","index_data_dishcovery/inverted_index_2.lmdb/data.mdb")
        self.PROJECT_ID = "dishcovery-449618"
        self.conn = self.get_connection()

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
        # return processed_query['tokens']

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

        cleaned_query = self.text_cleaner(query)
        tokenised_query = self.text_tokenizer(cleaned_query)
        print("Initial exclude tokens: " + str(exclude_tokens))

        if self.use_stopwords:
            tokenised_query = self.stopword_remover(tokenised_query)

        if len(tokenised_query) == 0:
            return "No tokens found"

        if self.use_stemming:
            tokenised_query = self.text_stemmer(tokenised_query)
            tokenized_exclusions = self.text_stemmer(exclude_tokens)

        processed_query['tokens'] = tokenised_query
        processed_query['exclude_tokens'] = tokenized_exclusions
        self.query_n_gram(processed_query)

        logging.info("Query processing completed in {}".format(datetime.datetime.now() - start_time))
        return processed_query

    def process_query_ingredients(self, query, exclude_tokens):

        logging.info("Processing Query: {}".format(query))
        start_time = datetime.datetime.now()

        # Inititalise processed query dict
        processed_query = {"tokens": [],
                           "exclude_tokens": exclude_tokens
                           }

        if self.use_stemming:
            tokenised_query = self.text_stemmer(query)
            tokenized_exclusions = self.text_stemmer(exclude_tokens)

        if len(tokenised_query) == 0:
            return "No tokens found"

        processed_query['tokens'] = tokenised_query
        processed_query['exclude_tokens'] = tokenized_exclusions

        return processed_query


    def get_ranked_documents(self, processed_query, isText, hasDietPreference=False):
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
        for token in processed_query.get('exclude_tokens', []):
            token_results = self.search_index(token)
            print("Token results: {}".format(token_results))
            if token_results:
                exclude_docs.update(token_results.keys())
        print("Excluded documents: {}".format(exclude_docs))
        matching_docs = set()
        proximity_scores = defaultdict(float)

        if isText:
            print("Text-based search")
            ranked_docs = self.text_search(processed_query, exclude_docs)
            #self.query_cache.set(query_cache_dict, ranked_docs)
            if hasDietPreference:
                return sorted(ranked_docs.items(), key=lambda x: x[1], reverse=True)[:1500] # to see if there are enough options
            else:
                return sorted(ranked_docs.items(), key=lambda x: x[1], reverse=True)[:1000]
        else:
            print("Ingredients-based search")
        token_results_map = {token: self.search_index(token) for token in processed_query.get('tokens', [])}

            token_doc_sets = [
                set(results.keys()) for results in token_results_map.values() if results
            ]
            matching_docs = set.intersection(*token_doc_sets) if token_doc_sets else set()
            if hasDietPreference:
                ranked_docs = self.tfidf_search(matching_docs, processed_query["tokens"], 1000)
            else:
                ranked_docs = self.tfidf_search(matching_docs, processed_query["tokens"], 1500)
            return ranked_docs


    def compute_idf(self, df, N):
        """Compute Inverse Document Frequency (IDF)"""
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    def tfidf_search(self, doc_set, query_terms, top_n=10):
        env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)
        doc_scores = defaultdict(float)

        with env.begin() as txn:
            for term in query_terms:
                key = term.encode('utf-8')
                data = txn.get(key)

                if data:
                    term_data = pickle.loads(data)
                    df = term_data.pop('___', 0)

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

    def text_search(self, processed_query, exclude_docs):
        matching_docs = set()
        proximity_scores = defaultdict(float)
        for token in processed_query.get('tokens', []):
            token_results = self.search_index(token)
            if token_results:
                matching_docs.update(token_results.keys())

        for ngram in processed_query.get('n_grams', []):
            ngram = list(ngram)
            threshold = 3 if len(ngram) == 2 else 5 if len(ngram) == 3 else None
            if threshold is None:
                continue

            token_results_map = {token: self.search_index(token) for token in ngram}
            token_results_map.pop('___')
            docs_for_ngram = set.intersection(
                *[set(results.keys()) for results in token_results_map.values() if results])

            if not docs_for_ngram:
                continue

            for doc_id in docs_for_ngram:
                positions_lists = [
                    sorted(pos for pos_list in token_results_map[token][doc_id].values() for pos in pos_list)
                    for token in ngram if doc_id in token_results_map[token]
                ]

                if len(positions_lists) == len(ngram) and self.tokens_in_proximity(positions_lists, threshold):
                    matching_docs.add(doc_id)
                    proximity_scores[doc_id] = 1 / (1 + threshold)

        final_docs = matching_docs - exclude_docs
        # bm25_scores = dict(self.bm25_search(final_docs, processed_query["tokens"], 10000))
        # tfidf_scores = dict(self.tfidf_search(final_docs, processed_query["tokens"], 10000))

        scores = self.bm25_tfidf_search(final_docs, processed_query["tokens"], 1000)
        bm25_scores = dict(scores[0])
        tfidf_scores = dict(scores[1])

        # This could be used for normalising and using all three scores?
        max_prox = max(proximity_scores.values(), default=1)
        min_prox = min(proximity_scores.values(), default=0)
        max_bm25 = max(bm25_scores.values(), default=1)
        min_bm25 = min(bm25_scores.values(), default=0)
        max_tfidf = max(tfidf_scores.values(), default=1)
        min_tfidf = min(tfidf_scores.values(), default=0)

        bm25_weight, tfidf_weight, proximity_weight = 0.5, 0.3, 0.2

        ranked_docs = {
            doc_id: bm25_weight * (
                    (bm25_scores.get(doc_id, min_bm25) - min_bm25) / (max_bm25 - min_bm25 + 1e-9)) +
                    tfidf_weight * (
                        (tfidf_scores.get(doc_id, min_tfidf) - min_tfidf) / (
                            max_tfidf - min_tfidf + 1e-9)) +
                    proximity_weight * (
                        (proximity_scores.get(doc_id, min_prox) - min_prox) / (
                            max_prox - min_prox + 1e-9))
                for doc_id in final_docs
        }
        # Store in query cache
        return ranked_docs

    def bm25_tfidf_search(self, doc_set, query_terms, top_n=100):
        env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)
        doc_scores_bm25 = defaultdict(float)
        doc_scores_tfidf = defaultdict(float)
        doc_lengths = {}

        with env.begin() as txn:
            for term in query_terms:
                key = term.encode('utf-8')
                data = txn.get(key)

                if data:
                    term_data = pickle.loads(data)
                    df = term_data.pop('___', 0)
                    idf = self.compute_idf(df, self.N)

                    for doc_id, fields in term_data.items():
                        if doc_id not in doc_set:
                            continue




                        for field_id, positions in fields.items():
                            if field_id == "dietary_flags":

                                is_vegan = (dietary_flags & 0b100) >> 2  # Extracts the third bit
                                is_vegetarian = (dietary_flags & 0b010) >> 1  # Extracts the second bit
                                is_gluten_free = (dietary_flags & 0b001)  # Extracts the first bit

                            tf = len(positions)
                            weight = self.FIELD_WEIGHTS.get(field_id, 1.0)
                            doc_length = doc_lengths.get(doc_id, self.avg_doc_length)

                            bm25_score = idf * ((tf * (self.k1 + 1)) /
                                                (tf + self.k1 * (
                                                        1 - self.b + self.b * (doc_length / self.avg_doc_length))))
                            tfidf_score = self.compute_tfidf(tf, df, self.N)

                            doc_scores_tfidf[doc_id] += tfidf_score * weight
                            doc_scores_bm25[doc_id] += bm25_score * weight

        return [sorted(doc_scores_bm25.items(), key=lambda x: x[1], reverse=True)[:top_n], sorted(doc_scores_tfidf.items(), key=lambda x: x[1], reverse=True)[:top_n]]

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

    def search_index(self, token):
        """
        This method will read from the lmdb inverted index and return list of documents that have the token,
        the field_id and the position of the token in the inverted index.
        Format: {doc_id: {field_id: [pos1, pos2, ...]}}
        index is stored in lmdb
        """

        env = lmdb.open(self.lmdb_path, readonly=True, subdir=False, lock=False)

        with env.begin() as txn:
            key = token.encode('utf-8')
            data = txn.get(key)

            if data:
                term_data = pickle.loads(data)  # {doc_id: {field_id: [positions]}}
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

    def get_recipe_mappings(self, ranked_documents, diet_preference):
        document_ids = [doc[0] for doc in ranked_documents]
        base_query = """
                SELECT document_id, recipe_id 
                FROM document_mappings_extended
                WHERE document_id = ANY(%s)
            """
        params = [document_ids]

        #print(ranked_documents[:100])
        # Apply dietary filter if necessary
        if diet_preference == 1:
            base_query += " AND is_vegan = True"
        elif diet_preference == 2:
            base_query += " AND is_vegetarian = True"
        elif diet_preference == 3:
            base_query += " AND is_gluten_free = True"

        conn = self.conn
        cursor = conn.cursor()
        cursor.execute(base_query, tuple(params))
        mappings = cursor.fetchall()  # List of (document_id, recipe_id)
        recipe_ids = [recipe_id[1] for recipe_id in mappings][:1000]
        return recipe_ids

    def get_recipe_from_store(self, recipe_ids, diet_preference):
        """
        document_ids = [doc[0] for doc in paged_documents]
        query = "SELECT document_id, recipe_id FROM document_mappings WHERE document_id = ANY(%s)"

        conn = self.conn
        cursor = conn.cursor()

        # Fetch recipes
        cursor.execute(query, (document_ids,))
        mappings = cursor.fetchall()
        recipe_ids = [doc[1] for doc in mappings]
        """

        conn = self.conn
        cursor = conn.cursor()

        final_recipes = []
        cursor.execute("SELECT * FROM recipe_details WHERE recipe_id = ANY(%s)", (recipe_ids,))
        db_recipes = cursor.fetchall()
        for r in db_recipes:
            recipe_dict = {
                    "id": r[0],
                    "url": r[2],
                    "title": r[1],
                    "ingredients": r[3],
                    "instructions": r[4]
            }
            final_recipes.append(recipe_dict)

        return final_recipes


    def get_selected_recipe_from_store(self, recipe_id):
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipe_details WHERE recipe_id = %s", (recipe_id,))
        recipe_details = cursor.fetchall()
        if len(recipe_details)!=0:
            print(f"fetched recipe from store sucessfully : {recipe_id}")
        if len(recipe_details) != 0:
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



