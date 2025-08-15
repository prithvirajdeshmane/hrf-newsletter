from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file, abort
from scripts.DataManager import DataManager
from scripts.image_utils import ImageProcessor
from scripts.translation_service import NewsletterTranslationService
from scripts.mailchimp_image_uploader import MailchimpImageUploader
from scripts.mailchimp_newsletter_uploader import MailchimpNewsletterUploader
import threading
import webbrowser
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re
import secrets

# Constants
from config import GENERATED_NEWSLETTERS_DIR

DEBUG_LOGGING = False  # Console logging enabled for debugging

# Initialize the Flask application
app = Flask(__name__)
# Configure secret key for sessions (production-ready)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
# Create a DataManager instance for handling country data
data_manager = DataManager()
# Initialize translation service
translation_service = NewsletterTranslationService()

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
    languages_dict = country_info.get('languages', {})
    
    if not languages_dict:
        raise ValueError(f"No languages found for country: {country_key}")
    
    # Convert languages dictionary to list of language info objects
    languages = []
    for language_name, language_data in languages_dict.items():
        language_info = {
            'name': language_name,
            'code': language_data.get('languageCode', 'en'),
            'locale': language_data.get('locale', 'en-US'),
            'preferredName': language_data.get('preferredName', ''),
            'scriptDirection': language_data.get('scriptDirection', 'ltr')
        }
        languages.append(language_info)
    
    return country_info, country_name, languages


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


