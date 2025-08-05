import os
import logging
from PIL import Image, UnidentifiedImageError
from typing import Optional

# Configure logging for better visibility and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for image optimization. Using ALL_CAPS for constants is a common convention.
MAX_FILE_SIZE_MB = 1.0
MAX_WIDTH_PX = 1600
JPEG_QUALITY = 85

class ImageCompressionError(Exception):
    """
    Custom exception for errors during image compression.
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