#!/usr/bin/env python3
"""
Unit tests for Mailchimp credential management system.
Tests API endpoints, validation logic, and environment file handling.
"""

import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import patch, mock_open, MagicMock
import sys

# Add the scripts directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the Flask app and functions
from generate_newsletter import app, get_project_root

class TestCredentialManagement(unittest.TestCase):
    """Test suite for credential management functionality."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Clear environment variables
        for key in ['MAILCHIMP_API_KEY', 'MAILCHIMP_SERVER_PREFIX']:
            if key in os.environ:
                del os.environ[key]

class TestCheckCredentialsEndpoint(TestCredentialManagement):
    """Test the /api/check-credentials endpoint."""
    
    @patch('generate_newsletter.get_project_root')
    @patch('generate_newsletter.load_dotenv')
    @patch('os.getenv')
    def test_no_env_file_no_credentials(self, mock_getenv, mock_load_dotenv, mock_get_project_root):
        """Test when .env file doesn't exist and no environment variables are set."""
        # Setup mocks
        mock_get_project_root.return_value = self.test_dir
        mock_getenv.side_effect = lambda key, default=None: None
        
        # Make request
        response = self.client.get('/api/check-credentials')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['hasCredentials'])
        self.assertFalse(data['debug']['envFileExists'])
        self.assertFalse(data['debug']['hasApiKey'])
        self.assertFalse(data['debug']['hasServerPrefix'])
    
    @patch('generate_newsletter.get_project_root')
    @patch('generate_newsletter.load_dotenv')
    @patch('os.getenv')
    def test_env_file_exists_with_valid_credentials(self, mock_getenv, mock_load_dotenv, mock_get_project_root):
        """Test when .env file exists with valid credentials."""
        # Create .env file
        env_file_path = os.path.join(self.test_dir, '.env')
        with open(env_file_path, 'w') as f:
            f.write('MAILCHIMP_API_KEY=1234567890abcdef1234567890abcdef-us21\n')
            f.write('MAILCHIMP_SERVER_PREFIX=us21\n')
        
        # Setup mocks
        mock_get_project_root.return_value = self.test_dir
        mock_getenv.side_effect = lambda key, default=None: {
            'MAILCHIMP_API_KEY': '1234567890abcdef1234567890abcdef-us21',
            'MAILCHIMP_SERVER_PREFIX': 'us21'
        }.get(key, default)
        
        # Make request
        response = self.client.get('/api/check-credentials')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['hasCredentials'])
        self.assertTrue(data['debug']['envFileExists'])
        self.assertTrue(data['debug']['hasApiKey'])
        self.assertTrue(data['debug']['hasServerPrefix'])
    
    @patch('generate_newsletter.get_project_root')
    @patch('generate_newsletter.load_dotenv')
    @patch('os.getenv')
    def test_env_file_exists_with_empty_credentials(self, mock_getenv, mock_load_dotenv, mock_get_project_root):
        """Test when .env file exists but credentials are empty."""
        # Create .env file with empty values
        env_file_path = os.path.join(self.test_dir, '.env')
        with open(env_file_path, 'w') as f:
            f.write('MAILCHIMP_API_KEY=\n')
            f.write('MAILCHIMP_SERVER_PREFIX=\n')
        
        # Setup mocks
        mock_get_project_root.return_value = self.test_dir
        mock_getenv.side_effect = lambda key, default=None: {
            'MAILCHIMP_API_KEY': '',
            'MAILCHIMP_SERVER_PREFIX': ''
        }.get(key, default)
        
        # Make request
        response = self.client.get('/api/check-credentials')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['hasCredentials'])
        self.assertTrue(data['debug']['envFileExists'])
        self.assertFalse(data['debug']['hasApiKey'])
        self.assertFalse(data['debug']['hasServerPrefix'])

