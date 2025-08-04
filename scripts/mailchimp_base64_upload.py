#!/usr/bin/env python3
"""
Alternative Mailchimp image upload using base64 encoding instead of multipart form data.
This bypasses potential issues with multipart uploads being corrupted by security software.
"""

import os
import base64
import requests
from dotenv import load_dotenv

class MailchimpImageUploadError(Exception):
    pass

def upload_image_to_mailchimp_base64(image_path):
    """
    Upload an image to Mailchimp Content Studio using base64 encoding.
    
    Args:
        image_path (str): Absolute path to the image file
        
    Returns:
        str: The full_size_url of the uploaded image
        
    Raises:
        MailchimpImageUploadError: If upload fails
    """
    load_dotenv()
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')
    
    if not api_key or not server_prefix:
        raise MailchimpImageUploadError("Missing MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX in .env file")
    
    if not os.path.exists(image_path):
        raise MailchimpImageUploadError(f"Image file not found: {image_path}")
    
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/file-manager/files"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    filename = os.path.basename(image_path)
    file_size = os.path.getsize(image_path)
    print(f"Uploading image: {image_path} (size: {file_size} bytes)")
    
    # Read and encode the image as base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
    
    # Try JSON payload with base64 data
    data = {
        "name": filename,
        "file_data": base64_data,
        "type": "image"
    }
    
    print("Uploading with base64 encoding...")
    response = requests.post(url, headers=headers, json=data, verify=False)
    
    if response.status_code in (200, 201):
        resp_json = response.json()
        print(f"SUCCESS: Image uploaded to Mailchimp!")
        return resp_json['full_size_url']
    
    # If that fails, log the error details
    try:
        error_json = response.json()
        print(f"Full Mailchimp error response: {error_json}")
        if 'errors' in error_json:
            print(f"Field-specific errors: {error_json['errors']}")
    except:
        print(f"Raw error response: {response.text}")
    
    raise MailchimpImageUploadError(f"Mailchimp API error ({response.status_code}): {response.text}")

if __name__ == "__main__":
    # Test with the hero image
    test_image = os.path.join(os.path.dirname(__file__), '..', 'images', 'us', 'hero.jpg')
    test_image = os.path.abspath(test_image)
    
    try:
        url = upload_image_to_mailchimp_base64(test_image)
        print(f"Image URL: {url}")
    except Exception as e:
        print(f"Upload failed: {e}")
