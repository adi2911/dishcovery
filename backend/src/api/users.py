from flask import Flask, request, jsonify, session
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.cloud import firestore, secretmanager
import uuid
import os
import requests
import json


from scripts.query_processor import QueryProcessor


import logging
logging.basicConfig(level=logging.INFO)

# Setup Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, supports_credentials=True)

def get_firestore_credentials_from_secret():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/230003814546/secrets/firestore-key/versions/1"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')

key_json = get_firestore_credentials_from_secret()
db = firestore.Client.from_service_account_info(json.loads(key_json))
users_ref = db.collection('users')

# Sign-in API


@app.route("/health")
def health_check():
    return "Healthy", 200

@app.route('/')
def home():
    return "Flask app is running!"

@app.route('/api/signin', methods=['POST'])
def signin():
    access_token = request.json.get('token')
    if not access_token:
        return jsonify({'error': 'Token is missing'}), 400

    # Use the Google UserInfo endpoint
    userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    google_resp = requests.get(userinfo_endpoint, headers=headers)

    if google_resp.status_code != 200:
        return jsonify({'error': 'Invalid Access Token'}), 400

    user_info = google_resp.json()

    # Example user structure
    user_id = str(uuid.uuid4())
    user_data = {
        'user_id': user_id,
        'name': user_info.get('name'),
        'email': user_info.get('email'),
        'preferences': []
    }

    # Check if user already exists
    existing_user = users_ref.where('email', '==', user_data['email']).get()
    if existing_user:
        user = existing_user[0].to_dict()
    else:
        users_ref.document(user_id).set(user_data)
        user = user_data

    # Set Flask session
    session['user_id'] = user['user_id']

    return jsonify({'message': 'Signed in successfully', 'user': user}), 200

 
@app.route('/api/signout', methods=['POST'])
def signout():
    session.clear()  # Clears all session data
    return jsonify({'message': 'Signed out successfully'}), 200

# Get Current User API
@app.route('/api/user', methods=['GET'])
def get_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not signed in'}), 401

    user_doc = users_ref.document(user_id).get()
    if user_doc.exists:
        return jsonify({'user': user_doc.to_dict()}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    




@app.route('/api/searchByIngredients', methods=['POST'])
def search_by_ingredients():
    data = request.json
    ingredients = data.get('ingredients', [])
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path="data/stop_words_english.txt", use_stemming=True)

    # Construct a boolean query from ingredients and exclude lists
    processed_query = processor.process_query_ingredients(ingredients, exclude)

    #CALL KRISHI's function
    ranked_documents = processor.get_ranked_documents(processed_query, False)


    results = processor.get_recipe_from_store(ranked_documents, diet_preference)

    print("Ingredients search:")
    print("Processed query:", processed_query)
    print("Diet Preference:", diet_preference)

    # Dummy results
    results = [
        {
            "id": "unique_id_1",
            "title": "Dummy Ingredient Recipe",
            "ingredients": ["Tomato", "Onion", "Garlic"],
            "diet": "vegan",
            "instructions": "LONG text",
            "url": "url_for_recipe"
        }
    ]
    return jsonify({"results": results}), 200


@app.route('/api/searchByText', methods=['POST'])
def search_by_text():
    data = request.json
    text = data.get('text', '')
    exclude = data.get('exclude', [])
    diet_preference = data.get('dietPreference', 'none')

    # Initialize QueryProcessor
    processor = QueryProcessor(stop_word_path="data/stop_words_english.txt", use_stemming=True)

    # Process the text query
    processed_query = processor.process_query_text(text,exclude_tokens=exclude)
    
    if(processed_query == "No tokens found"):
        return jsonify({"error":processed_query}), 400

    #CALL KRISHI's function
    ranked_documents = processor.get_ranked_documents(processed_query, True)


    results = processor.get_recipe_from_store(ranked_documents, diet_preference)





    print("Text search:")
    print("Processed query:", processed_query)
    print("Diet Preference:", diet_preference)

   
    return jsonify({"results": results}), 200





@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    # TODO: Implement actual search logic
    # 1. Query  DB / Firestore for the recipe doc with ID = recipe_id

    # Example dummy data:
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

    recipe = dummy_db.get(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404




if __name__ == '__main__':
    app.run(debug=True)
