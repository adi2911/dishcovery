import logging

from flask import Blueprint, request, jsonify, session
from scripts.query_processor import QueryProcessor
from global_path import get_relative_path
import time

search_blueprint = Blueprint('search', __name__)

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
    start = time.time()
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    logging.info("Time taken to rank: " + str(time.time() - start))
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    # recalculate the ranked documents for each page request
    ranked_documents = processor.get_ranked_documents(processed_query, False)
    paginated_ranked_documents = ranked_documents[start_idx:end_idx]
    paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)

    return jsonify({
        "results": paginated_results[0],
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
    start = time.time()
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    logging.info("Time taken to rank: " + str(time.time() - start))
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)

    if processed_query == "No tokens found" :
        return jsonify({"error": "No results found"}), 400

    # recalculate the ranked documents for each page request
    ranked_documents = processor.get_ranked_documents(processed_query, True)
    paginated_ranked_documents = ranked_documents[start_idx:end_idx]
    paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)

    return jsonify({
        "results": paginated_results[0],
        "time-taken": paginated_results[1],
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page
    }), 200


@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)
    recipe = processor.get_selected_recipe_from_store(recipe_id)
    if recipe != "No recipe found":
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404

