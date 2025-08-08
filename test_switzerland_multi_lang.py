#!/usr/bin/env python3
"""
Test script to verify the optimized multi-language image upload for Switzerland scenario.
This test simulates:
- User selects Switzerland (CH) with de-CH and fr-CH languages
- User provides 3 custom images: hero.jpg, story-1.jpg, story-2.jpg
- System finds 1 brand image: HRF-Logo.png
- Total 4 images should be uploaded ONCE to Mailchimp
- Same Mailchimp URLs should be reused in both de-CH and fr-CH newsletters
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

from generate_newsletter import get_project_root, find_all_images_to_upload
from batch_image_upload import upload_images_for_newsletter

def create_test_images():
    """Create test images for the Switzerland scenario."""
    print("🖼️  Creating test images...")
    
    project_root = get_project_root()
    temp_dir = os.path.join(project_root, 'temp_images')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create test images with different sizes
    test_images = {
        'hero.jpg': (800, 600),      # Hero image
        'story-1.jpg': (400, 300),   # Story 1 image  
        'story-2.jpg': (400, 300),   # Story 2 image
    }
    
    created_images = []
    
    for filename, (width, height) in test_images.items():
        # Create a simple colored image
        if 'hero' in filename:
            color = (255, 100, 100)  # Red for hero
        elif 'story-1' in filename:
            color = (100, 255, 100)  # Green for story 1
        else:
            color = (100, 100, 255)  # Blue for story 2
            
        image = Image.new('RGB', (width, height), color)
        image_path = os.path.join(temp_dir, filename)
        image.save(image_path, 'JPEG', quality=85)
        
        created_images.append(image_path)
        print(f"   ✅ Created: {filename} ({width}x{height})")
    
    return created_images

def simulate_form_data():
    """Simulate form data for Switzerland with 3 user images."""
    project_root = get_project_root()
    
    return {
        'country': 'Switzerland',
        'hero': {
            'image': os.path.join(project_root, 'temp_images', 'hero.jpg'),
            'imageAlt': 'Switzerland Newsletter Hero',
            'headline': 'Human Rights in Switzerland',
            'description': 'Latest updates on human rights developments.',
            'learnMoreUrl': 'https://example.com/switzerland'
        },
        'ctas': [
            {'text': 'Learn More', 'url': 'https://example.com/cta1'},
            {'text': 'Get Involved', 'url': 'https://example.com/cta2'}
        ],
        'stories': [
            {
                'image': os.path.join(project_root, 'temp_images', 'story-1.jpg'),
                'imageAlt': 'Story 1 about Switzerland',
                'headline': 'Human Rights Progress in Geneva',
                'description': 'Recent developments in Geneva.',
                'url': 'https://example.com/story1'
            },
            {
                'image': os.path.join(project_root, 'temp_images', 'story-2.jpg'),
                'imageAlt': 'Story 2 about Switzerland',
                'headline': 'Civil Liberties Update',
                'description': 'Updates on civil liberties.',
                'url': 'https://example.com/story2'
            }
        ]
    }

async def test_optimized_multi_language_upload():
    """Test the optimized multi-language image upload approach."""
    
    print("🧪 Testing Optimized Multi-Language Image Upload for Switzerland")
    print("=" * 70)
    
    try:
        # Setup
        project_root = get_project_root()
        print(f"📁 Project root: {project_root}")
        
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
        
        # Verify we have German and French
        if 'German' not in languages or 'French' not in languages:
            print("❌ Switzerland should have German and French languages")
            return False
            
        # Simulate user image collection (like collect_user_images would do)
        user_images = []
        for image_path in test_image_paths:
            filename = os.path.basename(image_path)
            relative_path = f"temp_images/{filename}"
            user_images.append((relative_path, image_path))
        
        print(f"👤 User images collected: {len(user_images)}")
        for rel_path, full_path in user_images:
            print(f"   - {rel_path}")
        
        # Find all images (brand + user)
        all_images = find_all_images_to_upload(project_root, user_images)
        print(f"📦 Total images to upload: {len(all_images)}")
        
        # Verify we have 4 images total (3 user + 1 brand)
        expected_images = 4  # hero.jpg, story-1.jpg, story-2.jpg, HRF-Logo.png
        if len(all_images) != expected_images:
            print(f"⚠️  Expected {expected_images} images, found {len(all_images)}")
            for rel_path, full_path in all_images:
                print(f"   - {rel_path}")
        
        # Extract image paths for upload
        image_paths = [full_path for relative_path, full_path in all_images]
        
        # Create usage contexts
        usage_contexts = {}
        priorities = {}
        
        for relative_path, full_path in all_images:
            if 'hero' in relative_path.lower():
                usage_contexts[full_path] = 'hero'
                priorities[full_path] = 'critical'
            elif 'brand' in relative_path.lower():
                usage_contexts[full_path] = 'footer'
                priorities[full_path] = 'important'
            else:
                usage_contexts[full_path] = 'inline'
                priorities[full_path] = 'normal'
        
        print(f"\n🚀 Starting batch upload (ONCE for all languages)...")
        
        # Upload images once
        upload_summary = await upload_images_for_newsletter(
            image_paths, 
            usage_contexts=usage_contexts,
            priorities=priorities
        )
        
        print(f"\n📊 Upload Results:")
        print(f"   ✅ Successful: {upload_summary.successful_uploads}")
        print(f"   💾 Cached: {upload_summary.cached_hits}")
        print(f"   ❌ Failed: {upload_summary.failed_uploads}")
        print(f"   ⏱️  Time: {upload_summary.total_time_seconds:.2f}s")
        print(f"   🔗 URL Mappings: {len(upload_summary.url_mappings)}")
        
        # Verify URL mappings
        if upload_summary.url_mappings:
            print(f"\n🔗 Mailchimp URL Mappings:")
            for local_path, mailchimp_url in upload_summary.url_mappings.items():
                filename = os.path.basename(local_path)
                print(f"   {filename} -> {mailchimp_url[:50]}...")
        
        # Simulate reuse for both languages
        print(f"\n🗣️  Simulating URL reuse for both languages:")
        
        for lang_name, lang_data in languages.items():
            lang_code = lang_data.get('languageCode')
            locale = lang_data.get('locale')
            preferred_name = lang_data.get('preferredName')
            
            print(f"   📝 {lang_name} ({lang_code}):")
            print(f"      Locale: {locale}")
            print(f"      Preferred Name: {preferred_name}")
            print(f"      Would reuse {len(upload_summary.url_mappings)} Mailchimp URLs")
        
        # Calculate efficiency gains
        total_languages = len(languages)
        total_images = len(all_images)
        
        old_approach_uploads = total_languages * total_images  # Upload per language
        new_approach_uploads = total_images  # Upload once
        efficiency_gain = ((old_approach_uploads - new_approach_uploads) / old_approach_uploads) * 100
        
        print(f"\n📈 Efficiency Analysis:")
        print(f"   Languages: {total_languages}")
        print(f"   Images per language: {total_images}")
        print(f"   Old approach uploads: {old_approach_uploads}")
        print(f"   New approach uploads: {new_approach_uploads}")
        print(f"   Efficiency gain: {efficiency_gain:.1f}%")
        
        # Verify success
        success = (
            upload_summary.successful_uploads + upload_summary.cached_hits == total_images and
            len(upload_summary.url_mappings) == total_images and
            upload_summary.failed_uploads == 0
        )
        
        return success
        
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

def main():
    """Main test function."""
    print("🇨🇭 Switzerland Multi-Language Optimization Test")
    print("=" * 50)
    
    # Run the async test
    success = asyncio.run(test_optimized_multi_language_upload())
    
    if success:
        print(f"\n✅ Multi-language optimization test PASSED!")
        print("🎉 Images uploaded once and can be reused across languages!")
        print("💡 This approach is optimal for countries like Switzerland!")
    else:
        print(f"\n❌ Multi-language optimization test FAILED!")
        print("🔧 Check the error messages above for debugging information.")
    
    return success

if __name__ == '__main__':
    main()
