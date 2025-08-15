"""
Test script for Google Translate API integration.

This script tests the translation service functionality to ensure
it's working correctly before running the full newsletter generation.
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from scripts.translation_service import NewsletterTranslationService

@pytest.fixture
def translation_service():
    """Fixture to provide a translation service instance."""
    return NewsletterTranslationService()

@pytest.fixture
def sample_newsletter_content():
    """Fixture providing sample newsletter content for testing."""
    return {
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

@pytest.fixture
def sample_country_data():
    """Fixture providing sample country data for testing."""
    return {
        'languages': {
            'fr': {
                'preferredName': 'Suisse'
            }
        }
    }

def test_translation_service_availability(translation_service):
    """Test that the translation service is available and properly configured."""
    assert translation_service.is_available(), "Translation service should be available"

def test_basic_text_translation(translation_service):
    """Test basic text translation functionality."""
    if not translation_service.is_available():
        pytest.skip("Translation service not available")
    
    test_text = "Human rights are fundamental to all people."
    
    for target_lang in ['fr', 'de', 'es']:
        translated = translation_service.translate_text(test_text, target_lang)
        assert translated != test_text, f"Translation to {target_lang} should differ from original"
        assert len(translated) > 0, f"Translation to {target_lang} should not be empty"

def test_newsletter_content_translation(translation_service, sample_newsletter_content, sample_country_data):
    """Test newsletter content translation functionality."""
    if not translation_service.is_available():
        pytest.skip("Translation service not available")
    
    translated_content = translation_service.translate_newsletter_content(
        sample_newsletter_content, 'fr', sample_country_data
    )
    
    # Verify key fields are translated
    assert 'hero' in translated_content
    assert 'headline' in translated_content['hero']
    assert len(translated_content['hero']['headline']) > 0
    
    assert 'stories' in translated_content
    assert len(translated_content['stories']) > 0
    assert 'headline' in translated_content['stories'][0]
    
    assert 'static_translations' in translated_content
    assert 'footer_copyright' in translated_content['static_translations']

def test_static_text_translations(translation_service):
    """Test static text translations functionality."""
    if not translation_service.is_available():
        pytest.skip("Translation service not available")
    
    static_translations = translation_service.get_static_text_translations('de')
    
    assert 'learn_more' in static_translations
    assert 'read_story' in static_translations
    assert 'footer_copyright' in static_translations
    
    for key, value in static_translations.items():
        assert len(value) > 0, f"Static translation for {key} should not be empty"

def test_translation_caching(translation_service):
    """Test translation caching functionality."""
    if not translation_service.is_available():
        pytest.skip("Translation service not available")
    
    test_text = "This is a test for caching."
    
    # First translation (should hit API)
    result1 = translation_service.translate_text(test_text, 'fr')
    
    # Second translation (should use cache)
    result2 = translation_service.translate_text(test_text, 'fr')
    
    assert result1 == result2, "Cached translation should match original translation"

def test_environment_configuration():
    """Test that required environment variables are properly configured."""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    assert credentials_path is not None, "GOOGLE_APPLICATION_CREDENTIALS should be set"
    assert os.path.exists(credentials_path), f"Credentials file should exist at {credentials_path}"
