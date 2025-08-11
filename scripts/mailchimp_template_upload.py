import os
import requests
import logging
from dotenv import load_dotenv
from typing import Dict, Any

# Configure logging for better visibility and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MailchimpUploadError(Exception):
    """
    Custom exception for errors during the Mailchimp template upload process.
    This provides a specific error type for callers to handle.
    """
    pass

def upload_template_to_mailchimp(html_content: str, template_name: str) -> Dict[str, Any]:
    """
    Uploads the given HTML content as a new template to Mailchimp.

    This function sends a POST request to the Mailchimp API's templates endpoint
    with the provided HTML content and a template name.

    Args:
        html_content: A string containing the full HTML content of the template.
        template_name: The desired name for the new template in Mailchimp.

    Returns:
        A dictionary representing the JSON response from the Mailchimp API,
        which includes details about the newly created template.

    Raises:
        MailchimpUploadError: If there are issues with environment variables,
                              the API request fails, or the response is invalid.
    """
    # Load environment variables. In a larger application, this would ideally be
    # done once at the application's entry point.
    load_dotenv()
    
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')  # e.g., 'us21'

    if not all([api_key, server_prefix]):
        error_msg = "MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX not set in .env file."
        logging.error(error_msg)
        raise MailchimpUploadError(error_msg)

    # Construct the API endpoint URL
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/templates"
    
    # Prepare the request headers
    headers = {
        "Authorization": f"apikey {api_key}",
        "Content-Type": "application/json"
    }
    
    # Create the JSON payload for the API request
    data = {
        "name": template_name,
        "html": html_content
    }
    
    logging.info(f"Attempting to upload template: '{template_name}'")

    # Make the POST request to the Mailchimp API.
    # We use a try...except block to handle potential network errors and bad responses.
    # `verify=False` is generally not recommended in production; it disables SSL
    # certificate verification. Consider removing this for security.
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30, verify=True)
        response.raise_for_status()  # This will raise an HTTPError for 4xx/5xx responses
    except requests.exceptions.RequestException as e:
        error_msg = f"Request to Mailchimp API failed: {e}"
        
        # Attempt to get more detail from the response if it exists
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_json = e.response.json()
                logging.error(f'Full Mailchimp error response: {error_json}')
                error_detail = error_json.get('detail', e.response.text)
                if 'errors' in error_json:
                    logging.error(f"Field-specific errors: {error_json['errors']}")
                error_msg = f"Mailchimp API error ({e.response.status_code}): {error_detail}"
            except Exception:
                error_msg = f"Mailchimp API error ({e.response.status_code}): {e.response.text}"
        
        logging.error(error_msg)
        raise MailchimpUploadError(error_msg) from e

    # Process the successful response
    try:
        response_json = response.json()
        template_id = response_json.get('id')
        logging.info(f"Template '{template_name}' uploaded successfully with ID: {template_id}")
        return response_json
    except requests.exceptions.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON response from Mailchimp: {response.text}"
        logging.error(error_msg)
        raise MailchimpUploadError(error_msg) from e


if __name__ == '__main__':
    # Example usage:
    dummy_html = """
    <html>
    <body>
        <h1>Hello from a test template!</h1>
        <p>This is a paragraph of content.</p>
    </body>
    </html>
    """
    template_name = "My Test Template"
    
    try:
        print(f"Attempting to upload template '{template_name}'...")
        template_info = upload_template_to_mailchimp(dummy_html, template_name)
        print("Template uploaded successfully!")
        print("Returned information:", template_info)
    except MailchimpUploadError as e:
        print(f"Error during template upload: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        