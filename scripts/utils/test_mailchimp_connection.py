#!/usr/bin/env python3
"""
Simple test script to verify Mailchimp API connectivity.
This makes a basic GET request to test if the API key and connection work.
"""

import os
import requests
from dotenv import load_dotenv

def test_mailchimp_connection():
    load_dotenv()
    api_key = os.getenv('MAILCHIMP_API_KEY')
    server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')
    
    if not api_key or not server_prefix:
        print("ERROR: Missing MAILCHIMP_API_KEY or MAILCHIMP_SERVER_PREFIX in .env file")
        return False
    
    # Test basic API connectivity with a simple GET request
    url = f"https://{server_prefix}.api.mailchimp.com/3.0/"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"Testing connection to: {url}")
    print("Making basic API test call...")
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Basic Mailchimp API connection works!")
            resp_data = response.json()
            print(f"Account name: {resp_data.get('account_name', 'Unknown')}")
            return True
        else:
            print(f"FAILED: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: Connection error: {e}")
        return False

if __name__ == "__main__":
    test_mailchimp_connection()
