from flask import Flask, jsonify, request, render_template
from scripts.DataManager import DataManager
from scripts.env_utils import credentials_present, save_credentials
import threading
import webbrowser
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

# Constants
GENERATED_NEWSLETTERS_DIR = "generated_newsletters"
BRAND_INFO_FILE = "data/brand_information.json"
DEBUG_LOGGING = False  # Console logging enabled for debugging

# Initialize the Flask application
app = Flask(__name__)
# Create a DataManager instance for handling country data
data_manager = DataManager()

def map_story_fields(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map form story fields to template-expected field names.
    
    Args:
        story: Story data from form with fields like 'image', 'imageAlt'
        
    Returns:
        Story data with template-expected field names like 'image_url', 'image_alt'
    """
    # Debug logging for story data
    if DEBUG_LOGGING:
        print(f"DEBUG: Processing story data - Type: {type(story)}, Value: {story}")
    
    # Validate story data structure
    if not isinstance(story, dict):
        raise ValueError(f"Story data must be a dictionary, got {type(story).__name__}: {story}")
    
    return {
        'image_url': story.get('image', ''),
        'image_alt': story.get('imageAlt', ''),
        'headline': story.get('headline', ''),
        'description': story.get('description', ''),
        'url': story.get('url', ''),
        'cta': story.get('cta')  # CTA structure is already correct
    }

def _load_country_data(country_key: str) -> tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
    """
    Load and validate country data.
    
    Args:
        country_key: Country identifier
        
    Returns:
        Tuple of (country_info, country_name, languages)
        
    Raises:
        ValueError: If no languages found for country
    """
    countries_data = data_manager.get_countries()
    country_info = countries_data.get(country_key, {})
    country_name = country_info.get('name', country_key)
    languages = country_info.get('languages', [])
    
    if not languages:
        raise ValueError(f"No languages found for country: {country_key}")
    
    return country_info, country_name, languages


def _load_brand_info() -> Dict[str, Any]:
    """
    Load brand information from JSON file.
    
    Returns:
        Brand information dictionary
    """
    brand_info_path = Path(BRAND_INFO_FILE)
    with brand_info_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def _validate_form_data(form_data: Dict[str, Any]) -> None:
    """
    Validate form data structure.
    
    Args:
        form_data: Form data to validate
        
    Raises:
        ValueError: If hero data is not a dictionary
    """
    hero_data = form_data.get('hero', {})
    if not isinstance(hero_data, dict):
        raise ValueError(f"Hero data must be a dictionary, got {type(hero_data).__name__}: {hero_data}")


def _create_template_data(form_data: Dict[str, Any], country_name: str, language_info: Dict[str, Any], brand_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create template data for newsletter generation.
    
    Args:
        form_data: User form data
        country_name: Name of the country
        language_info: Language information
        brand_info: Brand information
        
    Returns:
        Template data dictionary
    """
    hero_data = form_data.get('hero', {})
    hero_ctas = form_data.get('ctas', [])
    user_stories = form_data.get('stories', [])
    
    language_code = language_info.get('code', 'en')
    script_direction = language_info.get('scriptDirection', 'ltr')
    
    return {
        'country': form_data['country'],
        'dir': script_direction,
        'lang': language_code,
        'metadata': {
            'country_name': country_name
        },
        'global': {
            'foundation_name': brand_info['foundation_name'],
            'footer_text': brand_info['footer_text'],
            'logo_url': brand_info['logo_url']
        },
        'hero': {
            'image_url': hero_data.get('image', ''),
            'image_alt': hero_data.get('imageAlt', ''),
            'headline': hero_data.get('headline', ''),
            'description': hero_data.get('description', ''),
            'cta_learn_more_url': hero_data.get('learnMoreUrl', ''),
            'ctas_buttons': hero_ctas
        },
        'stories': [map_story_fields(story) for story in user_stories]
    }


def _slugify(text: str) -> str:
    """
    Convert a string into a URL- and filename-safe slug.

    Replaces spaces with underscores and removes characters that are invalid
    for Windows filenames.

    Args:
        text: The string to slugify.

    Returns:
        The slugified string.
    """
    text = text.replace(' ', '_')
    return re.sub(r'[<>:"/\\|?*]', '_', text)


def _generate_safe_filename(country_key: str, language_code: str, timestamp: str) -> str:
    """
    Generate a safe filename for Windows by sanitizing invalid characters.
    
    Args:
        country_key: Country identifier
        language_code: Language code
        timestamp: Timestamp string
        
    Returns:
        Sanitized filename
    """
    safe_country_key = _slugify(country_key)
    return f"newsletter_{safe_country_key}_{language_code}_{timestamp}.html"


def generate_newsletter_templates(form_data: Dict[str, Any]) -> List[str]:
    """
    Generate newsletter templates for each language spoken in the selected country.
    
    Creates newsletters in generated_newsletters/{country}/ directory structure.
    For countries with multiple languages, generates one newsletter per language.
    
    Args:
        form_data: Captured form data from the user
        
    Returns:
        List of paths to generated template files
    """
    
    # Load and validate data
    _validate_form_data(form_data)
    country_key = form_data['country']
    country_info, country_name, languages = _load_country_data(country_key)
    brand_info = _load_brand_info()
    
    # Create output directory
    country_dir_name = _slugify(country_key)
    output_dir = Path(GENERATED_NEWSLETTERS_DIR) / country_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Generate one newsletter for each language
    for language_info in languages.values():
        template_data = _create_template_data(form_data.copy(), country_name, language_info, brand_info)
        
        # Generate safe filename
        language_code = language_info.get('languageCode', 'en')
        now = datetime.now()
        date_str = now.strftime("%m%d%y")
        time_str = now.strftime("%H%M%S")
        filename = _generate_safe_filename(country_key, language_code, f"{date_str}_{time_str}")
        
        # Generate and save template
        template_html = render_template('newsletter_template.html', **template_data)
        template_file = output_dir / filename
        template_file.write_text(template_html, encoding='utf-8')
        
        generated_files.append(str(template_file))
    
    return generated_files

@app.route('/api/countries')
def get_countries():
    """
    API endpoint to retrieve the list of countries and their languages.
    
    Returns:
        JSON response containing country-language data
    """
    try:
        data = data_manager.get_countries()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Failed to load countries data: {str(e)}'}), 500

@app.route("/")
def index() -> str:
    """
    Root endpoint serving the index.html page with a dropdown of countries.
    
    Returns:
        Rendered HTML page with country dropdown and credential status
    """
    try:
        countries = data_manager.get_countries()
        creds_ok = credentials_present()
        return render_template("index.html", countries=countries, creds_ok=creds_ok)
    except Exception as e:
        # Fallback to empty countries if data loading fails
        return render_template("index.html", countries={}, creds_ok=False, error=str(e))

@app.route("/build-newsletter")
def build_newsletter() -> str:
    """
    Render the build-newsletter.html page.
    
    The selected country is read by JavaScript from the query string.
    
    Returns:
        Rendered HTML page for newsletter building interface
    """
    return render_template("build-newsletter.html")

def _validate_request_data(form_data: Dict[str, Any]) -> None:
    """
    Validate incoming request data.
    
    Args:
        form_data: Form data to validate
        
    Raises:
        ValueError: If required fields are missing
    """
    if not form_data:
        raise ValueError('No data received')
    
    required_fields = ['country', 'hero']
    for field in required_fields:
        if field not in form_data:
            raise ValueError(f'Missing required field: {field}')


def _log_debug_info(form_data: Dict[str, Any]) -> None:
    """
    Log debug information if DEBUG_LOGGING is enabled.
    
    Args:
        form_data: Form data to log
    """
    if not DEBUG_LOGGING:
        return
        
    print("=" * 60)
    print("INCOMING FORM DATA:")
    print("=" * 60)
    print(f"Country: {form_data.get('country', 'NOT SET')}")
    print(f"Languages: {form_data.get('languages', 'NOT SET')}")
    print("\nHERO DATA:")
    hero_data = form_data.get('hero', {})
    if isinstance(hero_data, dict):
        for key, value in hero_data.items():
            print(f"  {key}: {value}")
    else:
        print(f"  Hero data is not a dictionary: {type(hero_data).__name__} = {hero_data}")
    print(f"\nCTAs: {form_data.get('ctas', [])}")
    print(f"\nSTORIES: {form_data.get('stories', [])}")
    print("=" * 60)


@app.route('/api/build-newsletter', methods=['POST'])
def api_build_newsletter():
    """Handle newsletter generation request."""
    try:
        form_data = request.get_json()
        if not form_data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        # Basic validation
        if 'country' not in form_data:
            return jsonify({'success': False, 'error': 'Missing country field'}), 400
        
        generated_files = generate_newsletter_templates(form_data)
        
        # Extract file information for the results page
        country = form_data['country']
        languages = form_data.get('languages', '').split(',') if form_data.get('languages') else []
        
        # Extract just the filenames from full paths
        filenames = [Path(file_path).name for file_path in generated_files]
        
        return jsonify({
            'success': True,
            'message': f'Successfully generated {len(generated_files)} newsletter(s)',
            'files': generated_files,
            'result_data': {
                'country': country,
                'total_newsletters': len(generated_files),
                'languages': languages,
                'filenames': filenames
            }
        })
        
    except Exception as e:
        error_msg = f"Failed to process form data: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/newsletters-generated')
def newsletters_generated():
    """
    Display the newsletter generation results page.
    
    Returns:
        Rendered HTML page showing generation results and upload options
    """
    # Get data from URL parameters (passed from JavaScript redirect)
    country = request.args.get('country', 'Unknown')
    total_newsletters = request.args.get('total', '0')
    languages = request.args.get('languages', '').split(',') if request.args.get('languages') else []
    filenames = request.args.get('filenames', '').split(',') if request.args.get('filenames') else []
    
    # Clean up empty strings from split
    languages = [lang.strip() for lang in languages if lang.strip()]
    filenames = [filename.strip() for filename in filenames if filename.strip()]
    
    return render_template('newsletters-generated.html', 
                         country=country,
                         total_newsletters=int(total_newsletters) if total_newsletters.isdigit() else 0,
                         languages=languages,
                         filenames=filenames)

@app.route("/api/save-credentials", methods=["POST"])
def api_save_credentials():
    """
    API endpoint to save Mailchimp credentials to .env file.
    
    Expects JSON: {"api_key": str, "server_prefix": str}
    
    Returns:
        JSON response with success status or error message
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400
            
        api_key = data.get("api_key", "").strip()
        server_prefix = data.get("server_prefix", "").strip()
        
        if not api_key or not server_prefix:
            return jsonify({"success": False, "error": "Both API key and server prefix are required"}), 400
            
        save_credentials(api_key, server_prefix)
        return jsonify({"success": True, "message": "Credentials saved successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save credentials: {str(e)}"}), 500

@app.route("/api/check-credentials", methods=["GET"])
def api_check_credentials():
    """
    API endpoint to check if Mailchimp credentials exist and are non-empty in .env.
    
    Returns:
        JSON response with credential presence status
    """
    try:
        has_credentials = credentials_present()
        return jsonify({"hasCredentials": has_credentials, "success": True})
    except Exception as e:
        return jsonify({"hasCredentials": False, "success": False, "error": str(e)}), 500

def open_browser() -> None:
    """
    Open the default web browser to the Flask application URL.
    
    This function is called automatically when the Flask app starts
    to provide a better user experience.
    """
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()
    app.run(debug=True)