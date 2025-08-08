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

# Set UTF-8 encoding for console output on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Assuming mailchimp_template_upload, mailchimp_image_upload, and image_utils are in the same directory
from mailchimp_template_upload import upload_template_to_mailchimp, MailchimpUploadError
from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError
from image_utils import compress_image_if_needed
from batch_image_upload import upload_images_for_newsletter, replace_image_urls_in_html

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

def save_base64_image(base64_data, local_path):
    """Save a base64 data URL as a local image file."""
    try:
        print(f"Processing base64 image data...")
        print(f"Target path: {local_path}")
        print(f"Target directory: {os.path.dirname(local_path)}")
        
        # Extract the base64 data from the data URL
        if base64_data.startswith('data:'):
            # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...
            header, data = base64_data.split(',', 1)
            print(f"Base64 header: {header}")
            
            # Decode base64 data
            import base64
            image_data = base64.b64decode(data)
            print(f"Decoded image data size: {len(image_data)} bytes")
            
            # Create directory with better error handling
            try:
                target_dir = os.path.dirname(local_path)
                print(f"Creating directory: {target_dir}")
                os.makedirs(target_dir, exist_ok=True)
                print(f"Directory created successfully")
            except Exception as dir_error:
                print(f"Error creating directory {target_dir}: {dir_error}")
                raise
            
            # Write file with better error handling
            try:
                print(f"Writing file: {local_path}")
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                print(f"File written successfully")
            except Exception as file_error:
                print(f"Error writing file {local_path}: {file_error}")
                raise
            
            print(f"Successfully saved base64 image to: {local_path} ({len(image_data)} bytes)")
            return True
        else:
            print(f"Invalid base64 data format: {base64_data[:50]}...")
            return False
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

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

def collect_user_images(form_data, project_root, country_code):
    """Collect and process user-provided images from form data."""
    user_images = []
    temp_dir = os.path.join(project_root, 'temp_images')
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"Collecting user images for country: {country_code}")
    
    # Process hero image
    hero_image = form_data.get('hero', {}).get('image', '')
    print(f"Hero image data: {hero_image[:100]}..." if len(hero_image) > 100 else f"Hero image data: {hero_image}")
    if hero_image:
        if hero_image.startswith('data:'):
            # Handle base64 data URL
            filename = f"hero_{country_code}.jpg"  # Default to jpg for base64
            local_path = os.path.join(temp_dir, filename)
            if save_base64_image(hero_image, local_path):
                user_images.append((f"temp_images/{filename}", local_path))
                print(f"Successfully collected hero image from base64: {filename}")
            else:
                print(f"Failed to save hero image from base64 data")
        elif hero_image.startswith('http'):
            # Handle regular URL
            try:
                parsed_url = urlparse(hero_image)
                path = parsed_url.path
                if '.' in path:
                    ext = path.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = f"hero_{country_code}.{ext}"
                    else:
                        filename = f"hero_{country_code}.jpg"
                else:
                    filename = f"hero_{country_code}.jpg"
            except:
                filename = f"hero_{country_code}.jpg"
            
            local_path = os.path.join(temp_dir, filename)
            if download_image_from_url(hero_image, local_path):
                user_images.append((f"temp_images/{filename}", local_path))
                print(f"Successfully collected hero image from URL: {filename}")
            else:
                print(f"Failed to download hero image from: {hero_image}")
        else:
            print(f"Unsupported hero image format: {hero_image[:50]}...")
    
    # Process story images
    for i, story in enumerate(form_data.get('stories', [])):
        story_image = story.get('image', '')
        print(f"Story {i+1} image data: {story_image[:100]}..." if len(story_image) > 100 else f"Story {i+1} image data: {story_image}")
        if story_image:
            if story_image.startswith('data:'):
                # Handle base64 data URL
                filename = f"story{i+1}_{country_code}.jpg"  # Default to jpg for base64
                local_path = os.path.join(temp_dir, filename)
                if save_base64_image(story_image, local_path):
                    user_images.append((f"temp_images/{filename}", local_path))
                    print(f"Successfully collected story {i+1} image from base64: {filename}")
                else:
                    print(f"Failed to save story {i+1} image from base64 data")
            elif story_image.startswith('http'):
                # Handle regular URL
                try:
                    parsed_url = urlparse(story_image)
                    path = parsed_url.path
                    if '.' in path:
                        ext = path.split('.')[-1].lower()
                        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            filename = f"story{i+1}_{country_code}.{ext}"
                        else:
                            filename = f"story{i+1}_{country_code}.jpg"
                    else:
                        filename = f"story{i+1}_{country_code}.jpg"
                except:
                    filename = f"story{i+1}_{country_code}.jpg"
                
                local_path = os.path.join(temp_dir, filename)
                if download_image_from_url(story_image, local_path):
                    user_images.append((f"temp_images/{filename}", local_path))
                    print(f"Successfully collected story {i+1} image from URL: {filename}")
                else:
                    print(f"Failed to download story {i+1} image from: {story_image}")
            else:
                print(f"Unsupported story {i+1} image format: {story_image[:50]}...")
    
    print(f"Total user images collected: {len(user_images)}")
    return user_images

