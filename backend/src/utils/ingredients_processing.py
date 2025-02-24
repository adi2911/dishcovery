import json



def load_ingredients(file_path):
    """Load ingredients from a JSON file containing recipes."""
    ingredients = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
        for recipe in recipes:
            # Expect each recipe to have an "ingredients" key with a list of strings
            for ingredient in recipe.get("ingredients", []):
                # Add each ingredient to the set for uniqueness
                ingredients.add(ingredient.strip())
    return ingredients

def main():
    
    # Load ingredients from both files
    ingredients1 = load_ingredients("test.json")
    ingredients2 = load_ingredients("train.json")
    
    # Merge the sets to get unique ingredients
    unique_ingredients = ingredients1.union(ingredients2)
    
    # Create the output structure
    output_data = { "ingredients": list(unique_ingredients) }
    
    # Write the results to the output file
    with open("ingredients.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    

if __name__ == "__main__":
    main()
