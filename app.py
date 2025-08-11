from flask import Flask, jsonify, request
from scripts.DataManager import DataManager
from scripts.env_utils import credentials_present, save_credentials
import threading
import webbrowser
import os

# Initialize the Flask application
app = Flask(__name__)
# Create a DataManager instance for handling country data
data_manager = DataManager()

@app.route('/api/countries')
def get_countries() -> 'flask.Response':
    """
    API endpoint to retrieve the list of countries and their languages.
    Returns:
        flask.Response: JSON response containing country-language data.
    """
    data = data_manager.get_countries()
    return jsonify(data)

from flask import render_template

@app.route("/")
def index() -> str:
    """
    Root endpoint serving the index.html page with a dropdown of countries.
    Returns:
        str: Rendered HTML page with country dropdown.
    """
    countries = data_manager.get_countries()
    creds_ok = credentials_present()
    return render_template("index.html", countries=countries, creds_ok=creds_ok)

@app.route("/build-newsletter")
def build_newsletter() -> str:
    """
    Render the build-newsletter.html page. The selected country is read by JS from query string.
    """
    return render_template("build-newsletter.html")

from flask import request

@app.route("/api/save-credentials", methods=["POST"])
def api_save_credentials():
    """
    API endpoint to save Mailchimp credentials to .env file.
    Expects JSON: {"api_key": ..., "server_prefix": ...}
    Returns:
        dict: Success or error message.
    """
    data = request.get_json()
    api_key = data.get("api_key", "").strip()
    server_prefix = data.get("server_prefix", "").strip()
    if not api_key or not server_prefix:
        return {"success": False, "error": "Both fields required."}, 400
    save_credentials(api_key, server_prefix)
    return {"success": True}

@app.route("/api/check-credentials", methods=["GET"])
def api_check_credentials():
    """
    API endpoint to check if Mailchimp credentials exist and are non-empty in .env.
    Returns:
        dict: {"hasCredentials": bool}
    """
    return {"hasCredentials": credentials_present()}

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()
    app.run(debug=True)