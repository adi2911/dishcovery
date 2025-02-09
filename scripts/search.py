import re

class BooleanSearchProcessor:
    def __init__(self):
        # Define logical operators and the index file location
        self.operators = ['AND', 'OR', 'NOT'] 
        self.booleanindexfilename = "scripts/index.txt"

    def parse_query(self, query):
        """
        Parse the input boolean query into tokens (terms and operators).
        """
        # Convert query to uppercase for uniform processing
        query = query.upper()

        # Split the query into words and operators
        tokens = re.findall(r'\w+|\&|\|', query)
        
        parsed_tokens = []
        for token in tokens:
            if token in self.operators:
                parsed_tokens.append(token)
            else:
                # Convert search terms to lowercase to maintain consistency
                parsed_tokens.append(token.lower())
        
        return parsed_tokens
    
    def search(self, query):
        """
        Search the boolean query across the index file (or dataset).
        """
        # Read the index file and process its contents into a list of records
        with open(self.booleanindexfilename, "r") as file:
            dataset = file.readlines()

        # Parse the query into tokens (terms and operators)
        parsed_query = self.parse_query(query)

        # Now, evaluate the parsed query and search the dataset
        result = self.evaluate_expression(parsed_query, dataset)
        return result

    def evaluate_expression(self, parsed_query, dataset):
        """
        Evaluate the parsed boolean expression on the dataset.
        """
        # Placeholder for the evaluation logic
        stack = []

        # Loop through each token in the parsed query
        for token in parsed_query:
            if token == "AND":
                b = stack.pop()
                a = stack.pop()
                stack.append(self.handle_and(a, b, dataset))
            elif token == "OR":
                b = stack.pop()
                a = stack.pop()
                stack.append(self.handle_or(a, b, dataset))
            elif token == "NOT":
                a = stack.pop()
                stack.append(self.handle_not(a, dataset))
            else:
                stack.append(self.handle_term(token, dataset))
        
        return stack[0]

    def handle_and(self, a, b, dataset):
        """
        Handle the AND operation on two results.
        """
        return [item for item in a if item in b]

    def handle_or(self, a, b, dataset):
        """
        Handle the OR operation on two results.
        """
        return list(set(a + b))

    def handle_not(self, a, dataset):
        """
        Handle the NOT operation on a result.
        """
        return [item for item in dataset if item not in a]

    def handle_term(self, term, dataset):
        """
        Search for the term in the dataset.
        """
        return [item for item in dataset if term in item.lower()]

processor = BooleanSearchProcessor()
query = "pasta AND sauce OR pizza"
results = processor.search(query)
print(results)
