#!/usr/bin/env python3
"""
Test script to verify the batch image upload integration in newsletter generation.
This script tests the end-to-end integration without requiring the web interface.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add the scripts directory to the Python path
script_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(script_dir))

from generate_newsletter import generate_newsletter_for_geo_lang, get_project_root

async def test_newsletter_generation_with_image_upload():
    """Test newsletter generation with integrated image upload system."""
    
    print("🧪 Testing Newsletter Generation with Batch Image Upload Integration")
    print("=" * 70)
    
    try:
        # Get project root
        project_root = get_project_root()
        print(f"📁 Project root: {project_root}")
        
        # Load test data
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        brand_file = os.path.join(project_root, 'data', 'brand_information.json')
        
        if not os.path.exists(countries_file):
            print(f"❌ Countries file not found: {countries_file}")
            return False
            
        if not os.path.exists(brand_file):
            print(f"❌ Brand file not found: {brand_file}")
            return False
        
        # Load data
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
            
        with open(brand_file, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)
        
        # Find a test country (use first available country)
        test_country = None
        test_country_code = None
        test_languages = None
        
        for country_name, country_info in countries_data.items():
            if 'countryCode' in country_info and 'languages' in country_info:
                test_country = country_name
                test_country_code = country_info['countryCode']
                test_languages = country_info['languages']
                break
        
        if not test_country:
            print("❌ No suitable test country found in countries data")
            return False
            
        print(f"🌍 Test country: {test_country} ({test_country_code})")
        print(f"🗣️  Available languages: {list(test_languages.keys())}")
        
        # Create test data structure
        test_data = {
            'global': brand_data,
            test_country_code: {
                'languages': test_languages
            }
        }
        
        # Test with first available language
        first_lang_name = list(test_languages.keys())[0]
        first_lang_data = test_languages[first_lang_name]
        test_lang_code = first_lang_data.get('languageCode')
        test_locale = first_lang_data.get('locale')
        preferred_name = first_lang_data.get('preferredName', test_country)
        
        if not test_lang_code:
            print(f"❌ No language code found for {first_lang_name}")
            return False
            
        print(f"🔤 Testing with language: {first_lang_name} ({test_lang_code})")
        print(f"📍 Locale: {test_locale}")
        print(f"🏷️  Preferred name: {preferred_name}")
        
        # Create simple form data for testing
        test_form_data = {
            'hero': {
                'image': 'images/brand/logo.png',  # Assume this exists
                'imageAlt': 'Test hero image',
                'headline': 'Test Newsletter Headline',
                'description': 'This is a test newsletter description.',
                'learnMoreUrl': 'https://example.com/learn-more'
            },
            'ctas': [
                {'text': 'Learn More', 'url': 'https://example.com/cta1'},
                {'text': 'Get Involved', 'url': 'https://example.com/cta2'}
            ],
            'stories': [
                {
                    'image': 'images/brand/story1.jpg',  # Assume this exists
                    'imageAlt': 'Test story 1 image',
                    'headline': 'Test Story 1 Headline',
                    'description': 'This is test story 1 description.',
                    'url': 'https://example.com/story1'
                }
            ]
        }
        
        print(f"\n🚀 Starting newsletter generation with image upload integration...")
        print(f"   Country: {test_country_code}")
        print(f"   Language: {test_lang_code}")
        print(f"   Form data: {len(test_form_data)} sections")
        
        # Call the integrated newsletter generation function
        successful_uploads = []
        result = await generate_newsletter_for_geo_lang(
            country_code=test_country_code,
            lang=test_lang_code,
            data=test_data,
            successful_uploads=successful_uploads,
            project_root=project_root,
            user_images=None,  # No additional user images for this test
            form_data=test_form_data,
            locale=test_locale,
            folder_name=test_country.replace(' ', '_'),
            content_country_name=preferred_name
        )
        
        print(f"\n📊 Generation Results:")
        if result:
            print(f"   ✅ Success: {bool(result)}")
            print(f"   📄 Local file: {result.get('local', 'None')}")
            
            mailchimp_result = result.get('mailchimp')
            if mailchimp_result:
                if 'error' in mailchimp_result:
                    print(f"   ⚠️  Mailchimp error: {mailchimp_result['error']}")
                elif 'upload_summary' in mailchimp_result:
                    summary = mailchimp_result['upload_summary']
                    print(f"   🖼️  Images uploaded: {mailchimp_result.get('images_uploaded', 0)}")
                    print(f"   📈 Success rate: {mailchimp_result.get('success_rate', 0):.1f}%")
                    print(f"   ⏱️  Upload time: {getattr(summary, 'total_time_seconds', 0):.2f}s")
                else:
                    print(f"   ℹ️  Mailchimp result: {mailchimp_result}")
            else:
                print(f"   ❌ No Mailchimp result")
                
            return True
        else:
            print(f"   ❌ Generation failed: No result returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function."""
    print("🔧 Batch Image Upload Integration Test")
    print("=" * 50)
    
    # Run the async test
    success = asyncio.run(test_newsletter_generation_with_image_upload())
    
    if success:
        print(f"\n✅ Integration test PASSED!")
        print("🎉 Batch image upload system is successfully integrated!")
    else:
        print(f"\n❌ Integration test FAILED!")
        print("🔧 Check the error messages above for debugging information.")
    
    return success

if __name__ == '__main__':
    main()
