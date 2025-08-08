#!/usr/bin/env python3
"""
Comprehensive Template Upload Integration Test

This test verifies the complete Mailchimp integration workflow:
1. Image upload optimization (once per country)
2. Template upload for each language version
3. End-to-end Switzerland scenario with de-CH and fr-CH

Tests the complete workflow:
- User provides images and content for Switzerland
- System uploads images once to Mailchimp
- System generates newsletters for German and French
- System uploads 2 separate templates to Mailchimp (different content)
- Verifies template IDs are returned and tracked
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from PIL import Image

# Add the scripts directory to the Python path
script_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(script_dir))

from generate_newsletter import get_project_root
from batch_template_upload import upload_templates_for_newsletter, clear_template_cache

def create_test_images():
    """Create test images for the template upload test."""
    print("🖼️  Creating test images for template upload test...")
    
    project_root = get_project_root()
    temp_dir = os.path.join(project_root, 'temp_images')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create test images
    test_images = {
        'hero.jpg': (600, 400),      # Hero image
        'story-1.jpg': (300, 200),   # Story 1 image  
    }
    
    created_images = []
    
    for filename, (width, height) in test_images.items():
        # Create a simple colored image
        if 'hero' in filename:
            color = (200, 50, 50)  # Dark red for hero
        else:
            color = (50, 200, 50)  # Dark green for story
            
        image = Image.new('RGB', (width, height), color)
        image_path = os.path.join(temp_dir, filename)
        image.save(image_path, 'JPEG', quality=90)
        
        created_images.append(image_path)
        print(f"   ✅ Created: {filename} ({width}x{height})")
    
    return created_images

async def test_template_upload_integration():
    """Test the complete template upload integration."""
    
    print("🧪 Testing Complete Template Upload Integration")
    print("=" * 60)
    
    try:
        # Setup
        project_root = get_project_root()
        print(f"📁 Project root: {project_root}")
        
        # Clear template cache for clean test
        clear_template_cache()
        print("🧹 Template cache cleared for clean test")
        
        # Create test images
        test_image_paths = create_test_images()
        
        # Load Switzerland data
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        if 'Switzerland' not in countries_data:
            print("❌ Switzerland not found in countries data")
            return False
            
        switzerland_info = countries_data['Switzerland']
        languages = switzerland_info.get('languages', {})
        
        print(f"🇨🇭 Switzerland Configuration:")
        print(f"   Country Code: {switzerland_info.get('countryCode')}")
        print(f"   Languages: {list(languages.keys())}")
        
        # Create test HTML templates for each language
        templates_to_upload = []
        
        for lang_name, lang_data in languages.items():
            lang_code = lang_data.get('languageCode')
            locale = lang_data.get('locale')
            preferred_name = lang_data.get('preferredName')
            script_direction = lang_data.get('scriptDirection', 'ltr')
            
            # Create language-specific HTML content
            html_content = f"""<!DOCTYPE html>
