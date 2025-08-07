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
from googletrans import Translator
import shutil
from urllib.parse import urlparse
import requests

# Assuming mailchimp_template_upload, mailchimp_image_upload, and image_utils are in the same directory
from mailchimp_template_upload import upload_template_to_mailchimp, MailchimpUploadError
from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError
from image_utils import compress_image_if_needed

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hrf-newsletter-secret-key'

# Initialize translator
translator = Translator()

def translate_text(text, target_language, source_language='en'):
    """Translate text to target language using Google Translate."""
    if not text or not text.strip():
        return text
    
    # Skip translation if target is same as source
    if target_language == source_language:
        return text
        
    try:
        result = translator.translate(text, dest=target_language, src=source_language)
        return result.text
    except Exception as e:
        print(f"Warning: Translation failed for '{text}' to {target_language}: {e}")
        return text  # Return original text if translation fails

def download_image_from_url(url, local_path):
    """Download an image from URL to local path."""
    try:
        print(f"Downloading image from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded image to: {local_path}")
        return True
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return False

def collect_user_images(form_data, project_root, geo):
    """Collect and process user-provided images from form data."""
    user_images = []
    temp_dir = os.path.join(project_root, 'temp_images')
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"Collecting user images for geo: {geo}")
    
    # Process hero image
    hero_image = form_data.get('hero', {}).get('image', '')
    print(f"Hero image URL: {hero_image}")
    if hero_image:
        if hero_image.startswith('http'):
            # Determine file extension from URL or default to jpg
            try:
                parsed_url = urlparse(hero_image)
                path = parsed_url.path
                if '.' in path:
                    ext = path.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = f"hero_{geo}.{ext}"
                    else:
                        filename = f"hero_{geo}.jpg"
                else:
                    filename = f"hero_{geo}.jpg"
            except:
                filename = f"hero_{geo}.jpg"
            
            local_path = os.path.join(temp_dir, filename)
            if download_image_from_url(hero_image, local_path):
                user_images.append((f"temp_images/{filename}", local_path))
                print(f"Successfully collected hero image: {filename}")
            else:
                print(f"Failed to download hero image from: {hero_image}")
    
    # Process story images
    for i, story in enumerate(form_data.get('stories', [])):
        story_image = story.get('image', '')
        print(f"Story {i+1} image URL: {story_image}")
        if story_image and story_image.startswith('http'):
            # Determine file extension from URL or default to jpg
            try:
                parsed_url = urlparse(story_image)
                path = parsed_url.path
                if '.' in path:
                    ext = path.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = f"story{i+1}_{geo}.{ext}"
                    else:
                        filename = f"story{i+1}_{geo}.jpg"
                else:
                    filename = f"story{i+1}_{geo}.jpg"
            except:
                filename = f"story{i+1}_{geo}.jpg"
            
            local_path = os.path.join(temp_dir, filename)
            if download_image_from_url(story_image, local_path):
                user_images.append((f"temp_images/{filename}", local_path))
                print(f"Successfully collected story {i+1} image: {filename}")
            else:
                print(f"Failed to download story {i+1} image from: {story_image}")
    
    print(f"Total user images collected: {len(user_images)}")
    return user_images

def copy_images_for_local_newsletter(all_images, project_root):
    """Copy all images to the generated_newsletters folder for local viewing."""
    output_dir = os.path.join(project_root, 'generated_newsletters')
    copied_images = {}
    
    for relative_path, full_path in all_images:
        if os.path.exists(full_path):
            # Create destination path in generated_newsletters
            dest_path = os.path.join(output_dir, relative_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            try:
                shutil.copy2(full_path, dest_path)
                copied_images[relative_path] = dest_path
                print(f"Copied image: {relative_path}")
            except Exception as e:
                print(f"Error copying image {relative_path}: {e}")
        else:
            print(f"Warning: Image not found: {full_path}")
    
    return copied_images

def save_local_newsletter(html_content, geo, lang, project_root, all_images=None):
    """Save newsletter HTML to local generated_newsletters folder with images."""
    output_dir = os.path.join(project_root, 'generated_newsletters')
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy images to local folder
    if all_images:
        print("Copying images for local newsletter...")
        copy_images_for_local_newsletter(all_images, project_root)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"newsletter_{geo}_{lang}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Local newsletter saved: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving local newsletter: {e}")
        return None

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



