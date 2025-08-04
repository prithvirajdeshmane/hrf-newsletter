import os
import json
import argparse
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import copy
import re

# Assuming mailchimp_template_upload, mailchimp_image_upload, and image_utils are in the same directory
from mailchimp_template_upload import upload_template_to_mailchimp, MailchimpUploadError
from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError
from image_utils import compress_image_if_needed

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
    """Finds all image files in images/global and images/{geo} folders that need to be uploaded."""
    image_files = []
    
    # Find all images in global folder
    global_images_dir = os.path.join(project_root, 'images', 'global')
    if os.path.exists(global_images_dir):
        for filename in os.listdir(global_images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                relative_path = f"images/global/{filename}"
                full_path = os.path.join(global_images_dir, filename)
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
    
    global_folder = os.path.join(project_root, 'images', 'global')
    if not os.path.exists(global_folder):
        missing_folders.append('images/global')
    
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
        print(f"Found {len(images_to_upload)} images to upload from global and {geo} folders")
        
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
                f"./{relative_path}",  # ./images/global/HRF-Logo.png
                f"/{relative_path}",   # /images/global/HRF-Logo.png  
                relative_path,         # images/global/HRF-Logo.png
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

def main():
    parser = argparse.ArgumentParser(description='Generate and upload newsletters for a specific geo.')
    parser.add_argument('geo', help="The geo code (e.g., 'ca', 'us').")
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'data', 'newsletter_data.json')

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {data_path}")
        sys.exit(1)

    geo_input = args.geo
    if geo_input not in data:
        print(f"\nError: Geo '{geo_input}' not found in data file.")
        sys.exit(1)

    geo_block = data[geo_input]
    
    # Determine which languages to generate for this geo
    if 'translations' in geo_block and isinstance(geo_block['translations'], dict):
        languages_to_generate = list(geo_block['translations'].keys())
    else:
        # If no translations block, assume it's a single-language geo (e.g., 'en')
        languages_to_generate = ['en']

    successful_uploads = []
    print(f"--- Starting newsletter generation for geo: {geo_input} ---")
    for lang in languages_to_generate:
        generate_newsletter_for_geo_lang(geo_input, lang, data, successful_uploads, project_root)

    if successful_uploads:
        print("\n--- Upload Summary ---")
        for name in successful_uploads:
            print(f"- {name}")
        print("\nAll newsletters were generated and uploaded successfully.")
    else:
        print("\nNo newsletters were uploaded.")

if __name__ == '__main__':
    main()
