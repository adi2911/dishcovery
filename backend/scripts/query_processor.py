import pprint
import re
import Stemmer
import datetime
import json
from collections import OrderedDict, defaultdict
import logging
from nltk.corpus import wordnet
import nltk
from nltk.metrics import edit_distance

nltk.download('words')
from nltk.corpus import words


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

    def get_synonyms(self, word):
        '''
        Retrieves synonyms for a given word from WordNet.
        Args:
            word (str): The input word for which synonyms are needed.

        Returns:
            list: List of synonyms (cleaned and stemmed if enabled).
        '''
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace("_", " ")  # Convert underscores to spaces
                synonyms.add(synonym)

        # Apply text cleaning and stemming
        synonyms = [self.text_cleaner(syn) for syn in synonyms]  # Clean synonyms
        if self.use_stemming:
            synonyms = [self.stemmer.stemWord(syn) for syn in synonyms]  # Stem synonyms

        return list(synonyms)
    def fix_typo(self, word):
        """
        Fixes typos by finding the closest matching word from an English vocabulary.

        Args:
            word (str): The input word to correct.

        Returns:
            str: The corrected word (or the original if no better match is found).
        """
        if word in english_vocab:  # If word is correct, return it as is
            return word

        # Find the closest word using edit distance (Levenshtein Distance)
        closest_match = min(english_vocab, key=lambda w: edit_distance(word, w))

        return closest_match if edit_distance(word, closest_match) <= 2 else word  # Allow small corrections

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

        # tokenised_query=[self.fix_typo(token) for token in tokenised_query]
        # print(query)
        # print(tokenised_query)


        if self.use_stopwords:
            tokenised_query = self.stopword_remover(tokenised_query)

     # Expand query with synonyms
        expanded_terms = []
        print(tokenised_query)
        for token in tokenised_query:
            expanded_terms.extend(self.get_synonyms(token))

        processed_query['synonyms'] = expanded_terms
        
        if len(tokenised_query) == 0:
            return "No tokens found" 

        if self.use_stemming:
            tokenised_query = self.text_stemmer(tokenised_query)
            processed_query['synonyms']=self.text_stemmer(processed_query['synonyms'])

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
        ranked_documents = [

        ]
        '''
        pass

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
    english_vocab = set(words.words())
    stop_words_path = "backend/data/stop_words_english.txt"
    processor = QueryProcessor(stop_word_path=stop_words_path, use_stemming=True)
    
    query = 'chickn cury AND "spicy sauce" NOT tomaato'
    processed_query = processor.process_query_text(query,[])
    
    pprint.pprint(processed_query)