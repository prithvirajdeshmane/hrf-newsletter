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

# Constants
TEMP_TEMPLATE_DIR = "temp_template_testing"
BRAND_INFO_FILE = "data/brand_information.json"
DEBUG_LOGGING = True  # Set to False for production

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
    return {
        'image_url': story.get('image', ''),
        'image_alt': story.get('imageAlt', ''),
        'headline': story.get('headline', ''),
        'description': story.get('description', ''),
        'url': story.get('url', ''),
        'cta': story.get('cta')  # CTA structure is already correct
    }

def generate_test_templates(form_data: Dict[str, Any]) -> List[str]:
    """
    Generate three test template variations using the captured form data.
    
    Template 1: Hero with 1 CTA, 0 stories
    Template 2: Hero with 2 CTAs, 1 story with CTA
    Template 3: Hero with no CTA, 2 stories (mixed CTAs)
    
    Args:
        form_data: Captured form data from the user
        
    Returns:
        List of generated template file paths
    """
    template_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = Path(TEMP_TEMPLATE_DIR)
    output_dir.mkdir(exist_ok=True)
    
    # Load country name from country_languages.json
    countries_data = data_manager.get_countries()
    country_key = form_data['country']
    country_name = countries_data.get(country_key, {}).get('name', country_key)
    
    # Load brand information
    brand_info_path = Path(BRAND_INFO_FILE)
    with brand_info_path.open('r', encoding='utf-8') as f:
        brand_info = json.load(f)
    
    # Prepare common template variables
    common_vars = {
        'dir': 'ltr',
        'lang': 'en',
        'metadata': {
            'country_name': country_name
        },
        'global': {
            'foundation_name': brand_info['foundation_name'],
            'footer_text': brand_info['footer_text'],
            'logo_url': brand_info['logo_url']
        }
    }
    
    # Fix data structure: move CTAs from root to hero.ctas_buttons
    hero_ctas = form_data.get('ctas', [])
    
    # Template 1: Hero with 1 CTA, 0 stories
    template1_data = {
        'country': form_data['country'],
        'hero': {
            'image_url': form_data['hero'].get('image', ''),
            'image_alt': form_data['hero'].get('imageAlt', ''),
            'headline': form_data['hero'].get('headline', ''),
            'description': form_data['hero'].get('description', ''),
            'cta_learn_more_url': form_data['hero'].get('learnMoreUrl', ''),
            'ctas_buttons': hero_ctas[:1] if hero_ctas else []
        },
        'stories': [],
        **common_vars
    }
    
    template1_html = render_template('newsletter_template.html', **template1_data)
    template1_file = output_dir / f"template1_hero_1cta_0stories_{timestamp}.html"
    template1_file.write_text(template1_html, encoding='utf-8')
    template_files.append(str(template1_file))
    
    # Template 2: Hero with 2 CTAs, 1 story with CTA
    template2_data = {
        'country': form_data['country'],
        'hero': {
            'image_url': form_data['hero'].get('image', ''),
            'image_alt': form_data['hero'].get('imageAlt', ''),
            'headline': form_data['hero'].get('headline', ''),
            'description': form_data['hero'].get('description', ''),
            'cta_learn_more_url': form_data['hero'].get('learnMoreUrl', ''),
            'ctas_buttons': hero_ctas[:2] if len(hero_ctas) >= 2 else hero_ctas
        },
        'stories': [map_story_fields(story) for story in form_data['stories'][:1]] if form_data['stories'] else [],
        **common_vars
    }
    
    # Ensure the story has a CTA if available
    if template2_data['stories'] and form_data['stories']:
        first_story = form_data['stories'][0]
        if 'cta' not in first_story and hero_ctas:
            # Add a CTA to the story if it doesn't have one
            template2_data['stories'][0]['cta'] = {
                'text': 'Learn More',
                'url': first_story.get('url', '#')
            }
    
    template2_html = render_template('newsletter_template.html', **template2_data)
    template2_file = output_dir / f"template2_hero_2ctas_1story_with_cta_{timestamp}.html"
    template2_file.write_text(template2_html, encoding='utf-8')
    template_files.append(str(template2_file))
    
    # Template 3: Hero with no CTA, 2 stories (mixed CTAs)
    template3_data = {
        'country': form_data['country'],
        'hero': {
            'image_url': form_data['hero'].get('image', ''),
            'image_alt': form_data['hero'].get('imageAlt', ''),
            'headline': form_data['hero'].get('headline', ''),
            'description': form_data['hero'].get('description', ''),
            'cta_learn_more_url': form_data['hero'].get('learnMoreUrl', ''),
            'ctas_buttons': []  # No CTA buttons for template 3
        },
        'stories': [map_story_fields(story) for story in form_data['stories'][:2]] if form_data['stories'] else [],
        **common_vars
    }
    
    # Ensure mixed CTA scenario: first story has CTA, second doesn't (if we have 2 stories)
    if len(template3_data['stories']) >= 2:
        # First story gets a CTA
        if 'cta' not in template3_data['stories'][0]:
            template3_data['stories'][0]['cta'] = {
                'text': 'Take Action',
                'url': template3_data['stories'][0].get('url', '#')
            }
        # Second story has no CTA
        if 'cta' in template3_data['stories'][1]:
            del template3_data['stories'][1]['cta']
    
    template3_html = render_template('newsletter_template.html', **template3_data)
    template3_file = output_dir / f"template3_hero_0ctas_2stories_mixed_{timestamp}.html"
    template3_file.write_text(template3_html, encoding='utf-8')
    template_files.append(str(template3_file))
    
    return template_files

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

