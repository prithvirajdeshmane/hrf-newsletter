import os
import json
import sys
import webbrowser
import threading
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import copy
import re
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv, set_key

# Assuming mailchimp_template_upload, mailchimp_image_upload, and image_utils are in the same directory
from mailchimp_template_upload import upload_template_to_mailchimp, MailchimpUploadError
from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError
from image_utils import compress_image_if_needed

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hrf-newsletter-secret-key'

def deep_merge(source, destination):
    """Recursively merges source dict into a copy of destination dict, intelligently merging lists of objects."""
    result = copy.deepcopy(destination)
    for key, value in source.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(value, result[key])
        elif isinstance(value, list) and key in result and isinstance(result[key], list):
            if len(value) == len(result[key]):
                result[key] = [deep_merge(src_item, dest_item) for src_item, dest_item in zip(value, result[key])]
            else:
                result[key] = value
        else:
            result[key] = value
    return result



def find_all_images_to_upload(geo, project_root):
    """Finds all image files in images/brand and images/{geo} folders that need to be uploaded."""
    image_files = []
    
    # Find all images in brand folder
    brand_images_dir = os.path.join(project_root, 'images', 'brand')
    if os.path.exists(brand_images_dir):
        for filename in os.listdir(brand_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                relative_path = f"images/brand/{filename}"
                full_path = os.path.join(brand_images_dir, filename)
                image_files.append((relative_path, full_path))
    
    # Find all images in geo-specific folder
    geo_images_dir = os.path.join(project_root, 'images', geo)
    if os.path.exists(geo_images_dir):
        for filename in os.listdir(geo_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                relative_path = f"images/{geo}/{filename}"
                full_path = os.path.join(geo_images_dir, filename)
                image_files.append((relative_path, full_path))
    
    return image_files

def find_image_urls_in_html(html_content):
    """Finds all image src URLs in the rendered HTML content."""
    import re
    # Find all src attributes in img tags
    img_src_pattern = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
    matches = re.findall(img_src_pattern, html_content, re.IGNORECASE)
    return list(set(matches))  # Return unique URLs

def validate_image_folders(geo, project_root):
    """Validates that the required image folders exist."""
    missing_folders = []
    
    brand_folder = os.path.join(project_root, 'images', 'brand')
    if not os.path.exists(brand_folder):
        missing_folders.append('images/brand')
    
    geo_folder = os.path.join(project_root, 'images', geo)
    if not os.path.exists(geo_folder):
        missing_folders.append(f'images/{geo}')
    
    return missing_folders

def get_newsletter_context(data, geo, lang):
    """Constructs the final context for a given geo and language, handling all data merging."""
    global_data = data.get('global', {})
    geo_block = data.get(geo, {})

    # Deep merge global data into the specific geo block
    # This ensures that all top-level data from global is available
    merged_data = deep_merge(global_data, geo_block)

    # If the geo has translations, merge the specific language data
    translations = merged_data.get('translations')
    if translations and lang in translations:
        lang_data = translations[lang]
        # Merge the language data into the already merged block
        final_data = deep_merge(merged_data, lang_data)
    else:
        # If no translations or lang not found, use the merged block as is
        final_data = merged_data

    # The template requires a 'global' key, so we ensure it's there
    final_data['global'] = global_data
    final_data['today'] = datetime.now().strftime('%Y-%m-%d')
    
    # Remove the translations block from the final context to avoid clutter
    final_data.pop('translations', None)

    return final_data, f"{geo}-{lang}"

def generate_newsletter_for_geo_lang(geo, lang, data, successful_uploads, project_root):
    """Generates a newsletter for a specific geo and language, then uploads it to Mailchimp."""
    context, resolved_geo = get_newsletter_context(data, geo, lang)

    if not context:
        print(f"\nError: Could not build context for geo '{geo}-{lang}'. Skipping.")
        return

    # --- Validate image folders exist ---
    missing_folders = validate_image_folders(geo, project_root)
    if missing_folders:
        print(f"\nError: For geo '{geo}', missing image folders:")
        for folder in missing_folders:
            print(f"- {folder}")
        sys.exit(1)

    template_loader = FileSystemLoader(searchpath=os.path.join(project_root, 'templates'))
    env = Environment(loader=template_loader)
    template = env.get_template('newsletter_template.html')
    html_content = template.render(context)

    # --- Upload ALL images from global and geo folders ---
    html_for_mailchimp = html_content
    try:
        # Find all images that need to be uploaded
        images_to_upload = find_all_images_to_upload(geo, project_root)
        print(f"Found {len(images_to_upload)} images to upload from brand and {geo} folders")
        
        local_to_mailchimp_url = {}
        
        # Upload all images and build URL mapping
        url_mappings = {}  # Maps relative_path to mailchimp_url
        
        for relative_path, full_path in images_to_upload:
            compressed_path = compress_image_if_needed(full_path)
            mailchimp_url = upload_image_to_mailchimp(compressed_path)
            url_mappings[relative_path] = mailchimp_url
        
        # Find all image URLs actually used in the rendered HTML
        html_image_urls = find_image_urls_in_html(html_content)
        print(f"Found {len(html_image_urls)} image URLs in rendered HTML: {html_image_urls}")
        
        # Replace URLs in HTML, handling different URL formats
        # Sort by length (longest first) to avoid partial replacements
        all_possible_urls = []
        for relative_path, mailchimp_url in url_mappings.items():
            # Generate all possible URL variants for this image
            variants = [
                f"./{relative_path}",  # ./images/brand/HRF-Logo.png
                f"/{relative_path}",   # /images/brand/HRF-Logo.png  
                relative_path,         # images/brand/HRF-Logo.png
            ]
            for variant in variants:
                all_possible_urls.append((variant, mailchimp_url))
        
        # Sort by URL length (longest first) to avoid partial matches
        all_possible_urls.sort(key=lambda x: len(x[0]), reverse=True)
        
        # Replace URLs in the HTML
        for local_url, mailchimp_url in all_possible_urls:
            # Only replace if the local URL actually appears in the HTML
            if local_url in html_for_mailchimp:
                html_for_mailchimp = html_for_mailchimp.replace(local_url, mailchimp_url)
                print(f"Replaced '{local_url}' with '{mailchimp_url}'")

    except (MailchimpImageUploadError, Exception) as e:
        print(f"\nERROR: Failed during image processing for geo '{resolved_geo}'.")
        print(f"Reason: {e}")
        sys.exit(1)

    # --- Upload to Mailchimp ---
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    template_name = f"newsletter_{resolved_geo}_{timestamp}"
    try:
        upload_template_to_mailchimp(html_for_mailchimp, template_name)
        print(f"Successfully uploaded '{template_name}' to Mailchimp.")
        successful_uploads.append(template_name)
    except MailchimpUploadError as e:
        print(f"\nERROR: Failed to upload newsletter '{template_name}'.")
        print(f"Reason: {e}")
        sys.exit(1)

# Flask Routes
@app.route('/')
def index():
    """Serve the main HTML page."""
    project_root = get_project_root()
    return send_from_directory(project_root, 'index.html')

@app.route('/build-newsletter')
def build_newsletter():
    """Serve the build newsletter page."""
    project_root = get_project_root()
    return send_from_directory(project_root, 'build-newsletter.html')

@app.route('/api/countries')
def get_countries():
    """Get the list of countries from country_languages.json."""
    try:
        project_root = get_project_root()
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries = json.load(f)
        
        return jsonify(countries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-credentials')
def check_credentials():
    """Check if Mailchimp credentials are set."""
    load_dotenv()
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')
    
    has_credentials = bool(api_key and api_key.strip() and server_prefix and server_prefix.strip())
    
    return jsonify({'hasCredentials': has_credentials})

@app.route('/api/save-credentials', methods=['POST'])
def save_credentials():
    """Save Mailchimp credentials to .env file."""
    try:
        data = request.get_json()
        api_key = data.get('apiKey', '').strip()
        server_prefix = data.get('serverPrefix', '').strip()
        
        if not api_key or not server_prefix:
            return jsonify({'error': 'Both API key and server prefix are required'}), 400
        
        project_root = get_project_root()
        env_file = os.path.join(project_root, '.env')
        
        # Create .env file if it doesn't exist
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write('')
        
        # Save credentials
        set_key(env_file, 'MAILCHIMP_API_KEY', api_key)
        set_key(env_file, 'MAILCHIMP_SERVER_PREFIX', server_prefix)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/build-newsletter', methods=['POST'])
def build_newsletter_api():
    """Generate newsletter with custom content from the build form."""
    try:
        form_data = request.get_json()
        country = form_data.get('country')
        
        if not country:
            return jsonify({'error': 'Country is required'}), 400
        
        # Map country to geo code
        geo_mapping = {
            'United States': 'us',
            'Canada': 'ca',
            'Mexico': 'mx',
            'Brazil': 'br',
            'Chile': 'ch',
            'Argentina': 'ar',
            'Colombia': 'co',
            'Peru': 'pe',
            'Ecuador': 'ec',
            'Bolivia': 'bo',
            'Paraguay': 'py',
            'Uruguay': 'uy',
            'Venezuela': 've',
            'Guatemala': 'gt',
            'Honduras': 'hn',
            'El Salvador': 'sv',
            'Nicaragua': 'ni',
            'Costa Rica': 'cr',
            'Panama': 'pa',
            'Dominican Republic': 'do',
            'Cuba': 'cu',
            'Haiti': 'ht',
            'Jamaica': 'jm',
            'Trinidad and Tobago': 'tt',
            'Barbados': 'bb',
            'Bahamas': 'bs',
            'Belize': 'bz',
            'Guyana': 'gy',
            'Suriname': 'sr',
            'French Guiana': 'gf'
        }
        
        geo = geo_mapping.get(country)
        if not geo:
            return jsonify({'error': f'No geo mapping found for country "{country}"'}), 400
        
        # Create custom newsletter data from form input
        project_root = get_project_root()
        
        # Load base newsletter data structure
        data_file = os.path.join(project_root, 'data', 'newsletter_data.json')
        with open(data_file, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
        
        # Create custom newsletter data with form inputs
        custom_data = {
            'global': base_data.get('global', {}),
            geo: {
                'hero': {
                    'image_url': form_data['hero']['image'],
                    'cta_learn_more_url': form_data['hero'].get('learnMoreUrl', ''),
                    'ctas_buttons': [{'url': cta['url']} for cta in form_data.get('ctas', [])]
                },
                'stories': [{
                    'image_url': story['image'],
                    'url': story['url']
                } for story in form_data.get('stories', [])],
                'translations': {},
                'languages': []
            }
        }
        
        # Get languages from country_languages.json
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        if country in countries_data:
            languages = countries_data[country].get('languages', [])
            
            for lang_info in languages:
                lang_code = lang_info[1]  # Get language code (e.g., 'en', 'fr')
                lang_name = lang_info[0]  # Get language name (e.g., 'English', 'French')
                
                # Add language to the list
                custom_data[geo]['languages'].append(lang_code)
                
                # Create translation data with form inputs
                custom_data[geo]['translations'][lang_code] = {
                    'lang': lang_code,
                    'dir': 'ltr',
                    'metadata': {
                        'country_name': country
                    },
                    'hero': {
                        'image_alt': f'Newsletter hero image for {country}',
                        'headline': f'Newsletter for {country}',
                        'description': f'Latest news and updates for {country}',
                        'ctas_buttons': [{'text': cta['text']} for cta in form_data.get('ctas', [])]
                    },
                    'stories': [{
                        'image_alt': f'Story {i+1} image',
                        'headline': f'Story {i+1}',
                        'description': f'Read more about this important story.'
                    } for i, story in enumerate(form_data.get('stories', []))]
                }
        
        # Generate newsletters for all languages
        successful_uploads = []
        
        for lang in custom_data[geo]['languages']:
            generate_newsletter_for_geo_lang(geo, lang, custom_data, successful_uploads, project_root)
        
        return jsonify({
            'success': True,
            'templates': successful_uploads,
            'message': f'Successfully generated {len(successful_uploads)} newsletter templates'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-newsletter', methods=['POST'])
def generate_newsletter_api():
    """Generate newsletter for the selected country using existing data."""
    try:
        data = request.get_json()
        country = data.get('country')
        
        if not country:
            return jsonify({'error': 'Country is required'}), 400
        
        # Load country mappings
        project_root = get_project_root()
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        if country not in countries_data:
            return jsonify({'error': f'Country "{country}" not found'}), 400
        
        # Map country to geo code
        geo_mapping = {
            'United States': 'us',
            'Canada': 'ca',
            'Mexico': 'mx',
            'Brazil': 'br',
            'Chile': 'ch',
            'Argentina': 'ar',
            'Colombia': 'co',
            'Peru': 'pe',
            'Ecuador': 'ec',
            'Bolivia': 'bo',
            'Paraguay': 'py',
            'Uruguay': 'uy',
            'Venezuela': 've',
            'Guatemala': 'gt',
            'Honduras': 'hn',
            'El Salvador': 'sv',
            'Nicaragua': 'ni',
            'Costa Rica': 'cr',
            'Panama': 'pa',
            'Dominican Republic': 'do',
            'Cuba': 'cu',
            'Haiti': 'ht',
            'Jamaica': 'jm',
            'Trinidad and Tobago': 'tt',
            'Barbados': 'bb',
            'Bahamas': 'bs',
            'Belize': 'bz',
            'Guyana': 'gy',
            'Suriname': 'sr',
            'French Guiana': 'gf'
        }
        
        geo = geo_mapping.get(country)
        if not geo:
            return jsonify({'error': f'No geo mapping found for country "{country}"'}), 400
        
        # Load newsletter data
        data_file = os.path.join(project_root, 'data', 'newsletter_data.json')
        with open(data_file, 'r', encoding='utf-8') as f:
            newsletter_data = json.load(f)
        
        if geo not in newsletter_data:
            return jsonify({'error': f'No newsletter data found for geo "{geo}"'}), 400
        
        # Generate newsletters for all languages in the geo
        successful_uploads = []
        geo_data = newsletter_data[geo]
        
        if 'languages' not in geo_data:
            return jsonify({'error': f'No languages defined for geo "{geo}"'}), 400
        
        for lang in geo_data['languages']:
            generate_newsletter_for_geo_lang(geo, lang, newsletter_data, successful_uploads, project_root)
        
        return jsonify({
            'success': True,
            'templates': successful_uploads,
            'message': f'Successfully generated {len(successful_uploads)} newsletter templates'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def open_browser():
    """Open the web browser after a short delay."""
    import time
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    """Main function to start the web server."""
    print("HRF Newsletter Generator")
    print("=" * 40)
    print("Starting web server...")
    print("Opening browser at http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server
    app.run(host='localhost', port=5000, debug=False)

if __name__ == '__main__':
    main()
