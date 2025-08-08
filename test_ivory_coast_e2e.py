#!/usr/bin/env python3
"""
Ivory Coast End-to-End Simulation Test

This test simulates the complete real-world workflow for Ivory Coast:
1. User provides 3 custom images (hero, story-1, story-2)
2. System finds 1 brand image (HRF-Logo.png)
3. Upload all 4 images to Mailchimp (once per country)
4. Generate newsletters for en-CI and fr-CI with Mailchimp image URLs
5. Upload both newsletter templates to Mailchimp with proper naming
6. Verify complete integration works end-to-end

Expected Results:
- 4 images uploaded to Mailchimp with URLs
- 2 newsletters generated (English and French)
- 2 templates uploaded to Mailchimp with IDs
- Proper naming: newsletter_en-CI_{ddmmyy}_{hhmmss}.html
"""

import os
import sys
import json
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image

# Add the scripts directory to the Python path
script_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(script_dir))

from generate_newsletter import get_project_root, find_all_images_to_upload
from batch_image_upload import upload_images_for_newsletter
from batch_template_upload import upload_templates_for_newsletter

def create_ivory_coast_test_images():
    """Create test images for the Ivory Coast scenario."""
    print("🖼️  Creating Ivory Coast test images...")
    
    project_root = get_project_root()
    temp_dir = os.path.join(project_root, 'temp_images')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create the specific images requested by user
    test_images = {
        'hero.jpg': (800, 500),      # Hero image
        'story-1.jpg': (400, 300),   # Story 1 image  
        'story-2.jpg': (400, 300),   # Story 2 image
    }
    
    created_images = []
    
    for filename, (width, height) in test_images.items():
        # Create distinctive colored images for Ivory Coast
        if 'hero' in filename:
            color = (255, 140, 0)    # Orange (Ivory Coast flag color)
        elif 'story-1' in filename:
            color = (0, 128, 0)      # Green (Ivory Coast flag color)
        else:
            color = (255, 255, 255)  # White (Ivory Coast flag color)
            
        image = Image.new('RGB', (width, height), color)
        image_path = os.path.join(temp_dir, filename)
        image.save(image_path, 'JPEG', quality=85)
        
        created_images.append(image_path)
        print(f"   ✅ Created: {filename} ({width}x{height}) - {color}")
    
    return created_images

