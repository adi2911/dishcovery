from flask import Blueprint, request, jsonify, session
from scripts.query_processor import QueryProcessor
from global_path import get_relative_path

search_blueprint = Blueprint('search', __name__)

dummy_db = {
        "123": {
            "id": "123",
            "title": "Famous Vegan Chili",
            "ingredients": ["Beans", "Tomato", "Onion", "Garlic"],
            "diet": "vegan",
            "instructions": "Put ingredients in pot. Stir. Simmer for 30 minutes."
        },
        "456": {
            "id": "456",
            "title": "Delicious Gluten-Free Pasta",
            "ingredients": ["Gluten-Free Pasta", "Tomato Sauce", "Basil"],
            "diet": "gluten-free",
            "instructions": "Boil pasta. Add sauce. Enjoy."
        }
    }
@search_blueprint.route('/searchByIngredients', methods=['POST'])
def search_by_ingredients():
    data = request.json
    print(f"data : {data}")
    ingredients = data.get('ingredients', [])
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')

    # Pagination parameters
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 10))  # Default to 10 results per page

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    # If first page request, process the search and store results in session
    if page == 1:
        ranked_documents = processor.get_ranked_documents(processed_query, False)
        results = processor.get_recipe_from_store(ranked_documents, diet_preference)
        session['search_results'] = results  # Store full results in session
    else:
        results = session.get('search_results', [])

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results[start_idx:end_idx]

    # return jsonify({
    #     "results": paginated_results,
    #     "page": page,
    #     "per_page": per_page,
    #     "total_results": len(results),
    #     "total_pages": (len(results) + per_page - 1) // per_page  # Compute total pages
    # }), 200

    results=dummy_db
    return jsonify({"results": results}), 200

@search_blueprint.route('/searchByText', methods=['POST'])
def search_by_text():
    data = request.json
    text = data.get('text', '')
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)

    if processed_query == "No tokens found":
        return jsonify({"error": processed_query}), 400

    # If first page request, process search and store results in session
    if page == 1:
        ranked_documents = processor.get_ranked_documents(processed_query, True)
        results = processor.get_recipe_from_store(ranked_documents, diet_preference)
        session['search_results'] = results
    else:
        results = session.get('search_results', [])

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results[start_idx:end_idx]

    # return jsonify({
    #     "results": paginated_results,
    #     "page": page,
    #     "per_page": per_page,
    #     "total_results": len(results),
    #     "total_pages": (len(results) + per_page - 1) // per_page
    # }), 200

    return jsonify({"results": results}), 200

@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = dummy_db.get(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404
