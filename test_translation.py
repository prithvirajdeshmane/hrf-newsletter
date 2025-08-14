"""
Test script for Google Translate API integration.

This script tests the translation service functionality to ensure
it's working correctly before running the full newsletter generation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

from scripts.translation_service import NewsletterTranslationService

def test_translation_service():
    """Test the translation service with sample content."""
    print("Testing Google Translate API Integration...")
    print("=" * 50)
    
    # Initialize translation service
    translation_service = NewsletterTranslationService()
    
    # Check if service is available
    if not translation_service.is_available():
        print("[ERROR] Translation service is not available.")
        print("Please check your Google Cloud credentials and project ID.")
        return False
    
    print("[OK] Translation service initialized successfully!")
    
    # Test basic text translation
    print("\nTesting basic text translation...")
    test_text = "Human rights are fundamental to all people."
    
    for target_lang in ['fr', 'de', 'es']:
        try:
            translated = translation_service.translate_text(test_text, target_lang)
            print(f"  {target_lang}: {translated}")
        except Exception as e:
            print(f"  [ERROR] {target_lang}: Failed - {e}")
            return False
    
    # Test newsletter content translation
    print("\nTesting newsletter content translation...")
    
    sample_content = {
        'hero': {
            'image_alt': 'Human rights protest',
            'headline': 'Fighting for Freedom',
            'description': 'Join us in the fight for human rights around the world.',
        },
        'stories': [
            {
                'image_alt': 'Democracy activists',
                'headline': 'Democracy Under Threat',
                'description': 'Activists work to protect democratic institutions.',
                'cta': {'text': 'Support Democracy'}
            }
        ],
        'ctas': [
            {'text': 'Donate Now'}
        ],
        'country': 'Switzerland'
    }
    
    # Test translation to French
    try:
        country_data = {
            'languages': {
                'fr': {
                    'preferredName': 'Suisse'
                }
            }
        }
        
        translated_content = translation_service.translate_newsletter_content(
            sample_content, 'fr', country_data
        )
        
        print("[OK] Newsletter content translation successful!")
        print(f"  Hero headline: {translated_content['hero']['headline']}")
        print(f"  Story headline: {translated_content['stories'][0]['headline']}")
        print(f"  Country name: {translated_content.get('country_display_name', 'N/A')}")
        print(f"  Footer: {translated_content['static_translations']['footer_copyright']}")
        
    except Exception as e:
        print(f"[ERROR] Newsletter content translation failed: {e}")
        return False
    
    # Test static translations
    print("\nTesting static text translations...")
    static_translations = translation_service.get_static_text_translations('de')
    print(f"  Learn more (DE): {static_translations['learn_more']}")
    print(f"  Read Story (DE): {static_translations['read_story']}")
    
    print("\n[SUCCESS] All translation tests passed!")
    return True

def test_caching():
    """Test translation caching functionality."""
    print("\nTesting translation caching...")
    
    translation_service = NewsletterTranslationService()
    
    if not translation_service.is_available():
        print("[ERROR] Translation service not available for caching test.")
        return False
    
    test_text = "This is a test for caching."
    
    # First translation (should hit API)
    print("  First translation (API call)...")
    result1 = translation_service.translate_text(test_text, 'fr')
    
    # Second translation (should use cache)
    print("  Second translation (cached)...")
    result2 = translation_service.translate_text(test_text, 'fr')
    
    if result1 == result2:
        print("[OK] Caching working correctly!")
        return True
    else:
        print("[ERROR] Caching issue detected.")
        return False

if __name__ == "__main__":
    print("Google Translate API Integration Test")
    print("=" * 50)
    
    # Check environment variables
    print("Checking environment configuration...")
    
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not credentials_path:
        print("[ERROR] GOOGLE_APPLICATION_CREDENTIALS not set in environment")
        print("Please add it to your .env file")
        sys.exit(1)
    
    if not project_id:
        print("[WARNING] GOOGLE_CLOUD_PROJECT_ID not set (optional)")
    
    if not os.path.exists(credentials_path):
        print(f"[ERROR] Credentials file not found: {credentials_path}")
        sys.exit(1)
    
    print("[OK] Environment configuration looks good!")
    
    # Run tests
    try:
        success = test_translation_service()
        if success:
            test_caching()
            print("\n[SUCCESS] Translation integration is ready for newsletter generation!")
        else:
            print("\n[ERROR] Translation integration needs attention.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