@app.route('/api/build-newsletter', methods=['POST'])
def api_build_newsletter():
    """
    Handle newsletter generation request and create test template variations.
    
    Returns:
        JSON response with success status and generated template information
    """
    try:
        form_data = request.get_json()
        if not form_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Validate required fields
        required_fields = ['country', 'hero']
        for field in required_fields:
            if field not in form_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Debug logging (configurable via DEBUG_LOGGING constant)
        if DEBUG_LOGGING:
            print("=" * 60)
            print("INCOMING FORM DATA:")
            print("=" * 60)
            print(f"Country: {form_data.get('country', 'NOT SET')}")
            print(f"Languages: {form_data.get('languages', 'NOT SET')}")
            print("\nHERO DATA:")
            hero_data = form_data.get('hero', {})
            for key, value in hero_data.items():
                print(f"  {key}: {value}")
            print(f"\nCTAs: {form_data.get('ctas', [])}")
            print(f"\nSTORIES: {form_data.get('stories', [])}")
            print("=" * 60)
        
        # Generate test templates
        template_files = generate_test_templates(form_data)
        
        return jsonify({
            'success': True,
            'message': f'Successfully generated {len(template_files)} test template variations!',
            'local_files': template_files,
            'templates_count': len(template_files)
        })
        
    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Missing required data field: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to process form data: {str(e)}'
        }), 500

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
            return {"success": False, "error": "No data received"}, 400
            
        api_key = data.get("api_key", "").strip()
        server_prefix = data.get("server_prefix", "").strip()
        
        if not api_key or not server_prefix:
            return {"success": False, "error": "Both API key and server prefix are required"}, 400
            
        save_credentials(api_key, server_prefix)
        return {"success": True, "message": "Credentials saved successfully"}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to save credentials: {str(e)}"}, 500

@app.route("/api/check-credentials", methods=["GET"])
def api_check_credentials():
    """
    API endpoint to check if Mailchimp credentials exist and are non-empty in .env.
    
    Returns:
        JSON response with credential presence status
    """
    try:
        has_credentials = credentials_present()
        return {"hasCredentials": has_credentials, "success": True}
    except Exception as e:
        return {"hasCredentials": False, "success": False, "error": str(e)}, 500

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