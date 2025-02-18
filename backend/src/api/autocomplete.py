import json
from flask import Blueprint, request, jsonify

autocomplete_blueprint = Blueprint('autocomplete', __name__)

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
    
    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []  # No matches found
            node = node.children[char]
        
        results = []
        self._dfs(node, prefix, results)
        return results[:10]  # Return top 10 matches
    
    def _dfs(self, node, prefix, results):
        if len(results) >= 10:
            return
        if node.is_end_of_word:
            results.append(prefix)
        for char, child_node in node.children.items():
            self._dfs(child_node, prefix + char, results)

# Create a global Trie variable, initialized to None.
trie = None

def init_trie(json_path: str):
    """
    Load the ingredients from the specified JSON file
    and build the Trie only once.
    """
    global trie
    trie = Trie()  # instantiate a new trie

    with open(json_path, 'r') as file:
        data = json.load(file)                # e.g. { "ingredients": [...] }
        ingredient_list = data["ingredients"] # read the array of ingredients
        for item in ingredient_list:
            trie.insert(item.lower())
    print(f"Loaded {len(ingredient_list)} ingredients into Trie.")

@autocomplete_blueprint.route('/autocomplete', methods=['GET'])
def autocomplete():
    global trie
    # Make sure we have a trie to search
    if trie is None:
        return jsonify([])

    query = request.args.get('query', '').lower().strip()
    print(f"Query requested: {query}")

    if not query or len(query) < 2:
        return jsonify([])

    suggestions = trie.search(query)
    print(f"Suggestions found: {len(suggestions)}")
    return jsonify(suggestions)
