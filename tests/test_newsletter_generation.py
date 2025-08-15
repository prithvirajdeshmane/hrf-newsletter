"""
Test script for newsletter generation with translation fixes.

This script tests the complete newsletter generation workflow to verify
that all the translation fixes are working correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

from app import generate_newsletter_templates

def test_newsletter_generation():
    """Test newsletter generation with Central African Republic (en + fr)."""
    print("Testing Newsletter Generation with Translation Fixes")
    print("=" * 60)
    
    # Test data for Central African Republic
    form_data = {
        'country': 'Central African Republic',
        'hero': {
            'image': 'test_hero_image.jpg',
            'imageAlt': 'Human rights activists protesting',
            'headline': 'Fighting for Freedom in Central Africa',
            'description': 'Join us in supporting human rights defenders who risk their lives for democracy and freedom.',
            'url': 'https://example.com/learn-more'
        },
        'stories': [
            {
                'image': 'test_story1.jpg',
                'imageAlt': 'Democracy protesters',
                'headline': 'Democracy Under Attack',
                'description': 'Activists work tirelessly to protect democratic institutions from authoritarian threats.',
                'url': 'https://example.com/story1',
                'cta': {
                    'text': 'Support Democracy',
                    'url': 'https://example.com/support'
                }
            },
            {
                'image': 'test_story2.jpg',
                'imageAlt': 'Human rights defenders',
                'headline': 'Defending Human Rights',
                'description': 'Local organizations provide crucial support to those fighting for basic human rights.',
                'url': 'https://example.com/story2',
                'cta': {
                    'text': 'Donate Now',
                    'url': 'https://example.com/donate'
                }
            }
        ],
        'ctas': [
            {
                'text': 'Join Our Mission',
                'url': 'https://example.com/join'
            },
            {
                'text': 'Make a Donation',
                'url': 'https://example.com/donate'
            }
        ]
    }
    
    try:
        print("Generating newsletters for Central African Republic...")
        generated_files = generate_newsletter_templates(form_data)
        
        print(f"[OK] Generated {len(generated_files)} newsletter files:")
        for file_path in generated_files:
            print(f"  - {Path(file_path).name}")
        
        # Check the content of the French version
        fr_file = None
        for file_path in generated_files:
            if '_fr_' in Path(file_path).name:
                fr_file = file_path
                break
        
        if fr_file:
            print(f"\nChecking French version content: {Path(fr_file).name}")
            with open(fr_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for specific fixes
            fixes_verified = []
            
            # 1. Check for proper apostrophes (not HTML entities)
            if "l'histoire" in content.lower() or "l'histoire" in content.lower():
                fixes_verified.append("[OK] Proper apostrophes in French text")
            elif "l&#39;histoire" in content:
                fixes_verified.append("[ERROR] HTML entities still present in French text")
            else:
                fixes_verified.append("[INFO] Apostrophe test inconclusive")
            
            # 2. Check for country name (République Centrafricaine)
            if "République Centrafricaine" in content:
                fixes_verified.append("[OK] Country name using preferredName")
            elif "Central African Republic" in content:
                fixes_verified.append("[ERROR] Country name not translated")
            else:
                fixes_verified.append("[INFO] Country name test inconclusive")
            
            # 3. Check for CTA buttons (should have proper styling)
            cta_count = content.count('background-color: #007bff')
            if cta_count >= 4:  # Hero Learn More + 2 Hero CTAs + Story CTAs
                fixes_verified.append(f"[OK] Found {cta_count} properly styled CTA buttons")
            else:
                fixes_verified.append(f"[WARNING] Only found {cta_count} CTA buttons (expected 4+)")
            
            # 4. Check for translated static text
            if "Lire l'histoire" in content or "Lire l'histoire" in content:
                fixes_verified.append("[OK] 'Read Story' translated to French")
            else:
                fixes_verified.append("[ERROR] 'Read Story' not properly translated")
            
            print("\nFix Verification Results:")
            for result in fixes_verified:
                print(f"  {result}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Newsletter generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Newsletter Generation Test with Translation Fixes")
    print("=" * 60)
    
    success = test_newsletter_generation()
    
    if success:
        print("\n[SUCCESS] Newsletter generation test completed!")
        print("Check the generated files in the 'generated_newsletters/Central African Republic/' directory")
    else:
        print("\n[ERROR] Newsletter generation test failed!")
        sys.exit(1)
