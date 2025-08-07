#!/usr/bin/env python3
"""
Direct Arabic Newsletter Test - Bypassing UTF-8 encoding conflicts
Tests Arabic newsletter generation using the web interface approach.
"""

import os
import sys
import json
import requests
import time

# Fix Windows console encoding
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

def test_arabic_newsletter_via_api():
    """Test Arabic newsletter generation via the web API."""
    safe_print("🌍 Testing Arabic Newsletter Generation via Web API")
    safe_print("=" * 55)
    
    # Test data for Arabic newsletter (with all required fields)
    arabic_form_data = {
        "country": "Bahrain",
        "language": "Arabic",
        "title": "نشرة أخبار حقوق الإنسان",
        "subtitle": "آخر الأخبار من البحرين",
        "hero": "أهلاً وسهلاً بكم في نشرة حقوق الإنسان الخاصة بالبحرين",
        "content": "هذا نص تجريبي باللغة العربية لاختبار دعم النصوص من اليمين إلى اليسار في نظام النشرة الإخبارية. نحن نختبر كيفية عمل النظام مع المحتوى العربي والتكامل مع Mailchimp. يتضمن هذا الاختبار التحقق من أن جميع النصوص العربية تظهر بشكل صحيح وأن اتجاه النص من اليمين إلى اليسار يعمل كما هو متوقع.",
        "footer": "مؤسسة حقوق الإنسان - البحرين",
        "author": "فريق حقوق الإنسان",
        "date": "2025-08-07"
    }
    
    safe_print("📝 Test Data:")
    safe_print(f"   Country: {arabic_form_data['country']}")
    safe_print(f"   Language: {arabic_form_data['language']}")
    safe_print(f"   Title: {arabic_form_data['title']}")
    safe_print("")
    
    try:
        # Make API request to generate newsletter
        safe_print("🚀 Sending API request to generate Arabic newsletter...")
        
        response = requests.post(
            'http://localhost:5000/api/build-newsletter',
            json=arabic_form_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        safe_print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            safe_print("✅ Newsletter generation successful!")
            safe_print(f"📊 Result: {result}")
            
            # Check if files were generated
            newsletter_dir = os.path.join(os.path.dirname(__file__), 'generated_newsletters', 'Bahrain')
            if os.path.exists(newsletter_dir):
                safe_print(f"📂 Newsletter directory: {newsletter_dir}")
                
                # List files
                files = os.listdir(newsletter_dir)
                html_files = [f for f in files if f.endswith('.html')]
                safe_print(f"📄 HTML files found: {len(html_files)}")
                
                # Check latest HTML file for RTL content
                if html_files:
                    # Sort by modification time to get the latest
                    html_files.sort(key=lambda x: os.path.getmtime(os.path.join(newsletter_dir, x)), reverse=True)
                    latest_html = html_files[0]
                    
                    safe_print(f"🔍 Checking latest HTML file: {latest_html}")
                    
                    html_path = os.path.join(newsletter_dir, latest_html)
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for RTL attributes and Arabic content
                    checks = [
                        ('dir="rtl"', "RTL direction attribute"),
                        ('lang="ar"', "Arabic language attribute"),
                        ('البحرين', "Arabic country name"),
                        (arabic_form_data['title'], "Arabic title"),
                        ('مؤسسة حقوق الإنسان', "Arabic footer")
                    ]
                    
                    safe_print("🔍 Content validation:")
                    all_passed = True
                    
                    for check_text, description in checks:
                        if check_text in content:
                            safe_print(f"   ✅ {description}: Found")
                        else:
                            safe_print(f"   ❌ {description}: Missing")
                            all_passed = False
                    
                    if all_passed:
                        safe_print("🎉 All RTL/Arabic content checks passed!")
                    else:
                        safe_print("⚠️  Some RTL/Arabic content checks failed")
                    
                    # Show HTML preview
                    safe_print(f"\n📄 HTML Preview (first 800 characters):")
                    safe_print("-" * 50)
                    preview = content[:800] + "..." if len(content) > 800 else content
                    safe_print(preview)
                    safe_print("-" * 50)
                    
                    return all_passed
                else:
                    safe_print("❌ No HTML files found")
                    return False
            else:
                safe_print("❌ Newsletter directory not found")
                return False
        else:
            safe_print(f"❌ API request failed: {response.status_code}")
            try:
                error_data = response.json()
                safe_print(f"📄 Error details: {error_data}")
            except:
                safe_print(f"📄 Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        safe_print("❌ Connection failed - is the Flask server running?")
        safe_print("💡 Start the server with: python scripts/generate_newsletter.py")
        return False
    except Exception as e:
        safe_print(f"❌ Unexpected error: {e}")
        return False

def test_existing_newsletters():
    """Check existing newsletters for RTL content."""
    safe_print("\n📂 Checking Existing Newsletters")
    safe_print("=" * 35)
    
    newsletter_dir = os.path.join(os.path.dirname(__file__), 'generated_newsletters')
    
    if os.path.exists(newsletter_dir):
        countries = os.listdir(newsletter_dir)
        safe_print(f"📊 Found newsletters for {len(countries)} countries:")
        
        for country in countries:
            country_path = os.path.join(newsletter_dir, country)
            if os.path.isdir(country_path):
                files = os.listdir(country_path)
                html_files = [f for f in files if f.endswith('.html')]
                safe_print(f"   📄 {country}: {len(html_files)} HTML files")
                
                # Check if any contain Arabic content
                for html_file in html_files:
                    html_path = os.path.join(country_path, html_file)
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if 'dir="rtl"' in content or 'البحرين' in content:
                            safe_print(f"      🌍 {html_file}: Contains RTL/Arabic content")
                        else:
                            safe_print(f"      📝 {html_file}: LTR content")
                    except Exception as e:
                        safe_print(f"      ❌ {html_file}: Error reading ({e})")
        
        return True
    else:
        safe_print("❌ No newsletters directory found")
        return False

def check_server_status():
    """Check if the Flask server is running."""
    safe_print("\n🔍 Checking Server Status")
    safe_print("=" * 25)
    
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            safe_print("✅ Flask server is running")
            return True
        else:
            safe_print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        safe_print("❌ Flask server is not running")
        safe_print("💡 Start with: python scripts/generate_newsletter.py")
        return False
    except Exception as e:
        safe_print(f"❌ Server check failed: {e}")
        return False

def main():
    """Run the Arabic newsletter test."""
    safe_print("🧪 Direct Arabic Newsletter Generation Test")
    safe_print("=" * 45)
    
    # Check server status first
    server_running = check_server_status()
    
    # Check existing newsletters
    existing_newsletters = test_existing_newsletters()
    
    if server_running:
        # Test API-based generation
        api_test_result = test_arabic_newsletter_via_api()
    else:
        safe_print("\n⚠️  Skipping API test - server not running")
        api_test_result = False
    
    # Summary
    safe_print("\n" + "=" * 45)
    safe_print("📋 Test Summary:")
    safe_print(f"   {'✅' if server_running else '❌'} Server Status")
    safe_print(f"   {'✅' if existing_newsletters else '❌'} Existing Newsletters")
    safe_print(f"   {'✅' if api_test_result else '❌'} Arabic API Generation")
    
    if api_test_result:
        safe_print("\n🎉 Arabic newsletter generation is working!")
        safe_print("✅ RTL support is properly implemented")
        safe_print("🌍 System is ready for Arabic content")
    elif server_running and not api_test_result:
        safe_print("\n🔧 Arabic newsletter generation needs attention")
        safe_print("💡 Check the API response and server logs")
    else:
        safe_print("\n💡 Start the Flask server to test Arabic generation")
    
    safe_print("=" * 45)
    
    return api_test_result

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
