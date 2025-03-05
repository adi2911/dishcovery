from flask import Blueprint, request, jsonify, session, current_app as app

from scripts.query_processor import QueryProcessor
from global_path import get_relative_path
import time

import logging
import time
import cProfile

logging.basicConfig(level=logging.DEBUG)  # Ensure DEBUG level is set
logger = logging.getLogger(__name__)
processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)

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

    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    if page == 1:
        ranked_documents = processor.get_ranked_documents(processed_query, False)
        ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)
        session['ranked_recipes'] = ranked_recipes
        session.modified = True
    else:
        if "ranked_recipes" in session:
            ranked_recipes = session.get('ranked_recipes', [])
        else:
            ranked_documents = processor.get_ranked_documents(processed_query, False)
            ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)

    paginated_results = ranked_recipes[start_idx:end_idx]

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_recipes),
        "total_pages": (len(ranked_recipes) + per_page - 1) // per_page  # Compute total pages
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

    start = time.time()
    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)
    print(f'Time to process query:  {time.time() - start}')

    if processed_query == "No tokens found" :
        return jsonify({"error": "No results found"}), 400


    # If first page request, process search and store results in session
    # If not, retrieve recipes from session
    # if page == 1:
    start = time.time()
    ranked_documents = processor.get_ranked_documents(processed_query, True)
    print(f'Time to get Ranked Docs:  {time.time() - start}')
    start = time.time()
    ranked_recipes = processor.get_recipe_from_store(ranked_documents[start_idx:end_idx], diet_preference)
    print(f'Time to retrieve Docs from store:  {time.time() - start}')
    session['ranked_recipes'] = ranked_recipes
    session.modified = True
    # else:
    #     if "ranked_recipes" in session:
    #         ranked_recipes = session.get('ranked_recipes', [])
    #     else:
    #         ranked_documents = processor.get_ranked_documents(processed_query, False)
    #         ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)

    paginated_results = ranked_recipes

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_recipes),
        "total_pages": (len(ranked_recipes) + per_page - 1) // per_page  # Compute total pages
    }), 200


@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    processor = app.config['query_processor']
    recipe = processor.get_selected_recipe_from_store(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404
