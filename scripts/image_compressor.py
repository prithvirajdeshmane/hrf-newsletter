"""
Image Compressor Class

Handles image compression to ensure files are under 1MB for Mailchimp upload requirements.
Uses PIL (Pillow) for image processing with quality reduction and resizing strategies.
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageOps
import tempfile


class ImageCompressor:
    """
    Class for compressing images to meet Mailchimp's 1MB file size limit.
    
    Implements multi-pass compression with quality reduction and resizing
    to guarantee files are under the size limit.
    """
    
    def __init__(self, max_file_size_mb: float = 1.0):
        """
        Initialize the compressor with size limits.
        
        Args:
            max_file_size_mb: Maximum file size in MB (default: 1.0 for Mailchimp)
        """
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.temp_dir = tempfile.gettempdir()
        
        # Compression parameters
        self.initial_quality = 85
        self.min_quality = 20
        self.quality_step = 10
        self.max_dimension = 2048
        self.min_dimension = 400
        
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def _needs_compression(self, file_path: str) -> bool:
        """Check if file needs compression."""
        return self._get_file_size(file_path) > self.max_file_size_bytes
    
    def _get_image_dimensions(self, image: Image.Image) -> Tuple[int, int]:
        """Get image dimensions."""
        return image.size
    
    def _resize_image(self, image: Image.Image, max_dimension: int) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            max_dimension: Maximum width or height
            
        Returns:
            Resized PIL Image object
        """
        width, height = image.size
        
        if width <= max_dimension and height <= max_dimension:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int((height * max_dimension) / width)
        else:
            new_height = max_dimension
            new_width = int((width * max_dimension) / height)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _compress_with_quality(self, image: Image.Image, output_path: str, quality: int) -> bool:
        """
        Compress image with specified quality.
        
        Args:
            image: PIL Image object
            output_path: Output file path
            quality: JPEG quality (1-100)
            
        Returns:
            True if compression successful and under size limit
        """
        try:
            # Convert to RGB if necessary (for JPEG)
            if image.mode in ('RGBA', 'P', 'LA'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                    image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save with specified quality
            image.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            # Check if under size limit
            return self._get_file_size(output_path) <= self.max_file_size_bytes
            
        except Exception as e:
            print(f"Compression error: {e}")
            return False
    
    def compress_image(self, input_path: str, output_path: Optional[str] = None) -> Dict[str, any]:
        """
        Compress image to meet size requirements.
        
        Args:
            input_path: Path to input image
            output_path: Path for compressed output (optional, uses temp file if None)
            
        Returns:
            Dictionary with compression results
        """
        if not os.path.exists(input_path):
            return {
                'success': False,
                'error': f'Input file not found: {input_path}',
                'original_size': 0,
                'compressed_size': 0,
                'output_path': None
            }
        
        original_size = self._get_file_size(input_path)
        
        # Check if compression is needed
        if not self._needs_compression(input_path):
            return {
                'success': True,
                'error': None,
                'original_size': original_size,
                'compressed_size': original_size,
                'output_path': input_path,
                'compression_applied': False
            }
        
        # Generate output path if not provided
        if output_path is None:
            input_file = Path(input_path)
            output_path = os.path.join(
                self.temp_dir, 
                f"compressed_{input_file.stem}.jpg"
            )
        
        try:
            # Open and process image
            with Image.open(input_path) as image:
                # Auto-rotate based on EXIF data
                image = ImageOps.exif_transpose(image)
                
                current_image = image.copy()
                current_dimension = self.max_dimension
                quality = self.initial_quality
                
                # Multi-pass compression
                while quality >= self.min_quality:
                    # Try compression with current quality
                    if self._compress_with_quality(current_image, output_path, quality):
                        compressed_size = self._get_file_size(output_path)
                        return {
                            'success': True,
                            'error': None,
                            'original_size': original_size,
                            'compressed_size': compressed_size,
                            'output_path': output_path,
                            'compression_applied': True,
                            'final_quality': quality,
                            'final_dimensions': current_image.size
                        }
                    
                    # Reduce quality for next attempt
                    quality -= self.quality_step
                    
                    # If quality is getting low, try resizing
                    if quality < 50 and current_dimension > self.min_dimension:
                        current_dimension = max(self.min_dimension, int(current_dimension * 0.8))
                        current_image = self._resize_image(image, current_dimension)
                
                # If all attempts failed
                return {
                    'success': False,
                    'error': f'Could not compress image below {self.max_file_size_bytes} bytes',
                    'original_size': original_size,
                    'compressed_size': self._get_file_size(output_path) if os.path.exists(output_path) else 0,
                    'output_path': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Image processing error: {str(e)}',
                'original_size': original_size,
                'compressed_size': 0,
                'output_path': None
            }
    
    def compress_images_batch(self, image_paths: list) -> Dict[str, any]:
        """
        Compress multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Dictionary with batch compression results
        """
        results = []
        successful_count = 0
        failed_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        for image_path in image_paths:
            result = self.compress_image(image_path)
            results.append({
                'input_path': image_path,
                **result
            })
            
            if result['success']:
                successful_count += 1
            else:
                failed_count += 1
            
            total_original_size += result['original_size']
            total_compressed_size += result['compressed_size']
        
        compression_ratio = (
            (total_original_size - total_compressed_size) / total_original_size * 100
            if total_original_size > 0 else 0
        )
        
        return {
            'success': failed_count == 0,
            'total_images': len(image_paths),
            'successful_compressions': successful_count,
            'failed_compressions': failed_count,
            'total_original_size': total_original_size,
            'total_compressed_size': total_compressed_size,
            'compression_ratio_percent': round(compression_ratio, 2),
            'results': results
        }
    
    def cleanup_temp_files(self, file_paths: list) -> None:
        """
        Clean up temporary compressed files.
        
        Args:
            file_paths: List of temporary file paths to remove
        """
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path) and self.temp_dir in file_path:
                    os.remove(file_path)
            except OSError:
                pass  # Ignore cleanup errors