def _create_template_data(form_data: Dict[str, Any], country_name: str, language_info: Dict[str, Any], country_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create template data for newsletter generation.
    
    Args:
        form_data: User form data
        country_name: Name of the country
        language_info: Language information
        country_data: Full country data for translation context
        
    Returns:
        Template data dictionary
    """
    hero_data = form_data.get('hero', {})
    hero_ctas = form_data.get('ctas', [])
    user_stories = form_data.get('stories', [])
    
    # Map hero fields to template-expected names
    hero = {
        'image_url': hero_data.get('image', ''),
        'image_alt': hero_data.get('imageAlt', ''),
        'headline': hero_data.get('headline', ''),
        'description': hero_data.get('description', ''),
        'url': hero_data.get('url', ''),
        'cta': hero_data.get('cta'),  # CTA structure is already correct
        'learn_more_text': 'Learn more'  # Default text
    }
    
    # Map story fields to template-expected names
    stories = [map_story_fields(story) for story in user_stories]
    
    # Create base template data
    template_data = {
        'hero': hero,
        'stories': stories,
        'ctas': hero_ctas,
        'country': country_name,
        'lang': language_info.get('code', 'en'),
        'dir': language_info.get('scriptDirection', 'ltr')
    }
    
    # Apply translations if not English
    target_language = language_info.get('code', 'en')
    if target_language != 'en' and translation_service.is_available():
        try:
            # Translate the content
            translated_content = translation_service.translate_newsletter_content(
                template_data, target_language, country_data or {}
            )
            template_data.update(translated_content)
            
            # Use country display name if available
            if 'country_display_name' in translated_content:
                template_data['country'] = translated_content['country_display_name']

            # Update hero with translated 'Learn more' text
            if template_data.get('static_translations', {}).get('learn_more'):
                hero['learn_more_text'] = template_data['static_translations']['learn_more']
                
        except Exception as e:
            print(f"WARNING: Translation failed for {target_language}: {e}")
            print("Continuing with original English content...")
    
    return template_data




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
    country_key = form_data['country']
    country_info, country_name, languages = _load_country_data(country_key)
    
    # Get or create session ID for image isolation
    from flask import session as flask_session
    session_id = flask_session.get('session_id')
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())[:8]  # Short session ID
        flask_session['session_id'] = session_id
    
    # Initialize image processor with session ID for user isolation
    image_processor = ImageProcessor(session_id=session_id)
    
    # Clean up old images in this session before saving new ones
    image_processor.cleanup_old_images()
    
    # Save user images and get local file paths
    saved_images = image_processor.save_user_images(form_data)
    
    # Update form data with local image paths
    if 'hero' in saved_images:
        form_data['hero']['image'] = saved_images['hero']
    
    for i, story in enumerate(form_data.get('stories', []), 1):
        story_key = f'story{i}'
        if story_key in saved_images:
            story['image'] = saved_images[story_key]
    
    # Use OOP path utility for country newsletter directory and filename
    from scripts.utils.country_newsletter_path import CountryNewsletterPath
    country_path = CountryNewsletterPath(country_key)

    generated_files = []
    timestamp = datetime.now().strftime("%m%d%y_%H%M%S")
    
    for language_info in languages:
        language_code = language_info.get('code', 'en')
        
        # Create template data for this language with translation support
        template_data = _create_template_data(form_data, country_name, language_info, country_info)
        
        # Ensure country newsletter directory exists
        country_dir = country_path.ensure_newsletter_dir()
        
        # Generate newsletter file
        language_name = language_info.get('name', 'Unknown')
        filename = country_path.get_newsletter_filename(language_name, timestamp)
        file_path = country_dir / filename
        
        # Render template using Flask's render_template
        template_html = render_template('newsletter_template.html', **template_data)
        
        # Save rendered newsletter
        with open(file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(template_html)
        
        generated_files.append(str(file_path))
        
        if DEBUG_LOGGING:
            print(f"Generated newsletter: {file_path}")
    
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
        Rendered HTML page with country dropdown
    """
    try:
        countries = data_manager.get_countries()
        return render_template("index.html", countries=countries)
    except Exception as e:
        # Fallback to empty countries if data loading fails
        return render_template("index.html", countries={}, error=str(e))

@app.route('/api/select-country', methods=['POST'])
def api_select_country():
    """
    API endpoint to store selected country in session and return redirect URL.
    
    Expects JSON: {"country": str}
    
    Returns:
        JSON response with redirect URL
    """
    try:
        data = request.get_json()
        if not data or 'country' not in data:
            return jsonify({'success': False, 'error': 'Country is required'}), 400
            
        country = data['country'].strip()
        if not country:
            return jsonify({'success': False, 'error': 'Country cannot be empty'}), 400
            
        # Store country in session
        session['selected_country'] = country
        
        return jsonify({
            'success': True,
            'redirect_url': '/build-newsletter'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to select country: {str(e)}'}), 500

@app.route("/build-newsletter")
def build_newsletter() -> str:
    """
    Render the build-newsletter.html page.
    
    The selected country is read from the session.
    
    Returns:
        Rendered HTML page for newsletter building interface
    """
    # Check if country is selected in session
    selected_country = session.get('selected_country')
    
    if not selected_country:
        # No country selected, redirect to home
        return redirect(url_for('index'))
    
    return render_template("build-newsletter.html", selected_country=selected_country)

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
        
        # Store results in session for secure access
        country = form_data['country']
        languages = form_data.get('languages', '').split(',') if form_data.get('languages') else []
        filenames = [Path(file_path).name for file_path in generated_files]
        
        session['newsletter_results'] = {
            'country': country,
            'total_newsletters': len(generated_files),
            'languages': languages,
            'filenames': filenames,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': f'Successfully generated {len(generated_files)} newsletter(s)',
            'files': generated_files,
            'redirect_url': '/newsletters-generated'
        })
        
    except Exception as e:
        error_msg = f"Failed to process form data: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/newsletters-generated', methods=['GET', 'POST'])
def newsletters_generated():
    """
    Display the newsletter generation results page or handle image uploads.
    
    GET: Display results page
    POST: Handle Mailchimp image upload
    
    Returns:
        GET: Rendered HTML page showing generation results and upload options
        POST: JSON response with upload results
    """
    if request.method == 'POST':
        # Handle Mailchimp image upload
        try:
            uploader = MailchimpImageUploader()
            session_id = session.get('session_id')
            results = uploader.upload_session_images(session_id)
            return jsonify(results)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Upload initialization failed: {str(e)}',
                'total_images': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'results': []
            }), 500
    
    # GET request - display results page
    results = session.get('newsletter_results')
    
    if not results:
        # No results in session, redirect to home
        return redirect(url_for('index'))
    
    # Clear the session data after use (optional - prevents back button issues)
    # session.pop('newsletter_results', None)
    
    return render_template('newsletters-generated.html', 
                         country=results['country'],
                         total_newsletters=results['total_newsletters'],
                         languages=results['languages'],
                         filenames=results['filenames'])

