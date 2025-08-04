import os
import requests
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder

class MailchimpImageUploadError(Exception):
    pass

def upload_image_to_mailchimp(image_path):
    """
    Uploads a local image file to Mailchimp Content Studio and returns the hosted URL.
    Raises MailchimpImageUploadError on failure.
    """
    load_dotenv()
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')  # e.g. 'us21'
    if not api_key or not server_prefix:
        raise MailchimpImageUploadError("MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX not set in .env file.")

    if not os.path.isfile(image_path):
        raise MailchimpImageUploadError(f"Image file does not exist: {image_path}")
    file_size = os.path.getsize(image_path)
    print(f"Uploading image: {image_path} (size: {file_size} bytes)")
    if file_size == 0:
        raise MailchimpImageUploadError(f"Image file is empty: {image_path}")

    url = f"https://{server_prefix}.api.mailchimp.com/3.0/file-manager/files"
    headers = {
        "Authorization": f"apikey {api_key}",
        "Accept": "application/json"
    }
    filename = os.path.basename(image_path)
    with open(image_path, 'rb') as f:
        m = MultipartEncoder(
            fields={'name': filename, 'file_data': (filename, f, 'image/jpeg')}
        )
        headers['Content-Type'] = m.content_type
        response = requests.post(url, data=m, headers=headers)
    if response.status_code not in (200, 201):
        try:
            error_json = response.json()
            print('Full Mailchimp error response:', error_json)
            error_detail = error_json.get('detail', response.text)
            if 'errors' in error_json:
                print('Field-specific errors:', error_json['errors'])
        except Exception:
            error_detail = response.text
        raise MailchimpImageUploadError(f"Mailchimp API error ({response.status_code}): {error_detail}")
    resp_json = response.json()
    # Mailchimp returns the hosted URL in resp_json['full_size_url']
    return resp_json['full_size_url']