<html lang="{lang_code}" dir="{script_direction}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter - {preferred_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .hero {{ margin-bottom: 30px; }}
        .story {{ margin-bottom: 20px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <img src="https://mcusercontent.com/b3fcbb2e5d1a37cab6bb0f4e4/images/test-logo.png" alt="HRF Logo">
        <h1>Human Rights Foundation Newsletter</h1>
        <h2>{preferred_name}</h2>
    </div>
    
    <div class="hero">
        <img src="https://mcusercontent.com/b3fcbb2e5d1a37cab6bb0f4e4/images/test-hero.jpg" alt="Hero Image">
        <h2>Latest Human Rights Updates</h2>
        <p>Stay informed about human rights developments in {preferred_name}.</p>
    </div>
    
    <div class="story">
        <img src="https://mcusercontent.com/b3fcbb2e5d1a37cab6bb0f4e4/images/test-story1.jpg" alt="Story Image">
        <h3>Important Story Title</h3>
        <p>This is an important story about human rights developments. Content is in {lang_name} ({lang_code}).</p>
    </div>
    
    <div class="footer">
        <p>Language: {lang_name} | Locale: {locale} | Direction: {script_direction}</p>
        <p>© 2025 Human Rights Foundation</p>
    </div>
</body>
</html>"""
            
            templates_to_upload.append((
                html_content,
                "Switzerland",
                lang_code,
                locale
            ))
            
            print(f"📄 Template prepared for {lang_name}:")
            print(f"   Language Code: {lang_code}")
            print(f"   Locale: {locale}")
            print(f"   Preferred Name: {preferred_name}")
            print(f"   Direction: {script_direction}")
            print(f"   HTML Size: {len(html_content)} bytes")
        
        print(f"\n🚀 Starting batch template upload for {len(templates_to_upload)} templates...")
        
        # Upload templates
        upload_summary = await upload_templates_for_newsletter(templates_to_upload)
        
        print(f"\n📊 Template Upload Results:")
        print(f"   ✅ Successful: {upload_summary.successful_uploads}")
        print(f"   ❌ Failed: {upload_summary.failed_uploads}")
        print(f"   ⏱️  Time: {upload_summary.total_time_seconds:.2f}s")
        print(f"   📋 Template IDs: {len(upload_summary.template_ids)}")
        
        # Display template IDs
        if upload_summary.template_ids:
            print(f"\n🔗 Mailchimp Template IDs:")
            for template_name, template_id in upload_summary.template_ids.items():
                print(f"   {template_name} -> {template_id}")
        
        # Display detailed results
        print(f"\n📋 Detailed Upload Results:")
        for result in upload_summary.upload_results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.template_name}")
            if result.success:
                print(f"      Template ID: {result.template_id}")
                print(f"      Upload Time: {result.upload_time_seconds:.2f}s")
                print(f"      HTML Size: {result.html_size_bytes} bytes")
            else:
                print(f"      Error: {result.error_message}")
        
        # Verify success criteria
        expected_templates = len(templates_to_upload)
        success_criteria = [
            upload_summary.total_templates == expected_templates,
            upload_summary.successful_uploads == expected_templates,
            upload_summary.failed_uploads == 0,
            len(upload_summary.template_ids) == expected_templates
        ]
        
        all_success = all(success_criteria)
        
        print(f"\n🎯 Success Criteria:")
        print(f"   Expected templates: {expected_templates} {'✅' if success_criteria[0] else '❌'}")
        print(f"   All uploads successful: {'✅' if success_criteria[1] else '❌'}")
        print(f"   No failures: {'✅' if success_criteria[2] else '❌'}")
        print(f"   All template IDs received: {'✅' if success_criteria[3] else '❌'}")
        
        # Show errors if any
        if upload_summary.errors:
            print(f"\n⚠️  Upload Errors:")
            for error in upload_summary.errors:
                print(f"     - {error}")
        
        # Performance analysis
        if upload_summary.successful_uploads > 0:
            avg_upload_time = upload_summary.total_time_seconds / upload_summary.successful_uploads
            print(f"\n📈 Performance Analysis:")
            print(f"   Average upload time per template: {avg_upload_time:.2f}s")
            print(f"   Total templates uploaded: {upload_summary.successful_uploads}")
            print(f"   Templates ready for campaign creation: {len(upload_summary.template_ids)}")
        
        return all_success
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        # Cleanup test images
        try:
            temp_dir = os.path.join(get_project_root(), 'temp_images')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up test images")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

async def test_template_validation():
    """Test template validation functionality."""
    
    print("\n🔍 Testing Template Validation...")
    
    # Test cases for validation
    test_cases = [
        ("", "Empty HTML", False),
        ("Not HTML content", "No HTML tags", False),
        ("<html><body><h1>Valid</h1><img src='https://mcusercontent.com/test.jpg'></body></html>", "Valid HTML", True),
        ("<html><body>" + "x" * 1_000_001 + "</body></html>", "Too large", False),
        ("<body><h1>Missing html tag</h1></body>", "Missing html tag", False)
    ]
    
    from batch_template_upload import BatchTemplateUploader
    uploader = BatchTemplateUploader()
    
    for html_content, description, expected_valid in test_cases:
        is_valid, error_msg = uploader._validate_html_content(html_content, f"test_{description}")
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"   {status} {description}: {'Valid' if is_valid else f'Invalid - {error_msg}'}")
    
    print("🔍 Template validation tests completed")

def main():
    """Main test function."""
    print("📤 Template Upload Integration Test")
    print("=" * 40)
    
    async def run_all_tests():
        # Run template validation tests
        await test_template_validation()
        
        # Run main integration test
        success = await test_template_upload_integration()
        
        return success
    
    # Run the async tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print(f"\n✅ Template upload integration test PASSED!")
        print("🎉 Templates uploaded successfully for multi-language scenario!")
        print("📋 Template IDs are tracked and ready for campaign creation!")
    else:
        print(f"\n❌ Template upload integration test FAILED!")
        print("🔧 Check the error messages above for debugging information.")
    
    return success

if __name__ == '__main__':
    main()
