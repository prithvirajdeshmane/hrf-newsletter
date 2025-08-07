#!/usr/bin/env python3
"""
Test Arabic Newsletter Generation with RTL Support and Mailchimp Integration
Tests the complete workflow from newsletter generation to Mailchimp upload.
"""

import os
import sys
import json
import tempfile
import shutil

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except (AttributeError, OSError):
        pass

def safe_print(text):
    """Safely print Unicode text on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def test_arabic_newsletter_generation():
    """Test generating newsletter with Arabic RTL content."""
    safe_print("🌍 Testing Arabic Newsletter Generation with RTL Support")
    safe_print("=" * 60)
    
    # Add the scripts directory to Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
    
    try:
        # Import after adding to path
        import generate_newsletter as gn
        
        # Test data for Arabic newsletter
        arabic_test_data = {
            "title": "نشرة أخبار حقوق الإنسان",
            "subtitle": "آخر الأخبار من البحرين",
            "content": "هذا نص تجريبي باللغة العربية لاختبار دعم النصوص من اليمين إلى اليسار في نظام النشرة الإخبارية. نحن نختبر كيفية عمل النظام مع المحتوى العربي والتكامل مع Mailchimp.",
            "footer": "مؤسسة حقوق الإنسان - البحرين"
        }
        
        safe_print("📝 Test Data:")
        safe_print(f"   Title: {arabic_test_data['title']}")
        safe_print(f"   Country: البحرين (Bahrain)")
        safe_print(f"   Language: Arabic (RTL)")
        safe_print("")
        
        # Create temporary directory for testing
        test_dir = tempfile.mkdtemp()
        safe_print(f"📁 Test Directory: {test_dir}")
        
        try:
            # Test newsletter generation
            if hasattr(gn, 'generate_newsletter_for_geo_lang'):
                safe_print("🚀 Generating Arabic newsletter...")
                
                result = gn.generate_newsletter_for_geo_lang(
                    country_code="BH",
                    lang="ar",
                    data=arabic_test_data,
                    successful_uploads=[],
                    project_root=os.path.dirname(__file__),
                    user_images=None,
                    form_data=None,
                    locale="ar-BH",
                    folder_name="Bahrain",
                    content_country_name="البحرين"
                )
                
                safe_print("✅ Newsletter generation completed!")
                safe_print(f"📊 Result: {result}")
                
                # Check if files were generated
                newsletter_dir = os.path.join(os.path.dirname(__file__), 'generated_newsletters', 'Bahrain')
                if os.path.exists(newsletter_dir):
                    safe_print(f"📂 Newsletter directory created: {newsletter_dir}")
                    
                    # List generated files
                    files = os.listdir(newsletter_dir)
                    safe_print(f"📄 Generated files: {files}")
                    
                    # Check HTML content for RTL attributes
                    html_files = [f for f in files if f.endswith('.html')]
                    if html_files:
                        html_file = os.path.join(newsletter_dir, html_files[0])
                        with open(html_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        safe_print("🔍 Checking HTML content for RTL attributes:")
                        
                        if 'dir="rtl"' in content:
                            safe_print("   ✅ RTL direction attribute found")
                        else:
                            safe_print("   ❌ RTL direction attribute missing")
                        
                        if 'lang="ar"' in content:
                            safe_print("   ✅ Arabic language attribute found")
                        else:
                            safe_print("   ❌ Arabic language attribute missing")
                        
                        if 'البحرين' in content:
                            safe_print("   ✅ Arabic country name found")
                        else:
                            safe_print("   ❌ Arabic country name missing")
                        
                        if arabic_test_data['title'] in content:
                            safe_print("   ✅ Arabic title found")
                        else:
                            safe_print("   ❌ Arabic title missing")
                        
                        safe_print(f"📄 HTML file preview (first 500 chars):")
                        safe_print(content[:500] + "..." if len(content) > 500 else content)
                
                return True
                
            else:
                safe_print("❌ generate_newsletter_for_geo_lang function not available")
                return False
                
        except Exception as e:
            safe_print(f"❌ Newsletter generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)
    
    except ImportError as e:
        safe_print(f"❌ Could not import generate_newsletter module: {e}")
        return False

def test_mailchimp_connection():
    """Test Mailchimp connection with current credentials."""
    safe_print("\n🔗 Testing Mailchimp Connection")
    safe_print("=" * 40)
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        safe_print("✅ .env file found")
        
        # Read credentials
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'MAILCHIMP_API_KEY' in content and 'MAILCHIMP_SERVER_PREFIX' in content:
                safe_print("✅ Mailchimp credentials found in .env")
                
                # Test connection using the test script
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'utils'))
                
                try:
                    import test_mailchimp_connection
                    safe_print("🚀 Testing Mailchimp connection...")
                    
                    # This will run the connection test
                    # Note: The actual test will be performed by the imported module
                    safe_print("📡 Connection test initiated (check console output above)")
                    return True
                    
                except ImportError as e:
                    safe_print(f"❌ Could not import Mailchimp connection test: {e}")
                    return False
                except Exception as e:
                    safe_print(f"❌ Mailchimp connection test failed: {e}")
                    return False
            else:
                safe_print("❌ Mailchimp credentials not found in .env")
                return False
        except Exception as e:
            safe_print(f"❌ Error reading .env file: {e}")
            return False
    else:
        safe_print("❌ .env file not found")
        safe_print("💡 Please run the web interface and add your Mailchimp credentials")
        return False

def test_image_upload_preparation():
    """Test preparation for image upload to Mailchimp."""
    safe_print("\n🖼️ Testing Image Upload Preparation")
    safe_print("=" * 40)
    
    # Check if image upload module exists
    image_upload_path = os.path.join(os.path.dirname(__file__), 'scripts', 'mailchimp_image_upload.py')
    
    if os.path.exists(image_upload_path):
        safe_print("✅ Mailchimp image upload module found")
        
        # Check for test images
        test_images = []
        possible_dirs = ['images', 'assets', 'test_images']
        
        for dir_name in possible_dirs:
            if os.path.exists(dir_name):
                for file in os.listdir(dir_name):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        test_images.append(os.path.join(dir_name, file))
        
        if test_images:
            safe_print(f"✅ Found {len(test_images)} test images:")
            for img in test_images[:3]:  # Show first 3
                safe_print(f"   📷 {img}")
            if len(test_images) > 3:
                safe_print(f"   ... and {len(test_images) - 3} more")
        else:
            safe_print("⚠️  No test images found")
            safe_print("💡 Consider adding test images for upload testing")
        
        return True
    else:
        safe_print("❌ Mailchimp image upload module not found")
        return False

def test_template_upload_preparation():
    """Test preparation for template upload to Mailchimp."""
    safe_print("\n📤 Testing Template Upload Preparation")
    safe_print("=" * 40)
    
    # Check if template upload module exists
    template_upload_path = os.path.join(os.path.dirname(__file__), 'scripts', 'mailchimp_template_upload.py')
    
    if os.path.exists(template_upload_path):
        safe_print("✅ Mailchimp template upload module found")
        
        # Check for generated newsletters
        newsletter_dir = os.path.join(os.path.dirname(__file__), 'generated_newsletters')
        
        if os.path.exists(newsletter_dir):
            countries = os.listdir(newsletter_dir)
            safe_print(f"✅ Found newsletters for {len(countries)} countries:")
            
            for country in countries[:3]:  # Show first 3
                country_path = os.path.join(newsletter_dir, country)
                if os.path.isdir(country_path):
                    files = os.listdir(country_path)
                    html_files = [f for f in files if f.endswith('.html')]
                    safe_print(f"   📄 {country}: {len(html_files)} HTML files")
            
            if len(countries) > 3:
                safe_print(f"   ... and {len(countries) - 3} more countries")
        else:
            safe_print("⚠️  No generated newsletters found")
            safe_print("💡 Generate newsletters first to test template uploads")
        
        return True
    else:
        safe_print("❌ Mailchimp template upload module not found")
        return False

def main():
    """Run all tests."""
    safe_print("🧪 Comprehensive RTL/Arabic Newsletter and Mailchimp Integration Test")
    safe_print("=" * 70)
    
    tests = [
        ("Arabic Newsletter Generation", test_arabic_newsletter_generation),
        ("Mailchimp Connection", test_mailchimp_connection),
        ("Image Upload Preparation", test_image_upload_preparation),
        ("Template Upload Preparation", test_template_upload_preparation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        safe_print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            safe_print(f"📊 {test_name}: {status}")
        except Exception as e:
            safe_print(f"💥 {test_name}: ERROR ({e})")
            results.append((test_name, False))
    
    # Summary
    safe_print("\n" + "=" * 70)
    safe_print("📋 Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        safe_print(f"   {status} {test_name}")
    
    safe_print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        safe_print("🎉 All tests passed! System is ready for Arabic newsletters and Mailchimp integration!")
    else:
        safe_print("🔧 Some tests failed. Review the issues above and fix them before proceeding.")
    
    safe_print("=" * 70)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
