"""
Mailchimp Newsletter Uploader Class

Handles the complete newsletter upload workflow:
1. Upload images to Mailchimp and get URLs
2. Process HTML files with URL substitution
3. Upload processed newsletters as Mailchimp templates
4. Comprehensive error handling and retry logic
"""

import os
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from scripts.env_utils import credentials_present
from scripts.mailchimp_image_uploader import MailchimpImageUploader
from dotenv import load_dotenv


class MailchimpNewsletterUploader:
    """
    Class for uploading complete newsletters to Mailchimp.
    
    Handles image upload, URL substitution, and template creation
    with comprehensive error handling and retry logic.
    """
    
    def __init__(self):
        """Initialize the uploader with Mailchimp credentials."""
        load_dotenv()
        
        if not credentials_present():
            raise ValueError("Mailchimp credentials not found. Please configure API key and server prefix.")
        
        self.api_key = os.getenv("MAILCHIMP_API_KEY")
        self.server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.base_url = f"https://{self.server_prefix}.api.mailchimp.com/3.0"
        
        # Upload configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.timeout = 30
        
        # Initialize image uploader
        self.image_uploader = MailchimpImageUploader()
        
    def upload_newsletter_session(self, session_id: str, country: str) -> Dict[str, Any]:
        """
        Main method to upload complete newsletter session.
        
        Args:
            session_id: Session ID for user-specific images
            country: Country name for newsletter files
            
        Returns:
            Dictionary with complete upload results
        """
        try:
            # Step 1: Upload images and get Mailchimp URLs
            image_results = self._upload_session_images(session_id)
            
            if not image_results['success']:
                return {
                    'success': False,
                    'message': f'Image upload failed: {image_results["message"]}',
                    'image_results': image_results,
                    'newsletter_results': []
                }
            
            # Step 2: Process and upload newsletters
            newsletter_results = self._process_and_upload_newsletters(
                session_id, country, image_results['url_mapping']
            )
            
            # Step 3: Determine overall success
            overall_success = (
                image_results['success'] and 
                len([r for r in newsletter_results if r['status'] == 'success']) > 0
            )
            
            successful_newsletters = [r for r in newsletter_results if r['status'] == 'success']
            failed_newsletters = [r for r in newsletter_results if r['status'] == 'failed']
            
            return {
                'success': overall_success,
                'message': f'Uploaded {len(successful_newsletters)}/{len(newsletter_results)} newsletters successfully',
                'image_results': image_results,
                'newsletter_results': newsletter_results,
                'successful_count': len(successful_newsletters),
                'failed_count': len(failed_newsletters)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Newsletter upload process failed: {str(e)}',
                'image_results': {'success': False, 'results': []},
                'newsletter_results': []
            }
    
    def _upload_session_images(self, session_id: str) -> Dict[str, Any]:
        """Upload session images and create URL mapping."""
        # Upload images using existing functionality
        image_results = self.image_uploader.upload_session_images(session_id)
        
        if not image_results['success']:
            return {
                'success': False,
                'message': image_results['message'],
                'results': image_results['results'],
                'url_mapping': {}
            }
        
        # Create URL mapping for HTML substitution
        url_mapping = self._create_url_mapping(image_results['results'])
        
        return {
            'success': True,
            'message': image_results['message'],
            'results': image_results['results'],
            'url_mapping': url_mapping
        }
    
    def _create_url_mapping(self, image_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create mapping from local HTML paths to Mailchimp URLs."""
        url_mapping = {}
        
        for image_result in image_results:
            if image_result['status'] == 'success':
                image_name = image_result['name']
                mailchimp_url = image_result['url']
                
                # Map based on common naming patterns
                if 'HRF-Logo' in image_name or 'logo' in image_name.lower():
                    # Brand logo mapping
                    url_mapping['/static/images/brand/HRF-Logo.png'] = mailchimp_url
                elif 'hero' in image_name.lower():
                    # Hero image mapping with regex pattern for session ID
                    url_mapping['../../static/images/user-images/[^/]+/img-hero.jpg'] = mailchimp_url
                elif 'story1' in image_name.lower() or 'story-1' in image_name.lower():
                    # Story 1 image mapping with regex pattern for session ID
                    url_mapping['../../static/images/user-images/[^/]+/img-story1.jpg'] = mailchimp_url
                elif 'story2' in image_name.lower() or 'story-2' in image_name.lower():
                    # Story 2 image mapping with regex pattern for session ID
                    url_mapping['../../static/images/user-images/[^/]+/img-story2.jpg'] = mailchimp_url
        
        return url_mapping
    
    def _process_and_upload_newsletters(self, session_id: str, country: str, url_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Process HTML files and upload as Mailchimp templates."""
        # Find newsletter files
        newsletter_files = self._find_newsletter_files(country)
        
        if not newsletter_files:
            return [{
                'status': 'failed',
                'filename': 'N/A',
                'error': f'No newsletter files found for country: {country}',
                'template_id': None
            }]
        
        # Create mailchimp_versions folder
        mailchimp_folder = self._create_mailchimp_versions_folder(country)
        
        results = []
        
        for newsletter_file in newsletter_files:
            try:
                # Process single newsletter
                result = self._process_single_newsletter(
                    newsletter_file, url_mapping, mailchimp_folder
                )
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'failed',
                    'filename': newsletter_file['filename'],
                    'error': f'Processing failed: {str(e)}',
                    'template_id': None
                })
        
        return results
    
    def _find_newsletter_files(self, country: str) -> List[Dict[str, str]]:
        """Find newsletter HTML files for the specified country."""
        newsletter_files = []
        
        # Check generated_newsletters folder with slugified country name
        from scripts.utils.country_newsletter_path import CountryNewsletterPath
        country_dir = CountryNewsletterPath(country).ensure_newsletter_dir()
        
        for html_file in country_dir.glob("*.html"):
            newsletter_files.append({
                'filename': html_file.name,
                'path': str(html_file),
                'country': country
            })
        
        return newsletter_files
    
    def _create_mailchimp_versions_folder(self, country: str) -> str:
        """Create mailchimp_versions folder for the country."""
        from scripts.utils.country_newsletter_path import CountryNewsletterPath
        mailchimp_folder = CountryNewsletterPath(country).ensure_mailchimp_dir()
        return str(mailchimp_folder)
    
    def _process_single_newsletter(self, newsletter_file: Dict[str, str], url_mapping: Dict[str, str], output_folder: str) -> Dict[str, Any]:
        """Process a single newsletter file."""
        filename = newsletter_file['filename']
        file_path = newsletter_file['path']
        
        # Read original HTML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            return {
                'status': 'failed',
                'filename': filename,
                'error': f'Failed to read file: {str(e)}',
                'template_id': None
            }
        
        # Substitute image URLs
        updated_html = self._substitute_image_urls(html_content, url_mapping)
        
        # Generate new filename
        new_filename = self._generate_template_filename(filename)
        output_path = Path(output_folder) / new_filename
        
        # Save processed file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)
        except Exception as e:
            return {
                'status': 'failed',
                'filename': filename,
                'error': f'Failed to save processed file: {str(e)}',
                'template_id': None
            }
        
        # Upload to Mailchimp
        upload_result = self._upload_template_to_mailchimp(new_filename, updated_html)
        
        return {
            'status': upload_result['status'],
            'filename': new_filename,
            'original_filename': filename,
            'error': upload_result.get('error'),
            'template_id': upload_result.get('template_id'),
            'output_path': str(output_path)
        }
    
    def _substitute_image_urls(self, html_content: str, url_mapping: Dict[str, str]) -> str:
        """Replace local image URLs with Mailchimp URLs."""
        updated_html = html_content
        
        for local_pattern, mailchimp_url in url_mapping.items():
            # Check if pattern contains regex characters
            if '[^/]+' in local_pattern:
                # This is a regex pattern - use it directly
                regex_pattern = f'src="{re.escape(local_pattern).replace(r"\[", "[").replace(r"\]", "]").replace(r"\^", "^").replace(r"\+", "+")}"'
                replacement = f'src="{mailchimp_url}"'
                updated_html = re.sub(regex_pattern, replacement, updated_html)
            else:
                # Direct string replacement for exact matches
                pattern = f'src="{re.escape(local_pattern)}"'
                replacement = f'src="{mailchimp_url}"'
                updated_html = re.sub(pattern, replacement, updated_html)
        
        return updated_html
    
    def _generate_template_filename(self, original_filename: str) -> str:
        """Generate new filename - now just reuses the same name as original."""
        # Remove any path components and return just the filename
        from pathlib import Path
        return Path(original_filename).name
    
    def _upload_template_to_mailchimp(self, template_name: str, html_content: str) -> Dict[str, Any]:
        """Upload processed newsletter as Mailchimp template."""
        template_data = {
            'name': template_name.replace('.html', ''),
            'html': html_content
        }
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/templates",
                    auth=('anystring', self.api_key),
                    json=template_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'status': 'success',
                        'template_id': result.get('id'),
                        'template_name': result.get('name'),
                        'error': None
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt == self.max_retries - 1:
                        return {
                            'status': 'failed',
                            'template_id': None,
                            'error': error_msg
                        }
                    
            except Exception as e:
                error_msg = str(e)
                if attempt == self.max_retries - 1:
                    return {
                        'status': 'failed',
                        'template_id': None,
                        'error': error_msg
                    }
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return {
            'status': 'failed',
            'template_id': None,
            'error': 'Max retries exceeded'
        }
