# backend/src/app.py
from flask import Flask
from flask_cors import CORS
import logging

from api.users import users_blueprint
from api.search import search_blueprint
from api.autocomplete import autocomplete_blueprint, init_trie
from global_path import get_relative_path



logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, supports_credentials=True)


init_trie(get_relative_path("api","ingredients.json"))

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
    app.run(debug=True)
