import os
import json
import argparse
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import copy

def deep_merge(source, destination):
    """Recursively merges source dict into a copy of destination dict, intelligently merging lists of objects."""
    result = copy.deepcopy(destination)
    for key, value in source.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(value, result[key])
        elif isinstance(value, list) and key in result and isinstance(result[key], list):
            # This is the new logic to handle lists of objects (like stories or buttons)
            # It assumes the lists are the same length and merges items element-wise.
            if len(value) == len(result[key]):
                result[key] = [deep_merge(src_item, dest_item) for src_item, dest_item in zip(value, result[key])]
            else:
                # If lists are different lengths, the source list simply replaces the destination.
                result[key] = value
        else:
            result[key] = value
    return result

def get_geo_data(data, geo_code):
    """
    Resolves geo data, handling base geos by defaulting to 'en' or the first available language.
    Returns a tuple of (geo_data, resolved_geo_code).
    """
    parts = geo_code.split('-')
    base_geo = parts[0]
    lang = parts[1] if len(parts) > 1 else None

    if base_geo not in data:
        return None, None

    geo_block = data[base_geo]
    # Handle empty geo block
    if not geo_block or (isinstance(geo_block, dict) and len(geo_block) == 0):
        return 'EMPTY', base_geo
    translations = geo_block.get('translations')

    # This block handles any geo that has a 'translations' object.
    if translations:
        # If no language is specified, find a default.
        if not lang:
            if 'en' in translations:
                lang = 'en'
            # If 'en' is not found, and the translations object is not empty, pick the first one.
            elif translations:
                lang = list(translations.keys())[0]
            else:
                # This case handles an empty 'translations' object.
                return None, None

        # Now that we have a language (either specified or defaulted), check if it's valid.
        if lang in translations:
            lang_data = translations[lang]
            # The base_data should not include the translations themselves.
            base_data = {k: v for k, v in geo_block.items() if k != 'translations'}
            # The final data is the base data merged on top of the language data.
            final_data = deep_merge(base_data, lang_data)
            resolved_geo = f"{base_geo}-{lang}"
            return final_data, resolved_geo

    # This block handles simple geos that do NOT have a 'translations' object (like the old 'us' format).
    # It will only match if no language was specified.
    elif not lang:
        return geo_block, base_geo

    # If none of the above conditions were met, the geo_code is invalid.
    return None, None

def generate_newsletter_for_geo_lang(geo, lang):
    """Generates a newsletter for a specific geo and language, then uploads it to Mailchimp."""
    import sys
    from mailchimp_upload import upload_template_to_mailchimp, MailchimpUploadError
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'data', 'newsletter_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    geo_code = f"{geo}-{lang}"
    geo_data, resolved_geo = get_geo_data(data, geo_code)
    if geo_data == 'EMPTY':
        print(f"\nError: Geo '{geo}' exists in the data, but contains no content or translations.")
        print("Please provide newsletter content for this geo in the JSON file.")
        sys.exit(1)
    if not geo_data:
        print(f"\nError: Geo '{geo_code}' could not be resolved.")
        print("Please use a valid geo code with translations.")
        sys.exit(1)

    context = {**geo_data, 'global': data['global']}
    missing_images = validate_image_paths(context, project_root)
    if missing_images:
        print(f"\nError: Could not find the following image files for geo '{resolved_geo}':")
        for path in missing_images:
            print(f"  - {path}")
        print("\nPlease create the files or correct the paths in newsletter_data.json.")
        sys.exit(1)

    template_dir = os.path.join(project_root, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template('newsletter_template.html')
    html_content = template.render(context)

    base_geo = resolved_geo.split('-')[0]
    output_dir = os.path.join(project_root, 'generated_newsletters', base_geo)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f'newsletter_{resolved_geo}_{timestamp}.html'
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\nSuccessfully generated newsletter for geo '{resolved_geo}'.")
    print(f"Output saved to: {output_path}")

    # --- Compress, upload images to Mailchimp, and rewrite URLs in HTML ---
    try:
        from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError
        from image_utils import compress_image_if_needed

        image_urls = find_image_urls(context)
        local_to_mailchimp_url = {}

        for url in set(image_urls):
            clean_url = url.lstrip('./')
            image_path = os.path.join(project_root, clean_url.replace('/', os.sep))
            
            if not os.path.exists(image_path):
                print(f"Warning: Image not found at '{image_path}'. Skipping upload.")
                continue

            # Compress the image if it's too large before uploading
            compressed_image_path = compress_image_if_needed(image_path)

            mailchimp_url = upload_image_to_mailchimp(compressed_image_path)
            local_to_mailchimp_url[url] = mailchimp_url
            # Also map cleaned path for robustness
            local_to_mailchimp_url[clean_url] = mailchimp_url
        # Replace all image URLs in the HTML with Mailchimp URLs
        html_for_mailchimp = html_content
        for local_url, mailchimp_url in local_to_mailchimp_url.items():
            html_for_mailchimp = html_for_mailchimp.replace(local_url, mailchimp_url)
    except Exception as e:
        print(f"\nERROR: Unexpected error during image upload or URL replacement for geo '{resolved_geo}'.")
        print(f"Reason: {e}")
        sys.exit(1)

    # --- Upload to Mailchimp synchronously ---
    template_name = f"newsletter_{resolved_geo}_{timestamp}"
    try:
        upload_template_to_mailchimp(html_for_mailchimp, template_name)
        print(f"Successfully uploaded newsletter '{template_name}' to Mailchimp.")
    except MailchimpUploadError as e:
        print(f"\nERROR: Failed to upload newsletter '{template_name}' to Mailchimp for geo '{resolved_geo}'.")
        print(f"Reason: {e}")
        print("No further uploads will be attempted. Please resolve the issue and try again.")
        sys.exit(1)


def find_image_urls(data):
    """Recursively finds all values for the key 'image_url' in a nested dict/list."""
    urls = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'image_url' and isinstance(value, str):
                urls.append(value)
            else:
                urls.extend(find_image_urls(value))
    elif isinstance(data, list):
        for item in data:
            urls.extend(find_image_urls(item))
    return urls

def validate_image_paths(context, project_root):
    """Checks if all image_url paths in the context data exist on the filesystem."""
    missing_paths = []
    image_urls = find_image_urls(context)
    for url in image_urls:
        full_path = os.path.join(project_root, url.replace('/', os.sep))
        if not os.path.exists(full_path):
            missing_paths.append(url)
    return missing_paths

def main():
    parser = argparse.ArgumentParser(description='Generate newsletters for all translations of a geo.')
    parser.add_argument('geo', help="The geo code (e.g., 'ca', 'us').")
    args = parser.parse_args()
    geo_input = args.geo
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'data', 'newsletter_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if geo_input not in data:
        print(f"\nError: Geo '{geo_input}' could not be resolved.")
        print("Please use a valid geo code.")
        return
    geo_block = data[geo_input]
    translations = geo_block.get('translations')
    if not translations or not isinstance(translations, dict) or len(translations) == 0:
        print(f"\nError: Geo '{geo_input}' must have a non-empty 'translations' block.")
        print("Please provide at least one language translation for this geo in the JSON file.")
        return
    for lang in translations.keys():
        generate_newsletter_for_geo_lang(geo_input, lang)

if __name__ == '__main__':
    main()