async def simulate_ivory_coast_scenario():
    """Simulate the complete Ivory Coast newsletter generation scenario."""
    
    print("🇨🇮 Ivory Coast End-to-End Simulation")
    print("=" * 50)
    
    try:
        # Setup
        project_root = get_project_root()
        print(f"📁 Project root: {project_root}")
        
        # Create test images
        test_image_paths = create_ivory_coast_test_images()
        print(f"📸 Created {len(test_image_paths)} test images")
        
        # Load Ivory Coast data
        countries_file = os.path.join(project_root, 'data', 'country_languages.json')
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        if 'Ivory Coast' not in countries_data:
            print("❌ Ivory Coast not found in countries data")
            return False
            
        ivory_coast_info = countries_data['Ivory Coast']
        languages = ivory_coast_info.get('languages', {})
        country_code = ivory_coast_info.get('countryCode', 'CI')
        
        print(f"🇨🇮 Ivory Coast Configuration:")
        print(f"   Country Code: {country_code}")
        print(f"   Languages: {list(languages.keys())}")
        
        # Verify we have English and French
        if 'English' not in languages or 'French' not in languages:
            print("❌ Ivory Coast should have English and French languages")
            return False
        
        # === STEP 1: IMAGE UPLOAD (ONCE PER COUNTRY) ===
        print(f"\n🚀 STEP 1: Upload Images to Mailchimp (Once per Country)")
        
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
        
        print(f"\n📤 Uploading {len(image_paths)} images to Mailchimp...")
        
        # Upload images once
        image_upload_summary = await upload_images_for_newsletter(
            image_paths, 
            usage_contexts=usage_contexts,
            priorities=priorities
        )
        
        print(f"\n📊 Image Upload Results:")
        print(f"   ✅ Successful: {image_upload_summary.successful_uploads}")
        print(f"   💾 Cached: {image_upload_summary.cached_hits}")
        print(f"   ❌ Failed: {image_upload_summary.failed_uploads}")
        print(f"   ⏱️  Time: {image_upload_summary.total_time_seconds:.2f}s")
        print(f"   🔗 URL Mappings: {len(image_upload_summary.url_mappings)}")
        
        # Display Mailchimp URLs
        if image_upload_summary.url_mappings:
            print(f"\n🔗 Mailchimp Image URLs:")
            for local_path, mailchimp_url in image_upload_summary.url_mappings.items():
                filename = os.path.basename(local_path)
                print(f"   {filename} -> {mailchimp_url}")
        
        # === STEP 2: NEWSLETTER GENERATION (PER LANGUAGE) ===
        print(f"\n📄 STEP 2: Generate Newsletters for Each Language")
        
        newsletters_generated = []
        
        for lang_name, lang_data in languages.items():
            lang_code = lang_data.get('languageCode')
            locale = lang_data.get('locale')
            preferred_name = lang_data.get('preferredName', 'Ivory Coast')
            script_direction = lang_data.get('scriptDirection', 'ltr')
            
            print(f"\n📝 Generating {lang_name} newsletter:")
            print(f"   Language Code: {lang_code}")
            print(f"   Locale: {locale}")
            print(f"   Preferred Name: {preferred_name}")
            print(f"   Direction: {script_direction}")
            
            # Create newsletter HTML with Mailchimp image URLs
            html_content = f"""<!DOCTYPE html>
<html lang="{lang_code}" dir="{script_direction}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HRF Newsletter - {preferred_name}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
            direction: {script_direction};
        }}
        .container {{ 
            max-width: 600px; 
            margin: 0 auto; 
            background-color: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 3px solid #ff8c00;
            padding-bottom: 20px;
        }}
        .hero {{ 
            margin-bottom: 30px; 
            text-align: center;
        }}
        .story {{ 
            margin-bottom: 25px; 
            padding: 20px;
            border-left: 4px solid #008000;
            background-color: #f9f9f9;
        }}
        img {{ 
            max-width: 100%; 
            height: auto; 
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #ff8c00;
            color: #666;
        }}
        h1 {{ color: #ff8c00; }}
        h2 {{ color: #008000; }}
        h3 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">"""
            
            # Add HRF Logo with Mailchimp URL
            hrf_logo_url = None
            for local_path, mailchimp_url in image_upload_summary.url_mappings.items():
                if 'HRF-Logo.png' in local_path:
                    hrf_logo_url = mailchimp_url
                    break
            
            if hrf_logo_url:
                html_content += f'\n            <img src="{hrf_logo_url}" alt="Human Rights Foundation Logo" style="max-width: 200px;">'
            
            html_content += f"""
            <h1>Human Rights Foundation Newsletter</h1>
            <h2>{preferred_name}</h2>
        </div>
        
        <div class="hero">"""
            
            # Add hero image with Mailchimp URL
            hero_url = None
            for local_path, mailchimp_url in image_upload_summary.url_mappings.items():
                if 'hero.jpg' in local_path:
                    hero_url = mailchimp_url
                    break
            
            if hero_url:
                html_content += f'\n            <img src="{hero_url}" alt="Newsletter Hero Image">'
            
            html_content += f"""
            <h2>Latest Human Rights Updates</h2>
            <p>Stay informed about human rights developments in {preferred_name}. This newsletter is in {lang_name} ({lang_code}).</p>
        </div>
        
        <div class="story">"""
            
            # Add story 1 image with Mailchimp URL
            story1_url = None
            for local_path, mailchimp_url in image_upload_summary.url_mappings.items():
                if 'story-1.jpg' in local_path:
                    story1_url = mailchimp_url
                    break
            
            if story1_url:
                html_content += f'\n            <img src="{story1_url}" alt="Story 1 Image">'
            
            html_content += f"""
            <h3>Important Human Rights Development</h3>
            <p>This is an important story about human rights progress in {preferred_name}. The content is tailored for {lang_name} speakers and follows {script_direction} text direction.</p>
        </div>
        
        <div class="story">"""
            
            # Add story 2 image with Mailchimp URL
            story2_url = None
            for local_path, mailchimp_url in image_upload_summary.url_mappings.items():
                if 'story-2.jpg' in local_path:
                    story2_url = mailchimp_url
                    break
            
            if story2_url:
                html_content += f'\n            <img src="{story2_url}" alt="Story 2 Image">'
            
            html_content += f"""
            <h3>Community Action Update</h3>
            <p>Learn about recent community actions and advocacy efforts. This newsletter demonstrates our complete Mailchimp integration with optimized image and template upload.</p>
        </div>
        
        <div class="footer">
            <p><strong>Language:</strong> {lang_name} | <strong>Locale:</strong> {locale} | <strong>Direction:</strong> {script_direction}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>© 2025 Human Rights Foundation</p>
        </div>
    </div>
</body>
</html>"""
            
            # Save newsletter with proper naming convention
            timestamp = datetime.now().strftime('%d%m%y_%H%M%S')
            newsletter_filename = f"newsletter_{locale}_{timestamp}.html"
            
            # Create Ivory Coast folder
            ivory_coast_dir = os.path.join(project_root, 'generated_newsletters', 'Ivory_Coast')
            os.makedirs(ivory_coast_dir, exist_ok=True)
            
            newsletter_path = os.path.join(ivory_coast_dir, newsletter_filename)
            
            with open(newsletter_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            newsletters_generated.append({
                'language': lang_name,
                'lang_code': lang_code,
                'locale': locale,
                'filename': newsletter_filename,
                'path': newsletter_path,
                'html_content': html_content,
                'html_size': len(html_content)
            })
            
            print(f"   ✅ Generated: {newsletter_filename}")
            print(f"   📄 HTML Size: {len(html_content)} bytes")
            print(f"   💾 Saved to: Ivory_Coast/{newsletter_filename}")
        
        # === STEP 3: TEMPLATE UPLOAD (PER LANGUAGE) ===
        print(f"\n📤 STEP 3: Upload Newsletter Templates to Mailchimp")
        
        # Prepare templates for upload
        templates_to_upload = []
        for newsletter in newsletters_generated:
            templates_to_upload.append((
                newsletter['html_content'],
                'Ivory Coast',
                newsletter['lang_code'],
                newsletter['locale']
            ))
        
        print(f"📋 Uploading {len(templates_to_upload)} templates to Mailchimp...")
        
        # Upload templates
        template_upload_summary = await upload_templates_for_newsletter(templates_to_upload)
        
        print(f"\n📊 Template Upload Results:")
        print(f"   ✅ Successful: {template_upload_summary.successful_uploads}")
        print(f"   ❌ Failed: {template_upload_summary.failed_uploads}")
        print(f"   ⏱️  Time: {template_upload_summary.total_time_seconds:.2f}s")
        print(f"   📋 Template IDs: {len(template_upload_summary.template_ids)}")
        
        # Display template IDs
        if template_upload_summary.template_ids:
            print(f"\n🔗 Mailchimp Template IDs:")
            for template_name, template_id in template_upload_summary.template_ids.items():
                print(f"   {template_name} -> {template_id}")
        
        # === STEP 4: VERIFICATION AND SUMMARY ===
        print(f"\n🎯 VERIFICATION AND SUMMARY")
        
        # Verify success criteria
        image_success = (
            image_upload_summary.successful_uploads + image_upload_summary.cached_hits == expected_images and
            len(image_upload_summary.url_mappings) == expected_images and
            image_upload_summary.failed_uploads == 0
        )
        
        template_success = (
            template_upload_summary.successful_uploads == len(templates_to_upload) and
            template_upload_summary.failed_uploads == 0 and
            len(template_upload_summary.template_ids) == len(templates_to_upload)
        )
        
        newsletter_success = len(newsletters_generated) == 2
        
        print(f"📊 Success Criteria:")
        print(f"   ✅ Images uploaded successfully: {'✅' if image_success else '❌'}")
        print(f"   ✅ Newsletters generated: {'✅' if newsletter_success else '❌'}")
        print(f"   ✅ Templates uploaded successfully: {'✅' if template_success else '❌'}")
        
        print(f"\n📈 Performance Summary:")
        print(f"   🖼️  Images: {image_upload_summary.successful_uploads + image_upload_summary.cached_hits}/{expected_images} uploaded in {image_upload_summary.total_time_seconds:.2f}s")
        print(f"   📄 Newsletters: {len(newsletters_generated)} generated with proper naming")
        print(f"   📤 Templates: {template_upload_summary.successful_uploads}/{len(templates_to_upload)} uploaded in {template_upload_summary.total_time_seconds:.2f}s")
        
        print(f"\n🎉 IVORY COAST SCENARIO RESULTS:")
        print(f"   🇨🇮 Country: Ivory Coast ({country_code})")
        print(f"   🗣️  Languages: English (en-CI), French (fr-CI)")
        print(f"   🖼️  Images: {len(image_upload_summary.url_mappings)} Mailchimp URLs")
        print(f"   📋 Templates: {len(template_upload_summary.template_ids)} Template IDs")
        print(f"   📄 Local Files: {len(newsletters_generated)} newsletters saved")
        
        all_success = image_success and template_success and newsletter_success
        return all_success
        
    except Exception as e:
        print(f"\n❌ Simulation failed with exception: {e}")
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
    """Main simulation function."""
    print("🇨🇮 Ivory Coast End-to-End Mailchimp Integration Simulation")
    print("=" * 60)
    
    # Run the async simulation
    success = asyncio.run(simulate_ivory_coast_scenario())
    
    if success:
        print(f"\n✅ Ivory Coast simulation PASSED!")
        print("🎉 Complete end-to-end Mailchimp integration working!")
        print("🚀 Ready for production use!")
    else:
        print(f"\n❌ Ivory Coast simulation FAILED!")
        print("🔧 Check the error messages above for debugging information.")
    
    return success

if __name__ == '__main__':
    main()
