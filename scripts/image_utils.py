import os
import logging
from PIL import Image, UnidentifiedImageError
from typing import Optional

# Configure logging for better visibility and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for image optimization. Using ALL_CAPS for constants is a common convention.
MAX_FILE_SIZE_MB = 1.0          # HARD LIMIT - Mailchimp constraint
SAFETY_MARGIN_MB = 0.95         # Target 95% of limit for safety
MAX_WIDTH_PX = 1600
JPEG_QUALITY = 85

# Progressive compression settings for enforcing 1MB limit
COMPRESSION_STRATEGIES = [
    {'quality': 85, 'max_width': 1600, 'name': 'conservative'},
    {'quality': 75, 'max_width': 1200, 'name': 'moderate'},
    {'quality': 65, 'max_width': 800, 'name': 'aggressive'},
    {'quality': 55, 'max_width': 600, 'name': 'very_aggressive'},
    {'quality': 45, 'max_width': 400, 'name': 'last_resort'}
]

class ImageCompressionError(Exception):
    """
    Custom exception for errors during image compression.
    """
    pass

class CriticalImageError(Exception):
    """
    Raised when image cannot be compressed under 1MB limit.
    """
    pass

def compress_image_if_needed(image_path: str) -> Optional[str]:
    """
    Optimizes a local image file by resizing and compressing it if its size
    exceeds a predefined maximum or its width is too large.

    The function checks the image's size and dimensions. If optimization is
    required, it resizes the image while maintaining aspect ratio and saves it
    with JPEG compression. The original file is overwritten with the optimized version.

    Args:
        image_path: The absolute path to the image file.

    Returns:
        The path to the (possibly compressed) image file, or None if the
        image file does not exist or an unrecoverable error occurs.

    Raises:
        ImageCompressionError: If the file cannot be opened or processed
                               as an image.
    """
    # Check if the file exists and is a file. Return None to indicate failure
    # and prevent further processing.
    if not os.path.isfile(image_path):
        logging.error(f"Image file does not exist at path: {image_path}")
        return None

    # Determine the initial file size
    initial_file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

    # Check if optimization is needed based on file size
    if initial_file_size_mb <= MAX_FILE_SIZE_MB:
        logging.info(f"Image '{os.path.basename(image_path)}' is within size limit ({initial_file_size_mb:.2f} MB). No compression needed.")
        return image_path
    
    logging.info(f"Image '{os.path.basename(image_path)}' is {initial_file_size_mb:.2f} MB. Starting compression...")

    try:
        with Image.open(image_path) as img:
            # Check image width to see if resizing is needed
            if img.width > MAX_WIDTH_PX:
                ratio = MAX_WIDTH_PX / float(img.width)
                new_height = int(float(img.height) * ratio)
                logging.info(f"Resizing image from {img.width}x{img.height} to {MAX_WIDTH_PX}x{new_height}.")
                img = img.resize((MAX_WIDTH_PX, new_height), Image.Resampling.LANCZOS)
            
            # Ensure the image is in a compatible format for saving as JPEG
            # This handles images with an alpha channel (RGBA) or palette (P).
            if img.mode in ('RGBA', 'P'):
                logging.info(f"Converting image from '{img.mode}' mode to 'RGB'.")
                img = img.convert('RGB')
            
            # Save the optimized image, overwriting the original file
            img.save(image_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)
            
        new_file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        logging.info(f"Compression complete. New size: {new_file_size_mb:.2f} MB.")
    
    except UnidentifiedImageError as e:
        error_msg = f"Failed to open image file '{image_path}': Not a valid image file. Reason: {e}"
        logging.error(error_msg)
        raise ImageCompressionError(error_msg) from e
    except Exception as e:
        error_msg = f"An unexpected error occurred during image compression for '{image_path}'. Reason: {e}"
        logging.error(error_msg)
        raise ImageCompressionError(error_msg) from e

    return image_path

