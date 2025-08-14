"""
Image processing utilities for HRF Newsletter Generator.

Handles saving user-provided images locally with standardized naming.
"""
import os
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import mimetypes
from urllib.parse import urlparse


class ImageProcessor:
    """Handles image processing and local storage for newsletter generation."""
    
    def __init__(self, base_dir: str = "static/images/user-images", session_id: str = None):
        """
        Initialize ImageProcessor with target directory.
        
        Args:
            base_dir: Directory to save user images (relative to project root)
            session_id: Unique session identifier for user isolation
        """
        self.base_dir = Path(base_dir)
        self.session_id = session_id
        
        # Create session-specific directory if session_id provided
        if session_id:
            self.session_dir = self.base_dir / session_id
            self.session_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.session_dir = self.base_dir
            self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension_from_base64(self, base64_data: str) -> str:
        """
        Extract file extension from base64 data URI.
        
        Args:
            base64_data: Base64 data URI (e.g., 'data:image/jpeg;base64,/9j/4AAQ...')
            
        Returns:
            File extension (.jpg, .png, etc.)
        """
        if base64_data.startswith('data:'):
            # Extract MIME type from data URI
            mime_part = base64_data.split(',')[0]
            if 'image/jpeg' in mime_part or 'image/jpg' in mime_part:
                return '.jpg'
            elif 'image/png' in mime_part:
                return '.png'
            elif 'image/gif' in mime_part:
                return '.gif'
            elif 'image/webp' in mime_part:
                return '.webp'
        
        # Default to .jpg if unable to determine
        return '.jpg'
    
    def _get_file_extension_from_url(self, url: str) -> str:
        """
        Extract file extension from URL.
        
        Args:
            url: Image URL
            
        Returns:
            File extension (.jpg, .png, etc.)
        """
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if path.endswith(('.jpg', '.jpeg')):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        
        # Default to .jpg if unable to determine
        return '.jpg'
    
    def _save_base64_image(self, base64_data: str, filename: str) -> str:
        """
        Save base64 image data to local file.
        
        Args:
            base64_data: Base64 data URI
            filename: Target filename (without extension)
            
        Returns:
            Relative path to saved file (from newsletter location)
        """
        try:
            # Extract extension and actual base64 data
            extension = self._get_file_extension_from_base64(base64_data)
            if ',' in base64_data:
                actual_data = base64_data.split(',')[1]
            else:
                actual_data = base64_data
            
            # Decode base64 data
            image_data = base64.b64decode(actual_data)
            
            # Save to file in session directory
            file_path = self.session_dir / f"{filename}{extension}"
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            # Return relative path from newsletter location (generated_newsletters/{country}/)
            # to the image file (static/images/user-images/{session}/)
            if self.session_id:
                return f"../../static/images/user-images/{self.session_id}/{filename}{extension}"
            else:
                return f"../../static/images/user-images/{filename}{extension}"
            
        except Exception as e:
            print(f"ERROR: Failed to save base64 image {filename}: {str(e)}")
            return ""
    
    def _save_url_image(self, url: str, filename: str) -> str:
        """
        Download and save image from URL.
        
        Args:
            url: Image URL
            filename: Target filename (without extension)
            
        Returns:
            Relative path to saved file (from newsletter location)
        """
        try:
            # Download image
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine extension
            extension = self._get_file_extension_from_url(url)
            
            # Save to file in session directory
            file_path = self.session_dir / f"{filename}{extension}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Return relative path from newsletter location (generated_newsletters/{country}/)
            # to the image file (static/images/user-images/{session}/)
            if self.session_id:
                return f"../../static/images/user-images/{self.session_id}/{filename}{extension}"
            else:
                return f"../../static/images/user-images/{filename}{extension}"
            
        except Exception as e:
            print(f"ERROR: Failed to download and save image from {url}: {str(e)}")
            return ""
    
    def save_user_images(self, form_data: Dict) -> Dict[str, str]:
        """
        Save all user images from form data to local storage.
        
        Args:
            form_data: Form data containing hero and story image data
            
        Returns:
            Dictionary mapping original image references to local file paths
        """
        saved_images = {}
        
        # Process hero image
        hero_data = form_data.get('hero', {})
        hero_image = hero_data.get('image', '')
        
        if hero_image:
            if hero_image.startswith('data:'):
                # Base64 image
                local_path = self._save_base64_image(hero_image, 'img-hero')
            elif hero_image.startswith(('http://', 'https://')):
                # URL image
                local_path = self._save_url_image(hero_image, 'img-hero')
            else:
                # Assume it's already a local path
                local_path = hero_image
            
            if local_path:
                saved_images['hero'] = local_path
        
        # Process story images
        stories = form_data.get('stories', [])
        for i, story in enumerate(stories, 1):
            story_image = story.get('image', '')
            
            if story_image:
                filename = f'img-story{i}'
                
                if story_image.startswith('data:'):
                    # Base64 image
                    local_path = self._save_base64_image(story_image, filename)
                elif story_image.startswith(('http://', 'https://')):
                    # URL image
                    local_path = self._save_url_image(story_image, filename)
                else:
                    # Assume it's already a local path
                    local_path = story_image
                
                if local_path:
                    saved_images[f'story{i}'] = local_path
        
        return saved_images
    
    def cleanup_old_images(self) -> None:
        """
        Clean up old user images to prevent disk space issues.
        For session-based storage, removes all files in the current session directory.
        For non-session storage, removes all files in the user-images directory.
        """
        try:
            if self.session_dir.exists():
                for file_path in self.session_dir.glob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"Cleaned up old image: {file_path.name}")
        except Exception as e:
            print(f"WARNING: Failed to cleanup old images: {str(e)}")
    
    def cleanup_session_directory(self) -> None:
        """
        Clean up entire session directory and all its contents.
        Only works when session_id is provided.
        """
        try:
            if self.session_id and self.session_dir.exists():
                # Remove all files in session directory
                for file_path in self.session_dir.glob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                
                # Remove the session directory itself
                self.session_dir.rmdir()
                print(f"Cleaned up session directory: {self.session_id}")
        except Exception as e:
            print(f"WARNING: Failed to cleanup session directory: {str(e)}")

    @staticmethod
    def cleanup_all_sessions(base_dir: str = "static/images/user-images") -> None:
        """
        Clean up all session directories to prevent disk space issues.
        Useful for maintenance or when sessions expire.
        
        Args:
            base_dir: Base directory containing session folders
        """
        try:
            base_path = Path(base_dir)
            if base_path.exists():
                for session_dir in base_path.iterdir():
                    if session_dir.is_dir():
                        # Remove all files in session directory
                        for file_path in session_dir.glob('*'):
                            if file_path.is_file():
                                file_path.unlink()
                        
                        # Remove the session directory itself
                        session_dir.rmdir()
                        print(f"Cleaned up session directory: {session_dir.name}")
        except Exception as e:
            print(f"WARNING: Failed to cleanup all session directories: {str(e)}")
