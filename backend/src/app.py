import os
from flask import Flask
from flask_cors import CORS
from scripts.query_processor import QueryProcessor
from flask_session import Session
import logging

from api.search import search_blueprint
from api.autocomplete import autocomplete_blueprint, init_trie
from global_path import get_relative_path


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

CORS(app, supports_credentials=True)

app.config["SECRET_KEY"] = "your_secret_key"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # Session lasts only during user interaction
app.config['SESSION_USE_SIGNER'] = True  # Sign session to prevent tampering
app.config['SESSION_KEY_PREFIX'] = 'myapp_'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # Ensure a dedicated session folder
app.config['SESSION_FILE_THRESHOLD'] = 500 # Maximum number of session files before cleanup
app.config['SESSION_COOKIE_NAME'] = 'myapp_session'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # or 'None' if cross-site requests are needed
app.config['SESSION_COOKIE_SECURE'] = True
app.config['query_processor'] = QueryProcessor(stop_word_path=get_relative_path("data", "stop_words_english.txt"),
                                               use_stemming=True)

Session(app)


init_trie(get_relative_path("api", "ingredients.json"))

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