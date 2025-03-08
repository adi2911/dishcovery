from flask import Blueprint, request, jsonify, session, current_app as app

from scripts.query_processor import QueryProcessor
from global_path import get_relative_path
import time

import logging
import time
import cProfile
import redis
import json
import os

logging.basicConfig(level=logging.DEBUG)  # Ensure DEBUG level is set
logger = logging.getLogger(__name__)
processor = QueryProcessor(stop_word_path=get_relative_path("data","stop_words_english.txt"), use_stemming=True)

# Initialize Redis client
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

# Connect to Redis
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=2,
    decode_responses=True
)

try:
    redis_client.ping()
    logger.info("Connected to Redis Successfully")
except redis.exceptions.ConnectionError as e:
    logger.warning(f"Redis Connection Failed: {e}")

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/searchByIngredients', methods=['POST'])
def search_by_ingredients():
    data = request.json
    print(f"data : {data}")
    ingredients = data.get('ingredients', [])
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 0)
    print(f"SEARCHED BY INGREDIENTS : {ingredients} , exluded ingredients are : {exclude} , diet_preference is : {diet_preference}")

    # Pagination parameters
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 10))  # Default to 10 results per page

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    #processed_query = processor.process_query_ingredients(ingredients, exclude)
    
    cache_key = f"ingredients:{json.dumps(ingredients)}:exclude:{json.dumps(exclude)}:diet:{diet_preference}".replace(" ", "_")
    if page == 1:
        cached_docs = redis_client.get(cache_key)
        if cached_docs:
            try:
                ranked_documents = json.loads(cached_docs)
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted Cache Data: {e} - Resetting cache for {cache_key}")
                redis_client.delete(cache_key)
                ranked_documents = []
        else: 
            logger.info("CACHE MISS - Running QueryProcessor for Ingredients Search!")
            processed_query = processor.process_query_ingredients(ingredients, exclude)
            ranked_documents = processor.get_ranked_documents(processed_query, diet_preference, False)
            #redis_client.set(cache_key, json.dumps(ranked_documents))
            try:
                serialized_data = json.dumps(ranked_documents)
                redis_client.set(cache_key, serialized_data)
            except Exception as e:
                logger.error(f"Redis Serialization Error: {e}")
        
        paginated_results = processor.get_recipe_from_store(ranked_documents[:end_idx], diet_preference)
        session['ranked_documents'] = ranked_documents
        session.modified = True
    else:
        if "ranked_documents" in session:
            ranked_documents = session.get('ranked_documents', [])
            paginated_results = processor.get_recipe_from_store(ranked_documents[start_idx:end_idx], diet_preference)
        else:
            cached_docs = redis_client.get(cache_key)
            if cached_docs:
                try:
                    logger.info(f"CACHE HIT for Ingredients Search (page>1) ({cache_key})")
                    ranked_documents = json.loads(cached_docs)
                except json.JSONDecodeError as e:
                    logger.error(f"Corrupted Cache Data: {e} - Resetting cache for {cache_key}")
                    redis_client.delete(cache_key)
                    ranked_documents = []
            else:
                logger.info("CACHE MISS (page>1) - Running QueryProcessor for Ingredients Search!")
                processed_query = processor.process_query_ingredients(ingredients, exclude)
                ranked_documents = processor.get_ranked_documents(processed_query, diet_preference, False)
                #redis_client.set(cache_key, json.dumps(ranked_documents))
                try:
                    serialized_data = json.dumps(ranked_documents)
                    redis_client.set(cache_key, serialized_data)
                except Exception as e:
                    logger.error(f"Redis Serialization Error: {e}")
                
            paginated_results = processor.get_recipe_from_store(ranked_documents[start_idx:end_idx], diet_preference)
            session['ranked_documents'] = ranked_documents
            session.modified = True

    return jsonify({
        "results": paginated_results,
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
    diet_preference = data.get('dietPreference', 0)
    print(f"SEARCHED BY TEXT : {text} , exluded ingredients are : {exclude} , diet_preference is : {diet_preference}")
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Paginate the results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    processor = app.config['query_processor']

    '''
    # Get the QueryProcessor instance from app config
    processor = app.config['query_processor']
    processed_query = processor.process_query_text(text, exclude_tokens=exclude)
    print(f'Time to process query:  {time.time() - start}')

    if processed_query == "No tokens found" :
        return jsonify({"error": "Recipe not found"}), 400'''

    # If first page request, process search and store results in session
    # If not, retrieve recipes from session
    cache_key = f"text:{text}:exclude:{json.dumps(exclude)}:diet:{diet_preference}".replace(" ", "_")

    
    if page == 1:
        start = time.time()
        cached_docs = redis_client.get(cache_key)
        if cached_docs:
            try:
                logger.info(f"CACHE HIT for Text Search ({cache_key})")
                ranked_documents = json.loads(cached_docs)
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted Cache Data: {e} - Resetting cache for {cache_key}")
                redis_client.delete(cache_key)
                ranked_documents = []
        else:
            logger.info("CACHE MISS - Running QueryProcessor for Text Search!")
            start = time.time()
            # Get the QueryProcessor instance from app config
            processed_query = processor.process_query_text(text, exclude_tokens=exclude)
            print(f'Time to process query:  {time.time() - start}')
            if processed_query == "No tokens found" :
                return jsonify({"error": "Recipe not found"}), 400
            ranked_documents = processor.get_ranked_documents(processed_query, diet_preference, True)
            #redis_client.set(cache_key, json.dumps(ranked_documents))
            try:
                serialized_data = json.dumps(ranked_documents)
                redis_client.set(cache_key, serialized_data)
            except Exception as e:
                logger.error(f"Redis Serialization Error: {e}")

            print(f'Time to get Ranked Docs:  {time.time() - start}')
            start = time.time()
            
        paginated_results = processor.get_recipe_from_store(ranked_documents[:end_idx], diet_preference)
        session['ranked_documents'] = ranked_documents
        session.modified = True
    else:
        if "ranked_documents" in session:
            ranked_documents = session.get('ranked_documents', [])
            paginated_results = processor.get_recipe_from_store(ranked_documents[start_idx:end_idx], diet_preference)
        else:
            # Fallback: Check Redis if session is empty
            cached_docs = redis_client.get(cache_key)
            if cached_docs:
                try:
                    logger.info(f"CACHE HIT for Text Search (page>1) ({cache_key})")
                    ranked_documents = json.loads(cached_docs)
                except json.JSONDecodeError as e:
                    logger.error(f"Corrupted Cache Data: {e} - Resetting cache for {cache_key}")
                    redis_client.delete(cache_key)
                    ranked_documents = []
            else:
                logger.info("CACHE MISS (page>1) - Getting Ranked Docs for Text Search!")
                # Get the QueryProcessor instance from app config
                processed_query = processor.process_query_text(text, exclude_tokens=exclude)
                print(f'Time to process query:  {time.time() - start}')
                if processed_query == "No tokens found" :
                    return jsonify({"error": "Recipe not found"}), 400
                ranked_documents = processor.get_ranked_documents(processed_query, diet_preference, False)
                #redis_client.set(cache_key, json.dumps(ranked_documents))
                try:
                    serialized_data = json.dumps(ranked_documents)
                    redis_client.set(cache_key, serialized_data)
                except Exception as e:
                    logger.error(f"Redis Serialization Error: {e}")
                    
            paginated_results = processor.get_recipe_from_store(ranked_documents[start_idx:end_idx], diet_preference)

    if len(ranked_documents) == 0:
        return jsonify({"error": "Recipe not found"}), 400

    return jsonify({
        "results": paginated_results,
        "page": page,
        "per_page": per_page,
        "total_results": len(ranked_documents),
        "total_pages": (len(ranked_documents) + per_page - 1) // per_page  # Compute total pages
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

