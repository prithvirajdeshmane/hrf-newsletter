"""
Unit Test for Mailchimp Image Upload with Compression

Tests the complete workflow:
1. Image discovery from brand + test-images folders
2. Compression to <1MB
3. Upload to Mailchimp
4. Error analysis
"""

import os
from pathlib import Path
from scripts.mailchimp_image_uploader import MailchimpImageUploader
from scripts.image_compressor import ImageCompressor


def test_image_discovery():
    """Test image discovery from brand and test-images folders."""
    print("=" * 60)
    print("STEP 1: IMAGE DISCOVERY")
    print("=" * 60)
    
    uploader = MailchimpImageUploader()
    
    # Discover images from brand folder
    brand_images = []
    brand_path = Path("static/images/brand")
    if brand_path.exists():
        for image_file in brand_path.glob("*"):
            if uploader._is_image_file(image_file):
                brand_images.append({
                    'name': image_file.name,
                    'path': str(image_file),
                    'type': 'brand'
                })
    
    # Discover images from test-images folder
    test_images = []
    test_path = Path("static/images/test-images")
    if test_path.exists():
        for image_file in test_path.glob("*"):
            if uploader._is_image_file(image_file):
                test_images.append({
                    'name': image_file.name,
                    'path': str(image_file),
                    'type': 'test'
                })
    
    all_images = brand_images + test_images
    
    print(f"Found {len(brand_images)} brand images:")
    for img in brand_images:
        size_kb = os.path.getsize(img['path']) / 1024
        print(f"  - {img['name']}: {size_kb:.1f} KB")
    
    print(f"\nFound {len(test_images)} test images:")
    for img in test_images:
        size_kb = os.path.getsize(img['path']) / 1024
        print(f"  - {img['name']}: {size_kb:.1f} KB")
    
    print(f"\nTotal images to process: {len(all_images)}")
    return all_images


def test_individual_uploads():
    """Test uploading images one by one with detailed logging."""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL IMAGE UPLOADS")
    print("="*60)
    
    uploader = MailchimpImageUploader()
    
    # Get test images
    test_images = uploader.discover_images('test-session')
    if not test_images:
        print("No test images found in /static/images/test-images/")
        return
    
    print(f"Found {len(test_images)} test images")
    
    compression_results = []
    
    for i, image_info in enumerate(test_images, 1):
        print(f"\n--- Testing Image {i}/{len(test_images)}: {image_info['name']} ---")
        
        # Step 1: Test compression first
        print("Step 1: Testing compression...")
        compression_result = uploader.compressor.compress_image(image_info['path'])
        
        if not compression_result['success']:
            print(f"  Compression FAILED: {compression_result['error']}")
            compression_results.append({
                'image': image_info,
                'compression_result': compression_result,
                'upload': {'status': 'skipped', 'error': 'Compression failed'}
            })
            continue
            
        print(f"  Compression SUCCESS")
        print(f"  Original size: {compression_result.get('original_size', 'Unknown')}")
        print(f"  Final size: {compression_result.get('final_size', 'Unknown')}")
        print(f"  Compression applied: {compression_result.get('compression_applied', False)}")
        print(f"  Output path: {compression_result['output_path']}")
        
        # Step 2: Test upload with compressed file
        print("\nStep 2: Testing upload...")
        try:
            # Create modified image_info with compressed path
            upload_image_info = image_info.copy()
            upload_image_info['path'] = compression_result['output_path']
            
            result = uploader._upload_single_image(upload_image_info)
            
            print(f"  Upload Result:")
            print(f"    Status: {result['status']}")
            print(f"    Name: {result['name']}")
            
            if result['status'] == 'success':
                print(f"    URL: {result['url']}")
            else:
                print(f"    Error: {result['error']}")
                
            compression_results.append({
                'image': image_info,
                'compression_result': compression_result,
                'upload': result
            })
                
        except Exception as e:
            print(f"  UPLOAD EXCEPTION: {str(e)}")
            result = {'status': 'failed', 'error': str(e), 'name': image_info['name']}
            compression_results.append({
                'image': image_info,
                'compression_result': compression_result,
                'upload': result
            })
        
        # Step 3: Cleanup temporary files
        if compression_result.get('compression_applied', False):
            try:
                os.remove(compression_result['output_path'])
                print(f"  Cleaned up temporary file: {compression_result['output_path']}")
            except Exception as e:
                print(f"  Cleanup error: {str(e)}")
                
        print("-" * 40)  
    return compression_results


