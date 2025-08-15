"""
Pytest configuration and shared fixtures for HRF Newsletter Generator tests.
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def app():
    """Create Flask app instance for testing."""
    from app import app
    app.config['TESTING'] = True
    return app

@pytest.fixture(scope="session")
def client(app):
    """Create Flask test client."""
    return app.test_client()

@pytest.fixture
def sample_form_data():
    """Sample form data for newsletter generation testing."""
    return {
        'country': 'Central African Republic',
        'hero': {
            'image': 'https://example.com/hero.jpg',
            'imageAlt': 'Human rights activists',
            'headline': 'Fighting for Freedom',
            'description': 'Join us in the fight for human rights around the world.',
            'url': 'https://hrf.org/freedom',
            'cta': {'text': 'Learn More', 'url': 'https://hrf.org/freedom'}
        },
        'stories': [
            {
                'image': 'https://example.com/story1.jpg',
                'imageAlt': 'Democracy protest',
                'headline': 'Democracy Under Threat',
                'description': 'Activists work to protect democratic institutions.',
                'url': 'https://hrf.org/democracy',
                'cta': {'text': 'Support Democracy', 'url': 'https://hrf.org/democracy'}
            }
        ],
        'ctas': [
            {'text': 'Donate Now', 'url': 'https://hrf.org/donate'}
        ]
    }

@pytest.fixture
def sample_country_data():
    """Sample country data for testing."""
    return {
        'name': 'Central African Republic',
        'languages': {
            'French': {
                'languageCode': 'fr',
                'locale': 'fr-CF',
                'preferredName': 'République centrafricaine',
                'scriptDirection': 'ltr'
            },
            'English': {
                'languageCode': 'en',
                'locale': 'en-CF',
                'preferredName': 'Central African Republic',
                'scriptDirection': 'ltr'
            }
        }
    }

@pytest.fixture
def mock_session_id():
    """Mock session ID for testing."""
    return "test123"

@pytest.fixture
def skip_if_no_credentials():
    """Skip test if required credentials are not available."""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    mailchimp_key = os.getenv('MAILCHIMP_API_KEY')
    
    if not credentials_path or not os.path.exists(credentials_path):
        pytest.skip("Google Cloud credentials not available")
    
    if not mailchimp_key:
        pytest.skip("Mailchimp credentials not available")