@app.route('/preview/newsletter/<path:filename>')
def preview_newsletter(filename):
    """
    Serve newsletter HTML files for preview with strict security validation.
    
    Security measures:
    - Only serves files from generated_newsletters directory
    - Only allows .html files
    - Validates file path to prevent directory traversal
    - Returns 404 for any invalid or non-existent files
    """
    try:
        # Security: Only allow .html files
        if not filename.endswith('.html'):
            abort(404)
        
        # Security: Prevent directory traversal attacks
        if '..' in filename or filename.startswith('/') or '\\' in filename:
            abort(404)
        
        # Construct safe file path within generated_newsletters directory
        from pathlib import Path
        from config import GENERATED_NEWSLETTERS_DIR
        
        safe_path = Path(GENERATED_NEWSLETTERS_DIR) / filename
        
        # Security: Ensure the resolved path is still within our directory
        try:
            safe_path = safe_path.resolve()
            base_dir = Path(GENERATED_NEWSLETTERS_DIR).resolve()
            if not str(safe_path).startswith(str(base_dir)):
                abort(404)
        except (OSError, ValueError):
            abort(404)
        
        # Check if file exists
        if not safe_path.exists() or not safe_path.is_file():
            abort(404)
        
        # Read the HTML file and fix relative image paths for preview
        with open(safe_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Fix relative image paths to work in preview context
        # Convert ../../static/ to /static/ for Flask static file serving
        html_content = html_content.replace('../../static/', '/static/')
        
        # Return the modified HTML content
        from flask import Response
        return Response(html_content, mimetype='text/html')
        
    except Exception:
        # Any unexpected error should return 404 for security
        abort(404)

@app.route('/api/upload-newsletters', methods=['POST'])
def api_upload_newsletters():
    """
    Handle newsletter upload to Mailchimp after image uploads are complete.
    
    Thin wrapper around MailchimpNewsletterUploader class.
    
    Returns:
        JSON response with upload results and redirect URL
    """
    try:
        # Get session data
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID required'}), 400
        
        newsletter_results = session.get('newsletter_results')
        if not newsletter_results:
            return jsonify({'success': False, 'error': 'No newsletter generation results found'}), 400
        
        # Build file paths from session data
        country = newsletter_results['country']
        filenames = newsletter_results['filenames']
        from scripts.utils.country_newsletter_path import CountryNewsletterPath
        country_dir = CountryNewsletterPath(country).newsletter_dir()
    
        newsletter_files = []
        for filename in filenames:
            file_path = country_dir / filename
            if file_path.exists():
                newsletter_files.append(str(file_path))
        
        if not newsletter_files:
            return jsonify({'success': False, 'error': 'No newsletter files found to upload'}), 400
        
        # Use class-based approach for upload logic
        uploader = MailchimpNewsletterUploader()
        upload_results = uploader.upload_newsletter_session(session_id, country)
        
        # Store results in session for success page
        total_newsletters = upload_results['successful_count'] + upload_results['failed_count']
        session['newsletter_upload_results'] = {
            'success': upload_results['success'],
            'total_newsletters': total_newsletters,
            'successful_uploads': upload_results['successful_count'],
            'failed_uploads': upload_results['failed_count'],
            'uploaded_files': [r for r in upload_results['newsletter_results'] if r['status'] == 'success'],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': upload_results['success'],
            'message': upload_results['message'],
            'redirect_url': '/newsletters-uploaded'
        })
        
    except Exception as e:
        error_msg = f"Newsletter upload failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/newsletters-uploaded')
def newsletters_uploaded():
    """
    Display the newsletter upload success page.
    
    Returns:
        Rendered HTML page showing upload results and next steps
    """
    upload_results = session.get('newsletter_upload_results')
    
    if not upload_results:
        # No upload results in session, redirect to home
        return redirect(url_for('index'))
    
    return render_template('newsletters-uploaded.html', 
                         success=upload_results['success'],
                         total_newsletters=upload_results['total_newsletters'],
                         successful_uploads=upload_results['successful_uploads'],
                         failed_uploads=upload_results['failed_uploads'],
                         uploaded_files=upload_results['uploaded_files'])

def open_browser() -> None:
    """
    Open the default web browser to the Flask application URL.
    
    This function is called automatically when the Flask app starts
    to provide a better user experience in development.
    """
    # Only open browser in development mode
    if os.environ.get('FLASK_ENV') == 'development':
        webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug_mode, host=host, port=port)