class TestSaveCredentialsEndpoint(TestCredentialManagement):
    """Test the /api/save-credentials endpoint."""
    
    @patch('generate_newsletter.get_project_root')
    def test_save_valid_credentials(self, mock_get_project_root):
        """Test saving valid credentials."""
        mock_get_project_root.return_value = self.test_dir
        
        # Valid credentials
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us21'
        }
        
        # Make request
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('saved successfully', data['message'])
        
        # Check .env file was created
        env_file_path = os.path.join(self.test_dir, '.env')
        self.assertTrue(os.path.exists(env_file_path))
        
        # Check .env file contents
        with open(env_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('MAILCHIMP_API_KEY=1234567890abcdef1234567890abcdef-us21', content)
            self.assertIn('MAILCHIMP_SERVER_PREFIX=us21', content)
    
    def test_save_invalid_api_key_format(self):
        """Test saving credentials with invalid API key format."""
        credentials = {
            'apiKey': 'invalid-key',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Credential validation failed')
        self.assertIn('details', data)
        # Check that API key validation error is in details
        details_text = ' '.join(data['details'])
        self.assertIn('Invalid API key format', details_text)
    
    def test_save_invalid_server_prefix_format(self):
        """Test saving credentials with invalid server prefix format."""
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'INVALID'
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Credential validation failed')
        self.assertIn('details', data)
        # Check that server prefix validation error is in details
        details_text = ' '.join(data['details'])
        self.assertIn('Invalid server prefix format', details_text)
    
    def test_save_mismatched_credentials(self):
        """Test saving credentials where API key doesn't match server prefix."""
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us1'
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Credential validation failed')
        self.assertIn('details', data)
        # Check that mismatch validation error is in details
        details_text = ' '.join(data['details'])
        self.assertIn('API key server suffix', details_text)
    
    def test_save_empty_credentials(self):
        """Test saving empty credentials."""
        credentials = {
            'apiKey': '',
            'serverPrefix': ''
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn('API key and server prefix are required', data['error'])
    
    def test_save_missing_fields(self):
        """Test saving credentials with missing fields."""
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21'
            # Missing serverPrefix
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn('API key and server prefix are required', data['error'])

class TestMailchimpConnectionEndpoint(TestCredentialManagement):
    """Test the /api/test-mailchimp-connection endpoint."""
    
    @patch('requests.get')
    def test_successful_connection(self, mock_get):
        """Test successful Mailchimp connection."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'account_id': 'test123',
            'account_name': 'Test Account',
            'email': 'test@example.com'
        }
        mock_get.return_value = mock_response
        
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/test-mailchimp-connection',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('account_id', data['accountInfo'])
        self.assertEqual(data['accountInfo']['account_id'], 'test123')
    
    @patch('requests.get')
    def test_invalid_credentials_401(self, mock_get):
        """Test connection with invalid credentials (401 Unauthorized)."""
        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response
        
        credentials = {
            'apiKey': 'invalid-key-format',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/test-mailchimp-connection',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['errorType'], 'authentication')
        self.assertIn('suggestions', data)
    
    @patch('requests.get')
    def test_network_error(self, mock_get):
        """Test connection with network error."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/test-mailchimp-connection',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertFalse(data['success'])
        self.assertEqual(data['errorType'], 'network')
        self.assertIn('suggestions', data)

class TestCredentialValidation(TestCredentialManagement):
    """Test credential validation logic."""
    
    def test_valid_api_key_formats(self):
        """Test various valid API key formats."""
        valid_keys = [
            '1234567890abcdef1234567890abcdef-us21',
            'abcdef1234567890abcdef1234567890ab-us1',
            '0123456789abcdef0123456789abcdef-eu3',
            'fedcba0987654321fedcba0987654321-au1'
        ]
        
        for api_key in valid_keys:
            server_prefix = api_key.split('-')[-1]
            credentials = {
                'apiKey': api_key,
                'serverPrefix': server_prefix
            }
            
            response = self.client.post('/api/save-credentials',
                                      data=json.dumps(credentials),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200,
                           f"Valid API key should be accepted: {api_key}")
    
    def test_invalid_api_key_formats(self):
        """Test various invalid API key formats."""
        invalid_keys = [
            'too-short-us21',
            '1234567890abcdef1234567890abcdef',  # Missing server suffix
            '1234567890abcdef1234567890abcdef-',  # Empty server suffix
            'GGGG567890abcdef1234567890abcdef-us21',  # Invalid hex chars
            '1234567890abcdef1234567890abcde-us21',  # Too short hex part
            '1234567890abcdef1234567890abcdef1-us21'  # Too long hex part
        ]
        
        for api_key in invalid_keys:
            credentials = {
                'apiKey': api_key,
                'serverPrefix': 'us21'
            }
            
            response = self.client.post('/api/save-credentials',
                                      data=json.dumps(credentials),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 400,
                           f"Invalid API key should be rejected: {api_key}")
    
    def test_valid_server_prefix_formats(self):
        """Test various valid server prefix formats."""
        valid_prefixes = ['us1', 'us21', 'eu3', 'au1', 'ca1']
        
        for prefix in valid_prefixes:
            credentials = {
                'apiKey': f'1234567890abcdef1234567890abcdef-{prefix}',
                'serverPrefix': prefix
            }
            
            response = self.client.post('/api/save-credentials',
                                      data=json.dumps(credentials),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 200,
                           f"Valid server prefix should be accepted: {prefix}")
    
    def test_invalid_server_prefix_formats(self):
        """Test various invalid server prefix formats."""
        invalid_prefixes = [
            'US21',  # Uppercase
            'us',    # Missing numbers
            '21',    # Missing letters
            'usa21', # Too many letters
            'u21',   # Too few letters
            'us211', # Too many numbers
            ''       # Empty
        ]
        
        for prefix in invalid_prefixes:
            credentials = {
                'apiKey': '1234567890abcdef1234567890abcdef-us21',
                'serverPrefix': prefix
            }
            
            response = self.client.post('/api/save-credentials',
                                      data=json.dumps(credentials),
                                      content_type='application/json')
            
            self.assertEqual(response.status_code, 400,
                           f"Invalid server prefix should be rejected: {prefix}")

class TestEnvironmentFileHandling(TestCredentialManagement):
    """Test .env file creation and handling."""
    
    @patch('generate_newsletter.get_project_root')
    def test_env_file_creation_utf8(self, mock_get_project_root):
        """Test that .env file is created with UTF-8 encoding."""
        mock_get_project_root.return_value = self.test_dir
        
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        
        # Check file was created
        env_file_path = os.path.join(self.test_dir, '.env')
        self.assertTrue(os.path.exists(env_file_path))
        
        # Check UTF-8 encoding by reading with explicit encoding
        with open(env_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('MAILCHIMP_API_KEY=', content)
            self.assertIn('MAILCHIMP_SERVER_PREFIX=', content)
    
    @patch('generate_newsletter.get_project_root')
    def test_env_file_overwrite(self, mock_get_project_root):
        """Test that existing .env file is overwritten correctly."""
        mock_get_project_root.return_value = self.test_dir
        
        # Create existing .env file
        env_file_path = os.path.join(self.test_dir, '.env')
        with open(env_file_path, 'w') as f:
            f.write('OLD_KEY=old_value\n')
        
        credentials = {
            'apiKey': '1234567890abcdef1234567890abcdef-us21',
            'serverPrefix': 'us21'
        }
        
        response = self.client.post('/api/save-credentials',
                                  data=json.dumps(credentials),
                                  content_type='application/json')
        
        # Check new content
        with open(env_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('MAILCHIMP_API_KEY=', content)
            self.assertIn('MAILCHIMP_SERVER_PREFIX=', content)
            self.assertNotIn('OLD_KEY=', content)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestCheckCredentialsEndpoint,
        TestSaveCredentialsEndpoint,
        TestMailchimpConnectionEndpoint,
        TestCredentialValidation,
        TestEnvironmentFileHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Results Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)
