import os
from PIL import Image

MAX_FILE_SIZE_MB = 1.0
MAX_WIDTH = 1600

def compress_image_if_needed(image_path):
    """
    Checks if an image is larger than MAX_FILE_SIZE_MB and, if so,
    compresses it by resizing and optimizing. Overwrites the original file.

    Args:
        image_path (str): The absolute path to the image file.

    Returns:
        str: The path to the (now possibly compressed) image.
    """
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if file_size_mb <= MAX_FILE_SIZE_MB:
        # No need to print for every optimized image, keeps logs cleaner.
        return image_path

    print(f"Image '{os.path.basename(image_path)}' is {file_size_mb:.2f} MB. Compressing...")

    try:
        with Image.open(image_path) as img:
            # Ensure image is in RGB mode, as some JPGs might have an alpha channel (RGBA)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if wider than MAX_WIDTH, maintaining aspect ratio
            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / float(img.width)
                new_height = int(float(img.height) * float(ratio))
                img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

            # Save with optimization, overwriting the original file
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            
            new_file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            print(f"Successfully compressed image. New size: {new_file_size_mb:.2f} MB.")

    except Exception as e:
        print(f"Warning: Could not compress image {image_path}. Proceeding with original. Reason: {e}")

    return image_path
