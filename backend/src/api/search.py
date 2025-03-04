from flask import Blueprint, request, jsonify, session, current_app as app
from scripts.query_processor import QueryProcessor
from global_path import get_relative_path
import time
import logging
import redis
import json

logging.basicConfig(level=logging.DEBUG)  # Ensure DEBUG level is set
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=2, decode_responses=True)

# Configure Redis to use up to 1GB memory and an all-keys-LRU eviction policy
redis_client.config_set('maxmemory', '1gb')
redis_client.config_set('maxmemory-policy', 'allkeys-lru')

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
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    # Construct a Redis cache key based on the core search parameters.
    # Note: We do NOT include page/per_page here because we store the *entire* ranked_documents
    # and then do pagination in code.
    cache_key = f"ingredients:{json.dumps(ingredients)}:exclude:{json.dumps(exclude)}:diet:{diet_preference}"

    # If it's the first page, we either pull from cache or run the query.
    if page == 1:
        cached_docs = redis_client.get(cache_key)
        if cached_docs:
            logger.info(f"CACHE HIT for Ingredients Search ({cache_key})")
            ranked_documents = json.loads(cached_docs)
        else:
            logger.info("CACHE MISS - Running QueryProcessor for Ingredients Search!")
            start_time = time.time()
            ranked_documents = processor.get_ranked_documents(processed_query, False)
            redis_client.set(cache_key, json.dumps(ranked_documents))
            logger.info(f"Cache Miss Time: {time.time() - start_time:.4f} seconds")

        ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)
        # Store the final recipes in session for subsequent pagination
        session['ranked_recipes'] = ranked_recipes
        session.modified = True
    else:
        # For pages > 1, we first check if we have the recipes in session.
        if "ranked_recipes" in session:
            ranked_recipes = session.get('ranked_recipes', [])
        else:
            # If somehow session is empty, we still check Redis before running the query
            cached_docs = redis_client.get(cache_key)
            if cached_docs:
                logger.info(f"CACHE HIT for Ingredients Search (page>1) ({cache_key})")
                ranked_documents = json.loads(cached_docs)
            else:
                logger.info("CACHE MISS (page>1) - Running QueryProcessor for Ingredients Search!")
                ranked_documents = processor.get_ranked_documents(processed_query, use_text_model=False)
                redis_client.set(cache_key, json.dumps(ranked_documents))

            ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)
            session['ranked_recipes'] = ranked_recipes  # refresh session if needed
            session.modified = True

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
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)

    if processed_query == "No tokens found":
        return jsonify({"error": "Recipe not found"}), 400

    # Similar caching approach for text-based queries
    # We store the entire ranked_documents in Redis, ignoring page/per_page for the key.
    cache_key = f"text:{text}:exclude:{json.dumps(exclude)}:diet:{diet_preference}"

    if page == 1:
        cached_docs = redis_client.get(cache_key)
        if cached_docs:
            logger.info(f"CACHE HIT for Text Search ({cache_key})")
            ranked_documents = json.loads(cached_docs)
        else:
            logger.info("CACHE MISS - Running QueryProcessor for Text Search!")
            start_time = time.time()
            # Note that the original code uses `get_ranked_documents(..., True)` when page=1
            ranked_documents = processor.get_ranked_documents(processed_query, True)
            redis_client.set(cache_key, json.dumps(ranked_documents))
            logger.info(f"Cache Miss Time: {time.time() - start_time:.4f} seconds")

        ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)
        session['ranked_recipes'] = ranked_recipes
        session.modified = True
    else:
        if "ranked_recipes" in session:
            ranked_recipes = session.get('ranked_recipes', [])
        else:
            # Fallback: Check Redis if session is empty
            cached_docs = redis_client.get(cache_key)
            if cached_docs:
                logger.info(f"CACHE HIT for Text Search (page>1) ({cache_key})")
                ranked_documents = json.loads(cached_docs)
            else:
                logger.info("CACHE MISS (page>1) - Running QueryProcessor for Text Search!")
                ranked_documents = processor.get_ranked_documents(processed_query, use_text_model=False)
                redis_client.set(cache_key, json.dumps(ranked_documents))

            ranked_recipes = processor.get_recipe_from_store(ranked_documents, diet_preference)
            session['ranked_recipes'] = ranked_recipes
            session.modified = True

    if len(ranked_recipes) == 0:
        return jsonify({"error": "Recipe not found"}), 400

    paginated_results = ranked_recipes[start_idx:end_idx]

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_recipes),
        "total_pages": (len(ranked_recipes) + per_page - 1) // per_page
    }), 200


@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    print(f"get_recipe_by_id {recipe_id}")
    processor = app.config['query_processor']
    recipe = processor.get_selected_recipe_from_store(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 400
