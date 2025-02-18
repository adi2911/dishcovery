import pprint
import re
import Stemmer
import datetime
import json
from collections import OrderedDict, defaultdict
import logging

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
        self.field_weights = {0: 1.0, 1: 0.8, 2: 0.5}

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
        '''

        # 1 - Get exclude tokens' document IDs
        excluded = set()
        for token in processed_query['exclude_tokens']:
            token_found_in = self.search_index(token)
            if token_found_in is not None:
                excluded.add(token_found_in.keys())

        # 2 - Check isText
        if isText:
            # 3 - isText == True
            print("Text-based search")
            # a. find each tokens' details and store as {token: {doc_id: {field_id: [pos1, pos2, ...]}}}
            results = defaultdict(lambda: defaultdict(list))

            for token in processed_query['tokens']:
                token_found_in = self.search_index(token)
                if token_found_in is not None:
                    # get the position details of all tokens' appearance in the corpora
                    print("tbc")
                # use this to give weight based on if it was a token (1.0), synonym (0.8), exclude_tokens (-1.0)
                # also give weights to each field, if field is 0 (Title) - 1.0, 1 (Ingredients) - 0.8, 2 (Steps) - 0.5
                # using these weights and tf, idf values, calculate tfidf

            # b. perform positive+negative proximity search for each n_gram
            # for each space-separated bigram and trigram that we get in n grams, perform proximity search. if the words occur
            # within 3 words of each other for bigrams and 5 words for trigrams, add to the tfidf score by 0.3 and 0.2

        else:
            # 4 - isText == False
            print("Ingredients-based search")
            # a. find each tokens' details
            # don't do synonyms or token-type based weighting
            # b. perform AND search

            # c. get tfidf score for each doc

        # 5 - sort based on tfidf score

        pass

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
        pass


if __name__ == "__main__":
    stop_words_path = "data/stop_words_english.txt"
    processor = QueryProcessor(stop_word_path=stop_words_path, use_stemming=True)
    
    query = 'chicken curry AND "spicy sauce" NOT tomato'
    processed_query = processor.process_query_text(query)
    
    pprint.pprint(processed_query)