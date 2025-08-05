import os
import base64
import requests
import logging
from dotenv import load_dotenv

# Set up logging for better error reporting and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MailchimpImageUploadError(Exception):
    """
    Custom exception for errors during the Mailchimp image upload process.
    """
    pass

def upload_image_to_mailchimp(image_path: str) -> str:
    """
    Uploads a local image file to Mailchimp Content Studio and returns the hosted URL.

    This function reads an image file, encodes it in base64, and sends it to the
    Mailchimp API's file manager endpoint.

    Args:
        image_path: The full path to the local image file.

    Returns:
        The URL of the uploaded image hosted on Mailchimp's servers.

    Raises:
        MailchimpImageUploadError: If there are issues with environment variables,
                                    file access, or the Mailchimp API request fails.
    """
    # Load environment variables once at the start of the script or application
    # This is a good practice to avoid repeatedly loading the file.
    # We'll keep it here for this function's self-contained nature, but for a
    # larger application, it's better to call this once globally.
    load_dotenv()
    
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')  # e.g. 'us21'

    if not all([api_key, server_prefix]):
        error_msg = "MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX not set in .env file."
        logging.error(error_msg)
        raise MailchimpImageUploadError(error_msg)

    # Validate the image file
    if not os.path.isfile(image_path):
        error_msg = f"Image file does not exist: {image_path}"
        logging.error(error_msg)
        raise MailchimpImageUploadError(error_msg)
    
    file_size = os.path.getsize(image_path)
    if file_size == 0:
        error_msg = f"Image file is empty: {image_path}"
        logging.error(error_msg)
        raise MailchimpImageUploadError(error_msg)
    
    logging.info(f"Preparing to upload image: {image_path} (size: {file_size} bytes)")

    # Construct the API endpoint URL
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/file-manager/files"
    
    # Prepare the request headers
    headers = {
        "Authorization": f"apikey {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    filename = os.path.basename(image_path)
    
    # Read and encode the image as base64
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
    except IOError as e:
        error_msg = f"Failed to read image file: {image_path}. Error: {e}"
        logging.error(error_msg)
        raise MailchimpImageUploadError(error_msg) from e

    # Create the JSON payload for the API request
    data = {
        "name": filename,
        "file_data": base64_data,
        "type": "image"
    }
    
    logging.info(f"Sending request to Mailchimp API for file: {filename}")
    
    # Make the POST request to the Mailchimp API
    # Note: `verify=False` is generally not recommended in production for security reasons.
    # It disables SSL certificate verification. It's often used in development or
    # specific scenarios with self-signed certificates. Consider removing this
    # if you are in a production environment with proper CA-signed certificates.
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60, verify=True)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        error_msg = f"Request to Mailchimp API failed: {e}"
        logging.error(error_msg)
        
        # Attempt to get more detail from the response if it exists
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_json = e.response.json()
                logging.error('Full Mailchimp error response:', error_json)
                error_detail = error_json.get('detail', e.response.text)
                if 'errors' in error_json:
                    logging.error('Field-specific errors:', error_json['errors'])
                error_msg = f"Mailchimp API error ({e.response.status_code}): {error_detail}"
            except Exception:
                error_msg = f"Mailchimp API error ({e.response.status_code}): {e.response.text}"
        
        raise MailchimpImageUploadError(error_msg) from e

    # Process the successful response
    try:
        resp_json = response.json()
        hosted_url = resp_json.get('full_size_url')
        if not hosted_url:
            error_msg = "Mailchimp API response did not contain 'full_size_url'."
            logging.error(error_msg)
            raise MailchimpImageUploadError(error_msg)
        
        logging.info(f"Image uploaded successfully. Hosted URL: {hosted_url}")
        return hosted_url
    except requests.exceptions.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON response from Mailchimp: {response.text}"
        logging.error(error_msg)
        raise MailchimpImageUploadError(error_msg) from e

if __name__ == '__main__':
    # This is a simple example of how to use the function.
    # You would replace 'path/to/your/image.jpg' with an actual file path.
    # Create a dummy file for demonstration purposes.
    dummy_image_path = "test_image.txt"
    with open(dummy_image_path, "w") as f:
        f.write("dummy content")
    
    try:
        # This will likely fail as it's not a real image and Mailchimp will reject it.
        # It's intended to show the error handling path.
        print("Attempting to upload a dummy file to demonstrate functionality...")
        hosted_url = upload_image_to_mailchimp(dummy_image_path)
        print("Success! Hosted URL:", hosted_url)
    except MailchimpImageUploadError as e:
        print(f"Error during upload: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)