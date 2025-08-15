#!/usr/bin/env python3
"""
TDD Test for Mailchimp Newsletter Upload Workflow

Tests the complete pipeline:
1. Upload images to get Mailchimp URLs (reuse existing test)
2. Create mailchimp_versions folder structure
3. Process HTML files with URL substitution
4. Apply correct naming convention
5. Upload processed newsletters to Mailchimp
"""

import os
import re
import requests
import base64
from datetime import datetime
from pathlib import Path
from scripts.mailchimp_image_uploader import MailchimpImageUploader
from dotenv import load_dotenv


class NewsletterUploadTester:
    """Test class for newsletter upload workflow."""
    
    def __init__(self):
        """Initialize with Mailchimp credentials."""
        load_dotenv()
        self.api_key = os.getenv("MAILCHIMP_API_KEY")
        self.server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.base_url = f"https://{self.server_prefix}.api.mailchimp.com/3.0"
        
    def test_complete_workflow(self):
        """Test the complete newsletter upload workflow."""
        print("=" * 60)
        print("TESTING COMPLETE NEWSLETTER UPLOAD WORKFLOW")
        print("=" * 60)
        
        # Step 1: Get Mailchimp image URLs
        print("\nStep 1: Getting Mailchimp image URLs...")
        image_url_mapping = self._get_image_urls()
        
        if not image_url_mapping:
            print("[FAILED] Failed to get image URLs. Cannot proceed.")
            return False
            
        print(f"[SUCCESS] Got {len(image_url_mapping)} image URLs")
        for local_path, mailchimp_url in image_url_mapping.items():
            print(f"  {local_path} -> {mailchimp_url[:50]}...")
        
        # Step 2: Create mailchimp_versions folder
        print("\nStep 2: Creating mailchimp_versions folder...")
        mailchimp_folder = self._create_mailchimp_versions_folder()
        print(f"[SUCCESS] Created folder: {mailchimp_folder}")
        
        # Step 3: Process HTML files
        print("\nStep 3: Processing HTML files...")
        processed_files = self._process_html_files(image_url_mapping, mailchimp_folder)
        
        if not processed_files:
            print("[FAILED] Failed to process HTML files")
            return False
            
        print(f"[SUCCESS] Processed {len(processed_files)} HTML files")
        for file_info in processed_files:
            print(f"  {file_info['original_name']} -> {file_info['new_name']}")
        
        # Step 4: Upload to Mailchimp
        print("\nStep 4: Uploading newsletters to Mailchimp...")
        upload_results = self._upload_to_mailchimp(processed_files)
        
        # Step 5: Analyze results
        print("\nStep 5: Results Analysis...")
        self._analyze_results(upload_results)
        
        return upload_results
    
    def _get_image_urls(self):
        """Upload individual images and get Mailchimp URLs."""
        from scripts.image_compressor import ImageCompressor
        
        # Define images to upload
        images_to_upload = [
            {
                'name': 'HRF-Logo.png',
                'path': 'static/images/brand/HRF-Logo.png',
                'type': 'brand',
                'html_path': '../../static/images/brand/HRF-Logo.png'
            },
            {
                'name': 'hero.jpg',
                'path': 'test-images/hero.jpg',
                'type': 'user',
                'html_path': '../../static/images/user-images/d23d0a6b/img-hero.jpg'
            },
            {
                'name': 'story-1.jpg',
                'path': 'test-images/story-1.jpg',
                'type': 'user',
                'html_path': '../../static/images/user-images/d23d0a6b/img-story1.jpg'
            },
            {
                'name': 'story-2.jpg',
                'path': 'test-images/story-2.jpg',
                'type': 'user',
                'html_path': '../../static/images/user-images/d23d0a6b/img-story2.jpg'
            }
        ]
        
        uploader = MailchimpImageUploader()
        url_mapping = {}
        
        print(f"  Uploading {len(images_to_upload)} images individually...")
        
        for image_info in images_to_upload:
            print(f"    Processing: {image_info['name']}")
            
            # Check if file exists
            if not os.path.exists(image_info['path']):
                print(f"      [SKIP] File not found: {image_info['path']}")
                continue
            
            # Upload single image
            result = uploader._upload_single_image(image_info)
            
            if result['status'] == 'success':
                url_mapping[image_info['html_path']] = result['url']
                print(f"      [SUCCESS] {result['url'][:50]}...")
            else:
                print(f"      [FAILED] {result['error']}")
        
        return url_mapping
    
    def _create_mailchimp_versions_folder(self):
        """Create the mailchimp_versions folder structure."""
        mailchimp_folder = Path("test-newsletters/mailchimp_versions")
        mailchimp_folder.mkdir(parents=True, exist_ok=True)
        return str(mailchimp_folder)
    
    def _process_html_files(self, image_url_mapping, output_folder):
        """Process HTML files with URL substitution and proper naming."""
        test_files = [
            "newsletter_Ivory_Coast_en_081425_141914.html",
            "newsletter_Ivory_Coast_fr_081425_141914.html"
        ]
        
        processed_files = []
        
        for filename in test_files:
            file_path = Path("test-newsletters") / filename
            
            if not file_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue
            
            # Read original HTML
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Substitute image URLs
            updated_html = self._substitute_image_urls(html_content, image_url_mapping)
            
            # Generate new filename with timestamp
            new_filename = self._generate_filename(filename)
            output_path = Path(output_folder) / new_filename
            
            # Save processed file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)
            
            processed_files.append({
                'original_name': filename,
                'new_name': new_filename,
                'output_path': str(output_path),
                'html_content': updated_html
            })
            
            print(f"  [SUCCESS] Processed: {filename} -> {new_filename}")
        
        return processed_files
    
    def _substitute_image_urls(self, html_content, url_mapping):
        """Replace local image URLs with Mailchimp URLs."""
        updated_html = html_content
        substitutions_made = 0
        
        for local_path, mailchimp_url in url_mapping.items():
            # Use regex to find and replace src attributes
            pattern = f'src="{re.escape(local_path)}"'
            replacement = f'src="{mailchimp_url}"'
            
            if re.search(pattern, updated_html):
                updated_html = re.sub(pattern, replacement, updated_html)
                substitutions_made += 1
                print(f"    [REPLACED] {local_path}")
        
        print(f"    [SUCCESS] Made {substitutions_made} URL substitutions")
        return updated_html
    
    def _generate_filename(self, original_filename):
        """Generate new filename with timestamp."""
        # Extract country and language from original filename
        # newsletter_Ivory_Coast_en_081425_141914.html -> Ivory_Coast_English_081425_152430.html
        
        now = datetime.now()
        date_str = now.strftime("%m%d%y")
        time_str = now.strftime("%H%M%S")
        
        if "_en_" in original_filename:
            language = "English"
        elif "_fr_" in original_filename:
            language = "French"
        else:
            language = "Unknown"
        
        # Extract country (assuming format: newsletter_Country_Name_lang_...)
        parts = original_filename.split('_')
        if len(parts) >= 3:
            country = parts[1] + "_" + parts[2]  # Ivory_Coast
        else:
            country = "Unknown"
        
        return f"{country}_{language}_{date_str}_{time_str}.html"
    
    def _upload_to_mailchimp(self, processed_files):
        """Upload processed newsletters to Mailchimp as templates."""
        upload_results = []
        
        for file_info in processed_files:
            print(f"\n  Uploading: {file_info['new_name']}")
            
            # Prepare template data
            template_name = file_info['new_name'].replace('.html', '')
            template_data = {
                'name': template_name,
                'html': file_info['html_content']
            }
            
            # Upload to Mailchimp
            try:
                response = requests.post(
                    f"{self.base_url}/templates",
                    auth=('anystring', self.api_key),
                    json=template_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    upload_results.append({
                        'filename': file_info['new_name'],
                        'status': 'success',
                        'template_id': result.get('id'),
                        'template_name': result.get('name'),
                        'error': None
                    })
                    print(f"    [SUCCESS] Template ID: {result.get('id')}")
                else:
                    upload_results.append({
                        'filename': file_info['new_name'],
                        'status': 'failed',
                        'template_id': None,
                        'template_name': None,
                        'error': f"HTTP {response.status_code}: {response.text}"
                    })
                    print(f"    [FAILED] HTTP {response.status_code}")
                    
            except Exception as e:
                upload_results.append({
                    'filename': file_info['new_name'],
                    'status': 'failed',
                    'template_id': None,
                    'template_name': None,
                    'error': str(e)
                })
                print(f"    [EXCEPTION] {str(e)}")
        
        return upload_results
    
    def _analyze_results(self, upload_results):
        """Analyze and display upload results."""
        successful = [r for r in upload_results if r['status'] == 'success']
        failed = [r for r in upload_results if r['status'] == 'failed']
        
        print(f"\nUPLOAD RESULTS:")
        print(f"  Total files: {len(upload_results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        
        if successful:
            print(f"\nSUCCESSFUL UPLOADS:")
            for result in successful:
                print(f"  - {result['filename']} (ID: {result['template_id']})")
        
        if failed:
            print(f"\nFAILED UPLOADS:")
            for result in failed:
                print(f"  - {result['filename']}: {result['error']}")
        
        success_rate = len(successful) / len(upload_results) * 100 if upload_results else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")


def main():
    """Run the newsletter upload test."""
    tester = NewsletterUploadTester()
    results = tester.test_complete_workflow()
    
    if results:
        print(f"\nTest completed with {len(results)} results")
    else:
        print(f"\nTest failed to complete")


if __name__ == "__main__":
    main()
