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
import psycopg2
import google.cloud.secretmanager as secretmanager
import sqlalchemy
from google.cloud.sql.connector import Connector

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
        self.PROJECT_ID = "dishcovery-449618"

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
        cleaned_text=re.sub(r"[^a-zA-Z0-9\s-]", '',text).lower().replace("\n",' ').replace("  "," ").replace('-',' ')
        cleaned_text=re.sub(' +', ' ',cleaned_text)
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
        bigrams = [tokens[i] + " " + tokens[i+1] for i in range(len(tokens) - 1)]
        trigrams = [tokens[i] + " " + tokens[i+1] + " " + tokens[i+2] for i in range(len(tokens) - 2)]
        
        processed_query['n_grams'].extend(bigrams)
        processed_query['n_grams'].extend(trigrams)
        
        logging.info("n-grams generation completed in {}".format(datetime.datetime.now() - start_time))
        # return processed_query['tokens']

    def query_expansion_PRF(self,query):
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


        #Inititalise processed query dict
        processed_query={"original_query": query,
                        # "processed_query": "", NOT REQUIRED
                         "n_grams": []  , #remove underscore
                         "synonyms":[], #TO_DO
                         "tokens":[],
                         "exclude_tokens":exclude_tokens
                        }
        
        processed_query['phrase_queries'] = self.extract_phrases(query)
        # processed_query['boolean_operators'] = self.extract_boolean_operators(query) NOT REQUIRED

        
        cleaned_query = self.text_cleaner(query)
        tokenised_query = self.text_tokenizer(cleaned_query)

        if self.use_stopwords:
            tokenised_query = self.stopword_remover(tokenised_query)
        
        if len(tokenised_query) == 0:
            return "No tokens found" 

        if self.use_stemming:
            tokenised_query = self.text_stemmer(tokenised_query)

        processed_query['tokens'] = tokenised_query
        self.query_n_gram(processed_query)



        logging.info("Query processing completed in {}".format(datetime.datetime.now() - start_time))
        return processed_query
    
    def process_query_ingredients(self, query, exclude_tokens):

        logging.info("Processing Query: {}".format(query))
        start_time = datetime.datetime.now()

        #Inititalise processed query dict
        processed_query={"tokens":[],
                         "exclude_tokens":exclude_tokens
                        }

        if self.use_stemming:
            tokenised_query = self.text_stemmer(query)

        processed_query['tokens'] = tokenised_query

        return processed_query

    
    def get_ranked_documents(self, processed_query, isText):
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


        # 1 - Get exclude tokens' document IDs
        exclude_docs = set()
        for token in processed_query.get('exclude_tokens', []):
            token_results = self.search_index(token)
            if token_results:
                exclude_docs.update(token_results.keys())

        # This set will store documents that match the query
        matching_docs = set()

        if isText:
            print("Text-based search")
            # a. Gather documents that contain any of the tokens.
            for token in processed_query.get('tokens', []):
                token_results = self.search_index(token)
                if token_results:
                    matching_docs.update(token_results.keys())

            # b. Check n-grams for proximity in the documents.
            # For each n-gram, if the tokens occur in proximity, add the document.
            for ngram in processed_query.get('n_grams', []):
                if len(ngram) == 2:
                    threshold = 3
                elif len(ngram) == 3:
                    threshold = 5
                else:
                    continue

                docs_for_ngram = None
                for token in ngram:
                    token_results = self.search_index(token)
                    if token_results:
                        doc_ids = set(token_results.keys())
                    else:
                        doc_ids = set()
                    if docs_for_ngram is None:
                        docs_for_ngram = doc_ids
                    else:
                        docs_for_ngram &= doc_ids

                if not docs_for_ngram:
                    continue

                for doc_id in docs_for_ngram:
                    positions_lists = []
                    for token in ngram:
                        token_results = self.search_index(token)
                        if token_results and doc_id in token_results:
                            pos = []
                            for pos_list in token_results[doc_id].values():
                                pos.extend(pos_list)
                            positions_lists.append(sorted(pos))

                    if len(positions_lists) == len(ngram) and self.tokens_in_proximity(positions_lists, threshold):
                        matching_docs.add(doc_id)

        else:
            print("Ingredients-based search")
            # Ingredients-based search: perform an AND search.
            token_doc_sets = []
            for token in processed_query.get('tokens', []):
                token_results = self.search_index(token)
                if token_results:
                    token_doc_sets.append(set(token_results.keys()))
                else:
                    token_doc_sets.append(set())
            if token_doc_sets:
                matching_docs = set.intersection(*token_doc_sets)
            else:
                matching_docs = set()

        # 5 - Remove any excluded documents.
        final_docs = matching_docs - exclude_docs

        # 6 - Return a sorted list of document IDs.
        ranked_docs = sorted(final_docs)
        '''
        ranked_docs = self.bm25_search(processed_query["tokens"], 100)
        return ranked_docs

    def compute_idf(self, df, N):
        """Compute Inverse Document Frequency (IDF)"""
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    # BM25 Search Function
    def bm25_search(self, query_terms, top_n=1000):
        """Retrieve and rank documents using BM25 with field weighting."""
        lmdb_path = os.path.join("/Users/krishijainuk/PycharmProjects/dishcovery/backend/src/data/inverted_index.lmdb", "inverted_index.lmdb_data.mdb")
        env = lmdb.open(lmdb_path, readonly=True, subdir=False, lock=False)
        doc_scores = defaultdict(float)  # Store BM25 scores per document
        doc_lengths = {}  # If document lengths were stored, retrieve them

        with env.begin() as txn:
            for term in query_terms:
                key = term.encode('utf-8')
                data = txn.get(key)

                if data:
                    term_data = pickle.loads(data)  # {doc_id: {field_id: [positions]}}
                    df = term_data["___"]  # Document Frequency (DF)
                    term_data.pop('___', None)
                    # Compute IDF

                    idf = self.compute_idf(df, self.N)

                    for doc_id, fields in term_data.items():
                        for field_id, positions in fields.items():
                            term_freq = len(positions)  # TF = Number of occurrences
                            doc_length = doc_lengths.get(doc_id, self.avg_doc_length)  # Use avg length if unknown

                            # Compute BM25 for this term in this field
                            bm25_score = idf * ((term_freq * (self.k1 + 1)) /
                                                (term_freq + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))))

                            # Apply Field Weighting
                            weight = self.FIELD_WEIGHTS.get(field_id, 1.0)
                            doc_scores[doc_id] += bm25_score * weight  # Weighted score

        # Sort documents by final BM25 score
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        return ranked_docs[:top_n]  # Return top N results

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

        # return None if not found
        return {2: {1: [3, 7]}} # and so on

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
        #db_instance = self.access_secret("instance-name")

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

    def get_recipe_from_store(self, ranked_documents, diet_preference):
        
        '''
        results = [
        {
            "id": "unique_id_2",
            "title": "Dummy Text Recipe",
            "ingredients": ["List of dummy ingredients"],
            "description": "Delicious recipe found by text search: " + text,
            "diet": "vegetarian",
        }
        ]
        '''
        start_time = time.time()
        document_ids = [doc[0] for doc in ranked_documents]
        query = "SELECT document_id, recipe_id FROM document_mappings WHERE document_id = ANY(%s)"

        conn = self.get_connection()
        cursor = conn.cursor()

        # Fetch recipes
        cursor.execute(query, (document_ids,))
        mappings = cursor.fetchall()  # [(document_id, recipe_id), ...]

        recipe_ids = [doc[1] for doc in mappings]

        cursor.execute("SELECT * FROM recipe_details WHERE recipe_id = ANY(%s)", (recipe_ids,))
        recipes = cursor.fetchall()

        end_time = time.time()
        conn.close()

        return recipes, end_time - start_time


if __name__ == "__main__":
    start = time.time()
    stop_words_path = "data/stop_words_english.txt"
    processor = QueryProcessor(stop_word_path=stop_words_path, use_stemming=True)
    
    query = 'chicken curry AND "spicy sauce" NOT tomato'
    processed_query = processor.process_query_text(query, [])

    pprint.pprint(processed_query)
    docs = processor.get_ranked_documents(processed_query, True)
    print(docs)
    recipes, time_taken_to_get_from_data_store = processor.get_recipe_from_store(docs, 'Vegetarian')
    print("Time taken to get from data store = " + str(time_taken_to_get_from_data_store))
    print("Number of recipes = " + str(len(recipes)))
    print("Search took : " + str(time.time() - start))