def copy_images_for_local_newsletter(all_images, project_root, folder_name):
    """Copy all images to the generated_newsletters/{folder_name} folder for local viewing."""
    # Copy images to country-specific folder
    country_output_dir = os.path.join(project_root, 'generated_newsletters', folder_name)
    copied_images = {}
    
    for relative_path, full_path in all_images:
        if os.path.exists(full_path):
            # Create destination path in generated_newsletters/{country_code}
            dest_path = os.path.join(country_output_dir, relative_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            try:
                shutil.copy2(full_path, dest_path)
                copied_images[relative_path] = dest_path
                print(f"Copied image to {folder_name}: {relative_path}")
            except Exception as e:
                print(f"Error copying image {relative_path}: {e}")
        else:
            print(f"Warning: Image not found: {full_path}")
    
    return copied_images

def save_local_newsletter(html_content, country_code, lang, project_root, all_images=None, locale=None, country_name=None):
    """Save newsletter HTML to local generated_newsletters/{country_name} folder with images."""
    # Use country name with underscores for folder, fallback to country_code if not provided
    folder_name = country_name.replace(' ', '_') if country_name else country_code
    
    # Create country-specific folder: /generated_newsletters/{COUNTRY_NAME}/ (with underscores)
    country_output_dir = os.path.join(project_root, 'generated_newsletters', folder_name)
    os.makedirs(country_output_dir, exist_ok=True)
    print(f"Ensuring country folder exists: {country_output_dir}")
    
    # Copy images to local folder
    if all_images:
        print("Copying images for local newsletter...")
        copy_images_for_local_newsletter(all_images, project_root, folder_name)
    
    # New format: newsletter_{locale}_{mmddyy}_{hhmmss}.html (e.g., newsletter_en-CF_080725_111725.html)
    now = datetime.now()
    date_str = now.strftime('%m%d%y')  # MMDDYY format
    time_str = now.strftime('%H%M%S')  # HHMMSS format
    
    # Use locale if provided, otherwise fallback to country_code-lang
    file_identifier = locale if locale else f"{country_code}-{lang}"
    filename = f"newsletter_{file_identifier}_{date_str}_{time_str}.html"
    filepath = os.path.join(country_output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Local newsletter saved: {folder_name}/{filename}")
        return f"{folder_name}/{filename}"
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

async def generate_newsletter_for_geo_lang(country_code, lang, data, successful_uploads, project_root, user_images=None, form_data=None, locale=None, folder_name=None, content_country_name=None, mailchimp_url_mappings=None):
    try:
        print(f"Generating newsletter for {country_code} in {lang}")
        
        # Get language-specific information
        country_data = data.get(content_country_name or country_code, {})
        languages = country_data.get('languages', {})
        language_info = None
        
        # Find the language info by matching language code
        for lang_name, lang_data in languages.items():
            if lang_data.get('languageCode') == lang:
                language_info = lang_data
                break
        
        if not language_info:
            print(f"Warning: Language info not found for {lang} in {country_code}")
            language_info = {}
        
        # Get script direction (default to ltr)
        script_direction = language_info.get('scriptDirection', 'ltr')
        print(f"Script direction for {lang}: {script_direction}")
        
        # Determine display names
        display_country_name = content_country_name if content_country_name else country_code
        file_folder_name = folder_name if folder_name else country_code
        
        # Get preferred country name for this language if available
        preferred_country_name = language_info.get('preferredName', display_country_name)
        
        # Safe Unicode printing for Windows console
        try:
            print(f"Using preferred country name: {preferred_country_name}")
        except UnicodeEncodeError:
            print(f"Using preferred country name: [Unicode text - {len(preferred_country_name)} chars]")
        print(f"Using folder name: {file_folder_name}")
        
        # Build context from form_data if provided
        if form_data:
            print(f"Building context from form data...")
            
            # Use the passed content_country_name for newsletter content, fallback to country_code
            display_country_name = content_country_name if content_country_name else country_code
            
            # Use the passed folder_name for file organization, fallback to country_code
            file_folder_name = folder_name if folder_name else country_code
            
            context = {
                'global': data['global'],
                'metadata': {
                    'country_name': preferred_country_name
                },
                'dir': script_direction,  # Use 'dir' to match HTML template expectation
                'lang': lang,  # Add language code for template
                'hero': {
                    'image_url': form_data['hero']['image'],
                    'image_alt': form_data['hero'].get('imageAlt', ''),
                    'headline': form_data['hero'].get('headline', ''),
                    'description': form_data['hero'].get('description', ''),
                    'cta_learn_more_url': form_data['hero'].get('learnMoreUrl', ''),
                    'ctas_buttons': [{'text': cta['text'], 'url': cta['url']} for cta in form_data.get('ctas', [])]
                },
                'stories': [{
                    'image_url': story['image'],
                    'image_alt': story.get('imageAlt', ''),
                    'headline': story.get('headline', ''),
                    'description': story.get('description', ''),
                    'url': story['url']
                } for story in form_data.get('stories', [])]
            }
        else:
            # Fallback to old method
            context, resolved_geo = get_newsletter_context(data, country_code, lang)
            if not context:
                print(f"Error: Could not build context for geo '{country_code}-{lang}'. Skipping.")
                return
            
            # Add script direction and language to context for old method too
            context['dir'] = script_direction
            context['lang'] = lang
        
        # --- Apply translations if needed ---
        if form_data and lang != 'en':
            print(f"Translating content to {lang}...")
            
            # Translate hero content
            if 'hero' in context:
                if context['hero'].get('image_alt'):
                    context['hero']['image_alt'] = translate_text(context['hero']['image_alt'], lang)
                if context['hero'].get('headline'):
                    context['hero']['headline'] = translate_text(context['hero']['headline'], lang)
                if context['hero'].get('description'):
                    context['hero']['description'] = translate_text(context['hero']['description'], lang)
                
                # Translate CTA buttons
                if 'ctas_buttons' in context['hero']:
                    for cta in context['hero']['ctas_buttons']:
                        if cta.get('text'):
                            cta['text'] = translate_text(cta['text'], lang)
            
            # Translate stories content
            if 'stories' in context:
                for story in context['stories']:
                    if story.get('image_alt'):
                        story['image_alt'] = translate_text(story['image_alt'], lang)
                    if story.get('headline'):
                        story['headline'] = translate_text(story['headline'], lang)
                    if story.get('description'):
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
        
        # --- Replace image URLs with Mailchimp URLs if available ---
        if mailchimp_url_mappings:
            print("Replacing local image URLs with Mailchimp URLs...")
            html_content = replace_image_urls_in_html(html_content, mailchimp_url_mappings)
        
        # --- Save local copy with images ---
        print("Saving local newsletter...")
        local_filename = save_local_newsletter(html_content, country_code, lang, project_root, all_images, locale, file_folder_name)
        
        print(f"\n✅ Newsletter generation completed for {country_code}-{lang}")
        return {'local': local_filename}

    except Exception as e:
        print(f"\n=== EXCEPTION IN generate_newsletter_for_geo_lang ===")
        print(f"Error in generate_newsletter_for_geo_lang: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"=== END EXCEPTION ===")
        sys.stdout.flush()
        return None

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
    import os
    
    # Check if .env file exists
    project_root = get_project_root()
    env_file_path = os.path.join(project_root, '.env')
    env_file_exists = os.path.exists(env_file_path)
    
    print(f"🔍 Checking credentials:")
    print(f"   Project root: {project_root}")
    print(f"   .env file path: {env_file_path}")
    print(f"   .env file exists: {env_file_exists}")
    
    # Clear any existing environment variables to avoid cache issues
    if 'MAILCHIMP_API_KEY' in os.environ:
        del os.environ['MAILCHIMP_API_KEY']
    if 'MAILCHIMP_SERVER_PREFIX' in os.environ:
        del os.environ['MAILCHIMP_SERVER_PREFIX']
    
    # Only load from .env file if it exists
    api_key = None
    server_prefix = None
    
    if env_file_exists:
        # Load environment variables from .env file
        load_dotenv(env_file_path, override=True)
        api_key = os.getenv('MAILCHIMP_API_KEY')
        server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')
    
    print(f"   API key found: {bool(api_key)}")
    print(f"   Server prefix found: {bool(server_prefix)}")
    if api_key:
        print(f"   API key preview: {api_key[:10]}...")
    if server_prefix:
        print(f"   Server prefix: {server_prefix}")
    
    # Credentials are valid only if both exist and are non-empty
    has_credentials = bool(
        env_file_exists and 
        api_key and api_key.strip() and 
        server_prefix and server_prefix.strip()
    )
    
    print(f"   Final result: hasCredentials = {has_credentials}")
    
    return jsonify({
        'hasCredentials': has_credentials,
        'debug': {
            'envFileExists': env_file_exists,
            'envFilePath': env_file_path,
            'hasApiKey': bool(api_key),
            'hasServerPrefix': bool(server_prefix)
        }
    })

@app.route('/api/save-credentials', methods=['POST'])
def save_credentials():
    """Save Mailchimp credentials to .env file with comprehensive validation."""
    import re
    import datetime
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data',
                'details': ['Request body must contain valid JSON']
            }), 400
        
        api_key = data.get('apiKey', '').strip()
        server_prefix = data.get('serverPrefix', '').strip()
        
        # Basic presence validation
        if not api_key or not server_prefix:
            return jsonify({
                'success': False,
                'error': 'API key and server prefix are required',
                'details': [
                    'API key cannot be empty' if not api_key else None,
                    'Server prefix cannot be empty' if not server_prefix else None
                ],
                'suggestions': [
                    'Get your API key from Mailchimp Account > Extras > API keys',
                    'Server prefix is usually like "us21", "eu3", etc.'
                ]
            }), 400
        
        validation_errors = []
        
        # Validate API key format (32 hex characters + dash + server prefix)
        api_key_pattern = r'^[a-f0-9]{32}-[a-z]{2}\d+$'
        if not re.match(api_key_pattern, api_key):
            validation_errors.append('Invalid API key format. Expected: 32 hex characters, dash, then server prefix (e.g., "abc123...xyz-us21")')
        
        # Validate server prefix format (2 letters + numbers)
        server_prefix_pattern = r'^[a-z]{2}\d+$'
        if not re.match(server_prefix_pattern, server_prefix):
            validation_errors.append('Invalid server prefix format. Expected: 2 lowercase letters followed by numbers (e.g., "us21", "eu3")')
        
        # Cross-validation: API key should end with server prefix
        if api_key and server_prefix and '-' in api_key:
            api_key_suffix = api_key.split('-')[-1]
            if api_key_suffix != server_prefix:
                validation_errors.append(f'API key server suffix "{api_key_suffix}" does not match server prefix "{server_prefix}"')
        
        # If validation errors, return them
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Credential validation failed',
                'details': validation_errors,
                'suggestions': [
                    'Check your Mailchimp account settings for the correct API key',
                    'Ensure the server prefix matches your account region',
                    'API key format: 32 hex chars + dash + server prefix',
                    'Server prefix examples: us21, eu3, au1'
                ]
            }), 400
        
        # Save credentials to .env file
        project_root = get_project_root()
        env_file_path = os.path.join(project_root, '.env')
        
        print(f"💾 Saving credentials to: {env_file_path}")
        
        # Create/overwrite .env file with UTF-8 encoding
        env_content = f"""# Mailchimp API Credentials
# Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
MAILCHIMP_API_KEY={api_key}
MAILCHIMP_SERVER_PREFIX={server_prefix}
"""
        
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ Credentials saved successfully")
        
        return jsonify({
            'success': True,
            'message': 'Credentials saved successfully',
            'timestamp': datetime.datetime.now().isoformat(),
            'nextSteps': [
                'Test your connection using the "Test Connection" button',
                'Generate your first newsletter',
                'Check the Mailchimp integration status'
            ]
        }), 200
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'suggestions': [
                'Check file permissions in the project directory',
                'Ensure the project directory is writable',
                'Try again or contact support if the issue persists'
            ]
        }), 500

