import os
import requests
from dotenv import load_dotenv

class MailchimpUploadError(Exception):
    pass

def upload_template_to_mailchimp(html_content, template_name):
    """
    Uploads the given HTML content as a template to Mailchimp.
    Raises MailchimpUploadError on failure.
    """
    load_dotenv()
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')  # e.g. 'us21'
    if not api_key or not server_prefix:
        raise MailchimpUploadError("MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX not set in .env file.")

    url = f"https://{server_prefix}.api.mailchimp.com/3.0/templates"
    headers = {
        "Authorization": f"apikey {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "name": template_name,
        "html": html_content
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in (200, 201):
        try:
            error_detail = response.json().get('detail', response.text)
        except Exception:
            error_detail = response.text
        raise MailchimpUploadError(f"Mailchimp API error ({response.status_code}): {error_detail}")
    return response.json()