def test_compression(images):
    """Test compression on all images."""
    print("\n" + "=" * 60)
    print("STEP 2: COMPRESSION TESTING")
    print("=" * 60)
    
    compressor = ImageCompressor(max_file_size_mb=1.0)
    compression_results = []
    
    for image in images:
        print(f"\nTesting compression for: {image['name']}")
        
        # Get original size
        original_size = os.path.getsize(image['path'])
        original_mb = original_size / (1024 * 1024)
        print(f"  Original size: {original_mb:.2f} MB")
        
        # Test compression
        result = compressor.compress_image(image['path'])
        compression_results.append({
            'image': image,
            'compression_result': result
        })
        
        if result['success']:
            final_mb = result['compressed_size'] / (1024 * 1024)
            print(f"  [SUCCESS] Compression successful")
            print(f"  Final size: {final_mb:.2f} MB")
            print(f"  Output path: {result['output_path']}")
            if result.get('compression_applied'):
                print(f"  Quality: {result.get('final_quality', 'N/A')}")
                print(f"  Dimensions: {result.get('final_dimensions', 'N/A')}")
            else:
                print(f"  No compression needed (already <1MB)")
        else:
            print(f"  [FAILED] Compression failed: {result['error']}")
    
    return compression_results


def test_single_upload(image_info, compression_result):
    """Test upload of a single compressed image."""
    print(f"\nTesting upload for: {image_info['name']}")
    
    uploader = MailchimpImageUploader()
    
    # Create upload info with compressed path
    upload_info = {
        'name': image_info['name'],
        'path': compression_result['output_path'],
        'type': image_info['type']
    }
    
    # Test upload (but skip compression since we already did it)
    result = uploader._upload_single_image(upload_info)
    
    print(f"  Upload result: {result['status']}")
    if result['status'] == 'success':
        print(f"  [SUCCESS] URL received: {result['url'][:50]}...")
    else:
        print(f"  [FAILED] Error: {result['error']}")
    
    return result


def test_mailchimp_upload(compression_results):
    """Test Mailchimp upload with compressed images."""
    print("\n" + "=" * 60)
    print("STEP 3: MAILCHIMP UPLOAD TESTING")
    print("=" * 60)
    
    upload_results = []
    
    for item in compression_results:
        image = item['image']
        compression_result = item['compression_result']
        
        if compression_result['success']:
            upload_result = test_single_upload(image, compression_result)
            upload_results.append({
                'image': image,
                'compression': compression_result,
                'upload': upload_result
            })
        else:
            print(f"\nSkipping upload for {image['name']} (compression failed)")
            upload_results.append({
                'image': image,
                'compression': compression_result,
                'upload': {'status': 'skipped', 'error': 'Compression failed'}
            })
    
    return upload_results


def analyze_results(upload_results):
    """Analyze and summarize test results."""
    print("\n" + "=" * 60)
    print("STEP 4: RESULTS ANALYSIS")
    print("=" * 60)
    
    successful_uploads = 0
    failed_uploads = 0
    compression_failures = 0
    
    print("\nDetailed Results:")
    for item in upload_results:
        image = item['image']
        compression = item['compression']
        upload = item['upload']
        
        print(f"\n[IMAGE] {image['name']} ({image['type']})")
        
        if compression['success']:
            original_mb = compression['original_size'] / (1024 * 1024)
            final_mb = compression['compressed_size'] / (1024 * 1024)
            print(f"  [COMPRESS] {original_mb:.2f}MB -> {final_mb:.2f}MB")
            
            if upload['status'] == 'success':
                print(f"  [UPLOAD] SUCCESS")
                successful_uploads += 1
            else:
                print(f"  [UPLOAD] FAILED - {upload['error']}")
                failed_uploads += 1
        else:
            print(f"  [COMPRESS] FAILED - {compression['error']}")
            compression_failures += 1
    
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total images tested: {len(upload_results)}")
    print(f"Compression failures: {compression_failures}")
    print(f"Successful uploads: {successful_uploads}")
    print(f"Failed uploads: {failed_uploads}")
    
    if failed_uploads > 0:
        print(f"\nFAILURE ANALYSIS:")
        for item in upload_results:
            if item['upload']['status'] == 'failed':
                print(f"  - {item['image']['name']}: {item['upload']['error']}")


def main():
    """Run the complete test suite."""
    try:
        print("MAILCHIMP IMAGE UPLOAD TEST")
        print("=" * 50)
        
        # Test individual uploads with compression
        results = test_individual_uploads()
        
        if results:
            print("\n" + "="*60)
            print("FINAL RESULTS SUMMARY")
            print("="*60)
            
            success_count = 0
            for result in results:
                upload = result['upload']
                compression = result['compression_result']
                image = result['image']
                
                print(f"\nImage: {image['name']}")
                print(f"  Compression: {'SUCCESS' if compression['success'] else 'FAILED'}")
                if compression['success']:
                    print(f"    Applied: {compression.get('compression_applied', False)}")
                    print(f"    Final size: {compression.get('final_size', 'Unknown')}")
                
                print(f"  Upload: {upload['status'].upper()}")
                if upload['status'] == 'success':
                    success_count += 1
                    print(f"    URL: {upload.get('url', 'N/A')}")
                else:
                    print(f"    Error: {upload.get('error', 'Unknown error')}")
            
            print(f"\nOverall Success Rate: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)")
        else:
            print("No test results to analyze.")
            
    except Exception as e:
        print(f"[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