@app.route('/api/build-newsletter', methods=['POST'])
def build_newsletter_api():
    """Generate newsletter with custom content from the build form."""
    import sys
    import traceback
    
    try:
        print("\n=== API CALL STARTED ===")
        print("Flask route handler called successfully")
        sys.stdout.flush()
        
        print("About to get JSON data from request...")
        sys.stdout.flush()
        print("Getting JSON data from request...")
        sys.stdout.flush()
        
        form_data = request.get_json()
        print(f"Form data received successfully")
        print(f"Form data type: {type(form_data)}")
        print(f"Form data keys: {list(form_data.keys()) if form_data else 'None'}")
        sys.stdout.flush()
        
        if not form_data:
            print("ERROR: No form data received")
            sys.stdout.flush()
            return jsonify({'error': 'No form data received'}), 400
        
        country = form_data.get('country')
        print(f"Country extracted: {country}")
        sys.stdout.flush()
        
        if not country:
            return jsonify({'error': 'Country is required'}), 400
        
        print(f"Processing country: {country}")
        sys.stdout.flush()
        
        # Load country data from new JSON structure
        project_root = get_project_root()
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        if country not in countries_data:
            return jsonify({'error': f'Country "{country}" not found in country_languages.json'}), 400
        
        country_info = countries_data[country]
        country_code = country_info.get('countryCode')
        
        if not country_code:
            return jsonify({'error': f'No countryCode found for country "{country}"'}), 400
        
        print(f"Country code: {country_code}")
        sys.stdout.flush()
        
        # Load brand information
        brand_file = os.path.join(project_root, 'data', 'brand_information.json')
        print(f"Loading brand file: {brand_file}")
        sys.stdout.flush()
        
        with open(brand_file, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
        print(f"Brand data loaded successfully")
        sys.stdout.flush()
        
        # Create custom newsletter data with form inputs using country_code
        custom_data = {
            'global': brand_data,
            country_code: {
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
        
        # Get languages from new JSON structure (languages is now a dict)
        languages_dict = country_info.get('languages', {})
        
        for lang_name, lang_data in languages_dict.items():
            lang_code = lang_data.get('languageCode')
            locale = lang_data.get('locale')
            preferred_name = lang_data.get('preferredName', country)  # Use country name as fallback
            
            if not lang_code or not locale:
                print(f"Warning: Missing languageCode or locale for {lang_name}")
                continue
                
            # Add language info to the list
            custom_data[country_code]['languages'].append([lang_name, lang_code, locale, preferred_name])
            
            # Create translation data with form inputs
            custom_data[country_code]['translations'][lang_code] = {
                'lang': lang_code,
                'locale': locale,
                'dir': 'ltr',
                'metadata': {
                    'country_name': preferred_name  # Use preferred name for this language
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
        
        print(f"\n=== STARTING NEWSLETTER GENERATION ===")
        print(f"Country: {country}")
        print(f"Country Code: {country_code}")
        print(f"Languages: {custom_data[country_code]['languages']}")
        sys.stdout.flush()
        
        # Collect user-provided images
        print(f"\n=== COLLECTING USER IMAGES ===")
        user_images = collect_user_images(form_data, project_root, country_code)
        print(f"User images collected: {len(user_images) if user_images else 0}")
        sys.stdout.flush()
        
        # --- OPTIMIZED MAILCHIMP IMAGE UPLOAD (ONCE PER COUNTRY) ---
        mailchimp_url_mappings = {}
        try:
            print(f"\n🚀 Starting optimized Mailchimp image upload (once per country)...")
            
            # Collect all images (brand + user-provided)
            all_images = find_all_images_to_upload(project_root, user_images)
            print(f"Found {len(all_images)} total images for processing")
            
            if all_images:
                # Extract just the file paths from the (relative_path, full_path) tuples
                image_paths = [full_path for relative_path, full_path in all_images]
                
                # Create usage context mapping (hero, inline, etc.)
                usage_contexts = {}
                priorities = {}
                
                for relative_path, full_path in all_images:
                    if 'hero' in relative_path.lower():
                        usage_contexts[full_path] = 'hero'
                        priorities[full_path] = 'critical'
                    elif 'brand' in relative_path.lower():
                        usage_contexts[full_path] = 'footer'
                        priorities[full_path] = 'important'
                    else:
                        usage_contexts[full_path] = 'inline'
                        priorities[full_path] = 'normal'
                
                # Use our optimized batch upload system
                import asyncio
                upload_summary = asyncio.run(upload_images_for_newsletter(
                    image_paths, 
                    usage_contexts=usage_contexts,
                    priorities=priorities
                ))
                
                print(f"📊 Batch Upload Results:")
                print(f"   ✅ Successful: {upload_summary.successful_uploads}")
                print(f"   💾 Cached: {upload_summary.cached_hits}")
                print(f"   ❌ Failed: {upload_summary.failed_uploads}")
                print(f"   ⏱️  Time: {upload_summary.total_time_seconds:.2f}s")
                print(f"   🔗 URL Mappings: {len(upload_summary.url_mappings)}")
                
                # Store URL mappings for reuse across all languages
                mailchimp_url_mappings = upload_summary.url_mappings
                
                if upload_summary.errors:
                    print("⚠️  Upload Errors:")
                    for error in upload_summary.errors[:3]:  # Show first 3 errors
                        print(f"     - {error}")
                    if len(upload_summary.errors) > 3:
                        print(f"     ... and {len(upload_summary.errors) - 3} more")
                
            else:
                print("ℹ️  No images to upload to Mailchimp")
                
        except Exception as e:
            print(f"❌ Mailchimp image upload failed: {e}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Generate newsletters for all languages with translation
        successful_uploads = []
        generation_results = []
        local_files = []
        
        print(f"\nGenerating newsletters for {len(custom_data[country_code]['languages'])} languages...")
        sys.stdout.flush()
        
        for lang_info in custom_data[country_code]['languages']:
            lang_name = lang_info[0]  # e.g., 'English'
            lang_code = lang_info[1]  # e.g., 'en'
            locale = lang_info[2]     # e.g., 'en-CF'
            preferred_name = lang_info[3]  # e.g., 'République Centrafricaine'
            
            print(f"\nGenerating newsletter for {lang_name} ({lang_code}) - {locale}...")
            print(f"Using country name: {preferred_name}")
            sys.stdout.flush()
            
            import asyncio
            result = asyncio.run(generate_newsletter_for_geo_lang(
                country_code, lang_code, custom_data, successful_uploads, project_root, user_images, form_data, locale, country, preferred_name, mailchimp_url_mappings
            ))
            
            if result and result.get('local'):
                local_files.append(result['local'])
                generation_results.append(result)
                print(f"Successfully generated: {result['local']}")
            else:
                print(f"Failed to generate newsletter for {lang_name}")
            
            sys.stdout.flush()
        
        print(f"\n=== GENERATION COMPLETE ===")
        print(f"Local files generated: {local_files}")
        print(f"Total files: {len(local_files)}")
        sys.stdout.flush()
        
        return jsonify({
            'success': True,
            'local_files': local_files,
            'message': f'Successfully generated {len(local_files)} local newsletter files',
            'debug_info': {
                'user_images_collected': len(user_images) if user_images else 0,
                'languages_processed': len(local_files),
                'country_code': country_code,
                'country': country
            }
        })
        
    except Exception as e:
        print(f"\n=== EXCEPTION IN API CALL ===")
        print(f"Error in build_newsletter_api: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"=== END EXCEPTION ===")
        sys.stdout.flush()
        return jsonify({'error': f'Newsletter generation failed: {str(e)}'}), 500

# Old generate_newsletter_api function removed - now using build_newsletter_api with new JSON structure

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
    
    # Only open browser in the main process, not the reloader process
    # This prevents multiple browser tabs from opening in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server
    app.run(host='localhost', port=5000, debug=True)

if __name__ == '__main__':
    main()
