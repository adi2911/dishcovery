# global_trie.py
import json
from my_trie_module import Trie

trie = Trie()

def initialize_trie():
    with open("ingredients.json") as file:
        data = json.load(file)
        for item in data["ingredients"]:
            trie.insert(item.lower())
