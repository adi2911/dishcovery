from flask import Flask, request, jsonify, session
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.cloud import firestore
import uuid
import os
import requests


# Setup Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, supports_credentials=True)

# Firestore Initialization
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firestore-key.json'
db = firestore.Client()
users_ref = db.collection('users')

# Sign-in API

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
    # user_info should now look like:
    # {
    #   "sub": "...",
    #   "name": "John Doe",
    #   "given_name": "John",
    #   "family_name": "Doe",
    #   "picture": "https://...",
    #   "email": "john.doe@gmail.com",
    #   ...
    # }

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

if __name__ == '__main__':
    app.run(debug=True)
