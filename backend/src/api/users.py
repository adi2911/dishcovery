from flask import Blueprint, request, jsonify, session
from google.cloud import firestore, secretmanager
import uuid
import json
import requests
import warnings

warnings.filterwarnings("ignore", message="Your application has authenticated using end user credentials from Google Cloud SDK without a quota project.")

users_blueprint = Blueprint('users', __name__)

def get_firestore_credentials_from_secret():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/230003814546/secrets/firestore-key/versions/1"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')

key_json = get_firestore_credentials_from_secret()
db = firestore.Client.from_service_account_info(json.loads(key_json))
users_ref = db.collection('users')

@users_blueprint.route('/signin', methods=['POST'])
def signin():
    access_token = request.json.get('token')
    if not access_token:
        return jsonify({'error': 'Token is missing'}), 400

    userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    google_resp = requests.get(userinfo_endpoint, headers=headers)

    if google_resp.status_code != 200:
        return jsonify({'error': 'Invalid Access Token'}), 400

    user_info = google_resp.json()
    user_id = str(uuid.uuid4())

    user_data = {
        'user_id': user_id,
        'name': user_info.get('name'),
        'email': user_info.get('email'),
        'preferences': []
    }

    existing_user = users_ref.where('email', '==', user_data['email']).get()
    if existing_user:
        user = existing_user[0].to_dict()
    else:
        users_ref.document(user_id).set(user_data)
        user = user_data

    session['user_id'] = user['user_id']
    return jsonify({'message': 'Signed in successfully', 'user': user}), 200

@users_blueprint.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return jsonify({'message': 'Signed out successfully'}), 200

@users_blueprint.route('/user', methods=['GET'])
def get_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not signed in'}), 401

    user_doc = users_ref.document(user_id).get()
    if user_doc.exists:
        return jsonify({'user': user_doc.to_dict()}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
