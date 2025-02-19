import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
import logging

from api.users import users_blueprint
from api.search import search_blueprint
from api.autocomplete import autocomplete_blueprint, init_trie
from global_path import get_relative_path

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config['SESSION_TYPE'] = 'filesystem'
CORS(app, supports_credentials=True)
Session(app)

init_trie(get_relative_path("api", "ingredients.json"))

app.register_blueprint(users_blueprint, url_prefix='/api')
app.register_blueprint(search_blueprint, url_prefix='/api')
app.register_blueprint(autocomplete_blueprint, url_prefix='/api')

@app.route("/health")
def health_check():
    return "Healthy", 200

@app.route('/')
def home():
    return "Flask app is running!"

if __name__ == '__main__':
    # Use Cloud Run assigned PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
