import json
import os
import pytest

from app import app

@pytest.fixture
def client():
    """
    Pytest fixture to configure and provide a Flask test client.
    Yields:
        FlaskClient: The Flask test client for API requests.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_countries_returns_json(client):
    """
    Test that /api/countries returns the correct JSON from country_languages.json.
    Checks for a known country and the presence of the 'languages' key.
    """
    resp = client.get('/api/countries')
    assert resp.status_code == 200
    data = resp.get_json()
    # Check that a known country is present
    assert "United States" in data
    assert "languages" in data["United States"]

def test_root_serves_index_html(client):
    """
    Test that / serves the index page with the correct welcome message.
    """
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Newsletter Generator' in resp.data or b'Build Newsletter' in resp.data

def test_build_newsletter_logs_country(client, capsys):
    """
    Test that /build-newsletter?country=Germany prints/logs the country name.
    Verifies the log output contains the country.
    """
    test_country = "Germany"
    resp = client.get(f'/build-newsletter?country={test_country}')
    assert resp.status_code == 200
    captured = capsys.readouterr()
    assert test_country in captured.out