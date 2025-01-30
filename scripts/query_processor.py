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
logger = logging.getLogger()

logger.info("Begin")

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
        phrases_queries = re.findall(r'"(.*?)"', query)
        return phrases_queries

    def process_query(self, query):
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
        processed_query={"boolean_operators": [],
                         "phrase_queries": [],
                         "processed_tokens": []  
                        }
        
        processed_query['phrase_queries'] = self.extract_phrases(query)
        processed_query['boolean_operators'] = self.extract_boolean_operators(query)

        
        cleaned_query = self.text_cleaner(query)
        tokenised_query = self.text_tokenizer(cleaned_query)

        if self.use_stopwords:
            tokenised_query = self.stopword_remover(tokenised_query)

        if self.use_stemming:
            tokenised_query = self.text_stemmer(tokenised_query)

        processed_query['processed_tokens'] = tokenised_query


        logging.info("Query processing completed in {}".format(datetime.datetime.now() - start_time))
        return processed_query



if __name__ == "__main__":
    stop_words_path = "data/stop_words_english.txt"
    processor = QueryProcessor(stop_word_path=stop_words_path, use_stemming=True)
    
    query = 'chicken curry AND "spicy sauce" NOT tomato'
    processed_query = processor.process_query(query)
    
    pprint.pprint(processed_query)