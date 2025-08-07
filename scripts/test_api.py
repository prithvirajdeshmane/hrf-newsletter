#!/usr/bin/env python3
"""Test script to trigger the newsletter generation API and capture errors."""

import requests
import json

def test_newsletter_api():
    """Test the newsletter generation API endpoint."""
    
    # Sample form data that mimics what the frontend would send
    test_data = {
        "country": "Ivory Coast",
        "hero": {
            "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "imageAlt": "Test hero image",
            "headline": "Test Newsletter Headline",
            "description": "This is a test newsletter description",
            "learnMoreUrl": "https://example.com"
        },
        "ctas": [
            {
                "text": "Learn More",
                "url": "https://example.com/learn"
            }
        ],
        "stories": [
            {
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
                "imageAlt": "Test story image",
                "headline": "Test Story Headline",
                "description": "This is a test story description",
                "url": "https://example.com/story"
            }
        ]
    }
    
    url = "http://localhost:5000/api/build-newsletter"
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"Making POST request to: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("Response Content:")
        print("-" * 30)
        
        # Try to parse as JSON first
        try:
            json_response = response.json()
            print(json.dumps(json_response, indent=2))
        except:
            # If not JSON, print raw content
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    test_newsletter_api()