def find_all_images_to_upload(project_root, user_images=None):
    """Finds all image files in images/brand folder and user-provided images that need to be uploaded."""
    image_files = []
    
    # Find all images in brand folder
    brand_images_dir = os.path.join(project_root, 'images', 'brand')
    if os.path.exists(brand_images_dir):
        for filename in os.listdir(brand_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                relative_path = f"images/brand/{filename}"
                full_path = os.path.join(brand_images_dir, filename)
                image_files.append((relative_path, full_path))
        print(f"Found {len(image_files)} brand images")
    else:
        print("Warning: images/brand folder not found")
    
    # Add user-provided images
    if user_images:
        image_files.extend(user_images)
        print(f"Added {len(user_images)} user-provided images")
    
    return image_files

def find_image_urls_in_html(html_content):
    """Finds all image src URLs in the rendered HTML content."""
    import re
    # Find all src attributes in img tags
    img_src_pattern = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
    matches = re.findall(img_src_pattern, html_content, re.IGNORECASE)
    return list(set(matches))  # Return unique URLs

def validate_brand_folder(project_root):
    """Validates that the brand images folder exists."""
    brand_folder = os.path.join(project_root, 'images', 'brand')
    return os.path.exists(brand_folder)

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

def generate_newsletter_for_geo_lang(geo, lang, data, successful_uploads, project_root, user_images=None, form_data=None):
    """Generates a newsletter for a specific geo and language with translation, local saving, and Mailchimp upload."""
    print(f"\n=== Generating newsletter for {geo}-{lang} ===")
    
    # Get base context
    context, resolved_geo = get_newsletter_context(data, geo, lang)
    if not context:
        print(f"Error: Could not build context for geo '{geo}-{lang}'. Skipping.")
        return

    # --- Apply translations if form_data is provided ---
    if form_data and lang != 'en':
        print(f"Translating content to {lang}...")
        
        # Translate hero content
        if 'hero' in context:
            if 'image_alt' in context['hero']:
                context['hero']['image_alt'] = translate_text(context['hero']['image_alt'], lang)
            if 'headline' in context['hero']:
                context['hero']['headline'] = translate_text(context['hero']['headline'], lang)
            if 'description' in context['hero']:
                context['hero']['description'] = translate_text(context['hero']['description'], lang)
            
            # Translate CTA buttons
            if 'ctas_buttons' in context['hero']:
                for cta in context['hero']['ctas_buttons']:
                    if 'text' in cta:
                        cta['text'] = translate_text(cta['text'], lang)
        
        # Translate stories content
        if 'stories' in context:
            for story in context['stories']:
                if 'image_alt' in story:
                    story['image_alt'] = translate_text(story['image_alt'], lang)
                if 'headline' in story:
                    story['headline'] = translate_text(story['headline'], lang)
                if 'description' in story:
                    story['description'] = translate_text(story['description'], lang)

    # --- Validate brand folder exists ---
    if not validate_brand_folder(project_root):
        print(f"Warning: images/brand folder not found")
        # Continue with processing - user images may still be available

    # --- Render HTML template ---
    template_loader = FileSystemLoader(searchpath=os.path.join(project_root, 'templates'))
    env = Environment(loader=template_loader)
    template = env.get_template('newsletter_template.html')
    html_content = template.render(context)

    # --- Collect all images (brand + user-provided) ---
    all_images = find_all_images_to_upload(project_root, user_images)
    print(f"Found {len(all_images)} total images for processing")
    
    # --- Save local copy with images ---
    print("Saving local newsletter...")
    local_filename = save_local_newsletter(html_content, geo, lang, project_root, all_images)
    
    # --- Prepare for Mailchimp upload ---
    html_for_mailchimp = html_content
    try:
        
        if all_images:
            # Upload all images and build URL mapping
            url_mappings = {}  # Maps relative_path to mailchimp_url
            
            for relative_path, full_path in all_images:
                print(f"Processing image: {relative_path}")
                compressed_path = compress_image_if_needed(full_path)
                mailchimp_url = upload_image_to_mailchimp(compressed_path)
                url_mappings[relative_path] = mailchimp_url
                print(f"Uploaded: {relative_path} -> {mailchimp_url}")
            
            # Replace URLs in HTML for Mailchimp
            print("Replacing image URLs for Mailchimp...")
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
                if local_url in html_for_mailchimp:
                    html_for_mailchimp = html_for_mailchimp.replace(local_url, mailchimp_url)
                    print(f"Replaced '{local_url}' with Mailchimp URL")

    except (MailchimpImageUploadError, Exception) as e:
        print(f"ERROR: Failed during image processing for geo '{geo}-{lang}'.")
        print(f"Reason: {e}")
        sys.exit(1)

    # --- Upload to Mailchimp with improved naming ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    template_name = f"newsletter_{geo}_{lang}_{timestamp}"
    try:
        print(f"Uploading to Mailchimp: {template_name}")
        upload_template_to_mailchimp(html_for_mailchimp, template_name)
        print(f"Successfully uploaded '{template_name}' to Mailchimp.")
        successful_uploads.append(template_name)
        return {'local': local_filename, 'mailchimp': template_name}
    except MailchimpUploadError as e:
        print(f"ERROR: Failed to upload newsletter '{template_name}'.")
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
        
        # Load brand information
        brand_file = os.path.join(project_root, 'data', 'brand_information.json')
        with open(brand_file, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
        
        # Create custom newsletter data with form inputs
        custom_data = {
            'global': brand_data,
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
                        'image_alt': form_data['hero'].get('imageAlt', f'Newsletter hero image for {country}'),
                        'headline': form_data['hero'].get('headline', f'Newsletter for {country}'),
                        'description': form_data['hero'].get('description', f'Latest news and updates for {country}'),
                        'ctas_buttons': [{'text': cta['text']} for cta in form_data.get('ctas', [])]
                    },
                    'stories': [{
                        'image_alt': story.get('imageAlt', f'Story {i+1} image'),
                        'headline': story.get('headline', f'Story {i+1}'),
                        'description': story.get('description', 'Read more about this important story.')
                    } for i, story in enumerate(form_data.get('stories', []))]
                }
        
        # Collect user-provided images
        print(f"Collecting user images for {country} ({geo})...")
        user_images = collect_user_images(form_data, project_root, geo)
        
        # Generate newsletters for all languages with translation
        successful_uploads = []
        generation_results = []
        
        print(f"Generating newsletters for {len(custom_data[geo]['languages'])} languages...")
        for lang in custom_data[geo]['languages']:
            result = generate_newsletter_for_geo_lang(
                geo, lang, custom_data, successful_uploads, project_root, 
                user_images=user_images, form_data=form_data
            )
            if result:
                generation_results.append(result)
        
        # Clean up temporary images
        temp_dir = os.path.join(project_root, 'temp_images')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print("Cleaned up temporary images")
            except Exception as e:
                print(f"Warning: Could not clean up temp images: {e}")
        
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
        
        # Load brand information (legacy endpoint - consider removing)
        brand_file = os.path.join(project_root, 'data', 'brand_information.json')
        with open(brand_file, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
        
        # Create minimal data structure for legacy compatibility
        newsletter_data = {'global': brand_data}
        
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
