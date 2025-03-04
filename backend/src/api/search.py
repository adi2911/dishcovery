import logging
import json
import redis
import time
from flask import Blueprint, request, jsonify
from scripts.query_processor import QueryProcessor
from global_path import get_relative_path

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=2, decode_responses=True)

# Set Redis max memory & LRU policy
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
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Generate Redis cache key
    cache_key = f"ingredients:{json.dumps(ingredients)}:exclude:{json.dumps(exclude)}:diet:{diet_preference}"

    # Check Redis for cached result
    cached_result = redis_client.get(cache_key)
    if cached_result:
        logging.info(f"CACHE HIT for Ingredients Search ({cache_key})")
        ranked_documents = json.loads(cached_result)

        # We still need a processor to load from DB 
        processor = QueryProcessor(
            stop_word_path=get_relative_path("data", "stop_words_english.txt"),
            use_stemming=True
        )
    else:
        logging.info("CACHE MISS - Running QueryProcessor for Ingredients Search!")
        start_time = time.time()

        processor = QueryProcessor(
            stop_word_path=get_relative_path("data", "stop_words_english.txt"),
            use_stemming=True
        )
        processed_query = processor.process_query_ingredients(ingredients, exclude)
        ranked_documents = processor.get_ranked_documents(processed_query, False)

        # Store in Redis
        redis_client.set(cache_key, json.dumps(ranked_documents))

        logging.info(f"Cache Miss Time: {time.time() - start_time}")

    paginated_ranked_documents = ranked_documents[start_idx:end_idx]
    paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)
    print("nandita1")
    return jsonify({
        "results": paginated_results[0],
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page
    }), 200


@search_blueprint.route('/searchByText', methods=['POST'])
def search_by_text():
    data = request.json
    text = data.get('text', '')
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Cache Key
    cache_key = f"text:{text}:exclude:{json.dumps(exclude)}:diet:{diet_preference}:page:{page}"

    #Check if cached paginated results exist
    cached_results = redis_client.get(cache_key)
    if cached_results:
        logging.info(f"CACHE HIT for Text Search ({cache_key})")
        return jsonify(json.loads(cached_results)), 200

    # Step 2: Cache Miss - Run Query Processing
    logging.info(f"CACHE MISS - Running QueryProcessor for Text Search!")
    processor = QueryProcessor(
        stop_word_path=get_relative_path("data", "stop_words_english.txt"),
        use_stemming=True
    )
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)
    if processed_query == "No tokens found":
        return jsonify({"error": "No results found"}), 400

    ranked_documents = processor.get_ranked_documents(processed_query, True)
    paginated_ranked_documents = ranked_documents[start_idx:end_idx]
    paginated_results = processor.get_recipe_from_store(paginated_ranked_documents, diet_preference)

    response_data = {
        "results": paginated_results[0],
        "time-taken": paginated_results[1],
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page
    }

    # Step 3: Store Paginated Results in Redis 
    redis_client.set(cache_key, json.dumps(response_data))

    return jsonify(response_data), 200


@search_blueprint.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    processor = QueryProcessor(
        stop_word_path=get_relative_path("data", "stop_words_english.txt"),
        use_stemming=True
    )
    recipe = processor.get_selected_recipe_from_store(recipe_id)

    if recipe != "No recipe found":
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404
