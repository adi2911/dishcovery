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
        # Make sure we have a set to track all full words
        self.words = set()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        
        # Also store the full word in the set, to allow substring queries.
        self.words.add(word)
    
    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._dfs(node, prefix, results)
        return results[:10]  # top 10
    
    def _dfs(self, node, prefix, results):
        if len(results) >= 10:
            return
        if node.is_end_of_word:
            results.append(prefix)
        for char, child_node in node.children.items():
            self._dfs(child_node, prefix + char, results)

    def search_substring(self, query):
        """
        Returns up to 10 ingredients (from self.words) where the query
        exactly matches a token that is NOT the first token.
        """
        results = []
        for word in self.words:
            tokens = word.split()
            # Must have more than 1 token, and at least one token after the first matches exactly
            if len(tokens) > 1 and any(token == query for token in tokens[1:]):
                results.append(word)
                if len(results) >= 10:
                    break
        return results

# Create a global Trie variable, initialized to None.
trie = None

def init_trie(json_path: str):
    """
    Load the ingredients from the specified JSON file
    and build the Trie only once.
    """
    global trie
    trie = Trie()
    
    with open(json_path, 'r') as file:
        data = json.load(file)  # e.g. { "ingredients": [...] }
        ingredient_list = data["ingredients"]
        for item in ingredient_list:
            # Ensure item is a string, then lower it for consistent storing
            word = str(item).lower()
            trie.insert(word)

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

    # Standard prefix-based results
    prefix_suggestions = trie.search(query)
    print(f"prefix suggestions found: {len(prefix_suggestions)}")

    # Exact match after the first token
    interior_suggestions = trie.search_substring(query)
    print(f"interior suggestions found: {len(interior_suggestions)}")

    # Merge them (avoiding duplicates) and limit total suggestions to 10
    suggestions = prefix_suggestions + [s for s in interior_suggestions if s not in prefix_suggestions]
    suggestions = suggestions[:20]
    print(f"Suggestions found: {len(suggestions)}")
    return jsonify(suggestions)
