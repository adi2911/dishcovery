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

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    # If first page request, process the search and store results in session
    # If not, retrieve ranked documents from session
    if page == 1:
        ranked_documents = processor.get_ranked_documents(processed_query, False)
        paginated_ranked_documents = ranked_documents[start_idx:end_idx]
        paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)
        session['ranked_documents'] = ranked_documents  # Store the retrieved ranked documents in session
    else:
        ranked_documents = session.get('ranked_documents', [])
        paginated_ranked_documents = ranked_documents[start_idx:end_idx]
        paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page  # Compute total pages
    }), 200


@search_blueprint.route('/searchByText', methods=['POST'])
def search_by_text():
    data = request.json
    text = data.get('text', '')
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)

    if processed_query == "No tokens found" :
        return jsonify({"error": "No results found"}), 400

    # If first page request, process search and store results in session
    # If not, retrieve ranked documents from session
    if page == 1:
        ranked_documents = processor.get_ranked_documents(processed_query, False)
        paginated_ranked_documents = ranked_documents[start_idx:end_idx]
        paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)
        session['ranked_documents'] = ranked_documents  # Store the retrieved ranked documents in session
    else:
        ranked_documents = session.get('ranked_documents', [])
        paginated_ranked_documents = ranked_documents[start_idx:end_idx]
        paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page
    }), 200


@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = dummy_db.get(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404