def ensure_under_1mb(image_path: str) -> str:
    """
    GUARANTEE image is under 1MB - this is non-negotiable for Mailchimp compliance.
    
    Uses progressive compression strategies with increasing aggressiveness until
    the image is under the 1MB limit. This is a hard requirement for Mailchimp uploads.
    
    Args:
        image_path: The absolute path to the image file.
        
    Returns:
        The path to the compressed image (guaranteed under 1MB).
        
    Raises:
        CriticalImageError: If image cannot be compressed under 1MB after all attempts.
        ImageCompressionError: If file cannot be processed as an image.
    """
    if not os.path.isfile(image_path):
        raise ImageCompressionError(f"Image file does not exist: {image_path}")
    
    initial_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    logging.info(f"Starting 1MB enforcement for {os.path.basename(image_path)} ({initial_size_mb:.2f} MB)")
    
    # If already under safety margin, return as-is
    if initial_size_mb <= SAFETY_MARGIN_MB:
        logging.info(f"Image already under safety margin ({initial_size_mb:.2f} MB)")
        return image_path
    
    try:
        # Try each compression strategy progressively
        for i, strategy in enumerate(COMPRESSION_STRATEGIES):
            current_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            
            if current_size_mb <= SAFETY_MARGIN_MB:
                logging.info(f"Image compressed to {current_size_mb:.2f} MB using {strategy['name']} strategy")
                return image_path
            
            logging.warning(f"Attempt {i + 1}/{len(COMPRESSION_STRATEGIES)}: Applying {strategy['name']} compression...")
            
            with Image.open(image_path) as img:
                # Calculate new dimensions
                if img.width > strategy['max_width']:
                    ratio = strategy['max_width'] / float(img.width)
                    new_width = strategy['max_width']
                    new_height = int(float(img.height) * ratio)
                    logging.info(f"Resizing from {img.width}x{img.height} to {new_width}x{new_height}")
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    logging.info(f"Converting from {img.mode} to RGB")
                    img = img.convert('RGB')
                
                # Save with aggressive compression
                img.save(image_path, 'JPEG', quality=strategy['quality'], optimize=True)
                
                new_size_mb = os.path.getsize(image_path) / (1024 * 1024)
                logging.info(f"Compressed to {new_size_mb:.2f} MB with quality {strategy['quality']}%")
        
        # Final check - if still over 1MB, this is a critical error
        final_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if final_size_mb > MAX_FILE_SIZE_MB:
            raise CriticalImageError(
                f"CRITICAL: Cannot compress image under 1MB limit. "
                f"Final size: {final_size_mb:.2f}MB after all compression attempts. "
                f"Original size: {initial_size_mb:.2f}MB. "
                f"This image cannot be uploaded to Mailchimp."
            )
        
        logging.info(f"SUCCESS: Image guaranteed under 1MB ({final_size_mb:.2f} MB)")
        return image_path
        
    except UnidentifiedImageError as e:
        raise ImageCompressionError(f"Invalid image file: {image_path}. Error: {e}") from e
    except Exception as e:
        raise ImageCompressionError(f"Compression failed for {image_path}. Error: {e}") from e

def validate_mailchimp_size_limit(image_path: str) -> bool:
    """
    Final validation before Mailchimp upload - CRITICAL SAFETY CHECK.
    
    Args:
        image_path: Path to image file to validate.
        
    Returns:
        True if image is under 1MB limit.
        
    Raises:
        CriticalImageError: If image exceeds 1MB limit.
    """
    if not os.path.isfile(image_path):
        raise ImageCompressionError(f"Image file does not exist: {image_path}")
    
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise CriticalImageError(
            f"CRITICAL: Image {os.path.basename(image_path)} is {file_size_mb:.2f}MB - "
            f"exceeds Mailchimp 1MB limit! This should never happen if compression worked correctly."
        )
    
    if file_size_mb > SAFETY_MARGIN_MB:
        logging.warning(f"Image {os.path.basename(image_path)} is {file_size_mb:.2f}MB - close to 1MB limit")
    
    logging.info(f"✅ Size validation passed: {os.path.basename(image_path)} ({file_size_mb:.2f}MB)")
    return True

if __name__ == '__main__':
    # This example requires a dummy image file. Let's create one.
    from PIL import Image, ImageDraw
    
    # Create a large dummy image (e.g., a 2000x1200 image) to test resizing and compression.
    dummy_image_path = "large_test_image.jpg"
    try:
        # Check if the file already exists
        if not os.path.exists(dummy_image_path):
            img_to_create = Image.new('RGB', (2000, 1200), color = 'red')
            draw = ImageDraw.Draw(img_to_create)
            draw.text((10,10), "Large Test Image", fill='white')
            img_to_create.save(dummy_image_path, 'JPEG', quality=95)
            print(f"Created a large dummy image at '{dummy_image_path}' for testing.")
        
        # Run the compression function
        optimized_path = compress_image_if_needed(dummy_image_path)
        if optimized_path:
            print(f"Processing complete. Final image at: {optimized_path}")
            # You can add checks here to verify the new size/width if needed.
        
        # Test a scenario with an already small image.
        small_image_path = "small_test_image.jpg"
        if not os.path.exists(small_image_path):
            img_to_create = Image.new('RGB', (800, 600), color = 'blue')
            img_to_create.save(small_image_path, 'JPEG', quality=85)
            print(f"Created a small dummy image at '{small_image_path}' for testing.")
        
        print("\nTesting with an image that is already small...")
        optimized_path_small = compress_image_if_needed(small_image_path)
        print(f"Processing complete. Final image at: {optimized_path_small}")

    except ImageCompressionError as e:
        print(f"Image compression failed with a specific error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Clean up the dummy files
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)
        if os.path.exists(small_image_path):
            os.remove(small_image_path)
        print("\nCleaned up dummy files.")