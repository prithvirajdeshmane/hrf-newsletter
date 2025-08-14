"""
Mailchimp Image Uploader Class

Handles bulk image uploads to Mailchimp File Manager API with retry mechanism
and comprehensive error handling for the HRF Newsletter Generator.
"""

import os
import requests
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from scripts.env_utils import credentials_present
from scripts.image_compressor import ImageCompressor
from dotenv import load_dotenv
import base64


class MailchimpImageUploader:
    """
    Class for uploading images to Mailchimp File Manager API.
    
    Handles discovery of brand and user images, bulk upload with retry logic,
    and comprehensive error reporting.
    """
    
    def __init__(self):
        """Initialize the uploader with Mailchimp credentials and image compressor."""
        load_dotenv()
        
        if not credentials_present():
            raise ValueError("Mailchimp credentials not found. Please configure API key and server prefix.")
        
        self.api_key = os.getenv("MAILCHIMP_API_KEY")
        self.server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.base_url = f"https://{self.server_prefix}.api.mailchimp.com/3.0"
        
        # Upload configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.max_file_size_mb = 1.0
        self.timeout = 30
        
        # Initialize image compressor
        self.compressor = ImageCompressor(max_file_size_mb=self.max_file_size_mb)
        
    def discover_images(self, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Discover all images from brand and user-images folders.
        
        Args:
            session_id: Session ID for user-specific images
            
        Returns:
            List of image info dictionaries with 'name', 'path', and 'type' keys
        """
        images = []
        
        # Brand images (always included)
        brand_path = Path("static/images/brand")
        if brand_path.exists():
            for image_file in brand_path.glob("*"):
                if self._is_image_file(image_file):
                    images.append({
                        'name': image_file.name,
                        'path': str(image_file),
                        'type': 'brand'
                    })
        
        # User images (session-specific)
        if session_id:
            user_path = Path(f"static/images/user-images/{session_id}")
            if user_path.exists():
                for image_file in user_path.glob("*"):
                    if self._is_image_file(image_file):
                        images.append({
                            'name': image_file.name,
                            'path': str(image_file),
                            'type': 'user'
                        })
        
        return images
    
    def _is_image_file(self, file_path: Path) -> bool:
        """Check if file is a supported image format."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return file_path.suffix.lower() in image_extensions
    
    def _validate_file_size(self, file_path: str) -> bool:
        """Validate that file size is within Mailchimp limits."""
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            return file_size_mb <= self.max_file_size_mb
        except OSError:
            return False
    
    def _upload_single_image(self, image_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Upload a single image to Mailchimp with compression and retry logic.
        
        Args:
            image_info: Dictionary with 'name', 'path', and 'type' keys
            
        Returns:
            Dictionary with upload result
        """
        file_path = image_info['path']
        file_name = image_info['name']
        
        # Compress image if needed
        compression_result = self.compressor.compress_image(file_path)
        
        if not compression_result['success']:
            return {
                'name': file_name,
                'status': 'failed',
                'error': f'Compression failed: {compression_result["error"]}',
                'url': None
            }
        
        # Use compressed image path for upload
        upload_file_path = compression_result['output_path']
        temp_file_created = compression_result.get('compression_applied', False)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                with open(upload_file_path, 'rb') as image_file:
                    # Read file content
                    file_content = image_file.read()
                    
                    # Determine MIME type based on file extension
                    file_ext = Path(upload_file_path).suffix.lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg', 
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp',
                        '.webp': 'image/webp',
                        '.svg': 'image/svg+xml'
                    }.get(file_ext, 'image/jpeg')
                    
                    # Use JSON approach with base64 encoding (working solution)
                    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
                    
                    json_payload = {
                        'name': file_name,
                        'type': 'image',
                        'file_data': file_content_b64
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/file-manager/files",
                        auth=('anystring', self.api_key),
                        json=json_payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=self.timeout,
                        verify=True
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        # Clean up temp file if created
                        if temp_file_created:
                            self.compressor.cleanup_temp_files([upload_file_path])
                        
                        return {
                            'name': file_name,
                            'status': 'success',
                            'error': None,
                            'url': result.get('full_size_url', ''),
                            'compressed': temp_file_created,
                            'original_size': compression_result['original_size'],
                            'final_size': compression_result['compressed_size']
                        }
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        if attempt == self.max_retries - 1:
                            # Clean up temp file on final failure
                            if temp_file_created:
                                self.compressor.cleanup_temp_files([upload_file_path])
                            return {
                                'name': file_name,
                                'status': 'failed',
                                'error': error_msg,
                                'url': None
                            }
                        
            except Exception as e:
                error_msg = str(e)
                if attempt == self.max_retries - 1:
                    # Clean up temp file on final failure
                    if temp_file_created:
                        self.compressor.cleanup_temp_files([upload_file_path])
                    return {
                        'name': file_name,
                        'status': 'failed',
                        'error': error_msg,
                        'url': None
                    }
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        # Clean up temp file on max retries exceeded
        if temp_file_created:
            self.compressor.cleanup_temp_files([upload_file_path])
        
        return {
            'name': file_name,
            'status': 'failed',
            'error': 'Max retries exceeded',
            'url': None
        }
    
    def upload_images_bulk(self, image_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Upload multiple images to Mailchimp in bulk.
        
        Args:
            image_list: List of image info dictionaries
            
        Returns:
            Dictionary with overall results and individual image results
        """
        if not image_list:
            return {
                'success': True,
                'message': 'No images to upload',
                'total_images': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'results': []
            }
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for image_info in image_list:
            result = self._upload_single_image(image_info)
            results.append(result)
            
            if result['status'] == 'success':
                successful_count += 1
            else:
                failed_count += 1
        
        # Determine overall success (fail entirely if any image fails)
        overall_success = failed_count == 0
        
        return {
            'success': overall_success,
            'message': f'Uploaded {successful_count}/{len(image_list)} images successfully',
            'total_images': len(image_list),
            'successful_uploads': successful_count,
            'failed_uploads': failed_count,
            'results': results
        }
    
    def upload_session_images(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to discover and upload all images for a session.
        
        Args:
            session_id: Session ID for user-specific images
            
        Returns:
            Dictionary with complete upload results
        """
        try:
            # Discover all images
            images = self.discover_images(session_id)
            
            if not images:
                return {
                    'success': True,
                    'message': 'No images found to upload',
                    'total_images': 0,
                    'successful_uploads': 0,
                    'failed_uploads': 0,
                    'results': []
                }
            
            # Upload images in bulk
            return self.upload_images_bulk(images)
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Upload process failed: {str(e)}',
                'total_images': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'results': []
            }
