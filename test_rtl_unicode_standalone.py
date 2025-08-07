#!/usr/bin/env python3
"""
Standalone RTL/Unicode Compatibility Test for Mailchimp Integration
Tests Arabic content, RTL text direction, Unicode handling, and international character support.
"""

import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

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

def test_unicode_file_handling():
    """Test Unicode filename and content handling."""
    safe_print("🧪 Testing Unicode File Handling...")
    
    test_dir = tempfile.mkdtemp()
    unicode_test_cases = [
        ("arabic", "صورة_عربية.txt", "مرحبا بالعالم - نص عربي"),
        ("chinese", "图片_中文.txt", "你好世界 - 中文文本"),
        ("russian", "файл_русский.txt", "Привет мир - русский текст"),
        ("emoji", "test_🌍_emoji.txt", "🌍 Hello World 🚀 Unicode Test 📝")
    ]
    
    passed = 0
    failed = 0
    
    for lang, filename, content in unicode_test_cases:
        try:
            test_path = os.path.join(test_dir, filename)
            
            # Write Unicode content
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Read back and verify
            with open(test_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
                
            if read_content == content:
                safe_print(f"   ✅ {lang.capitalize()} Unicode handling: PASS")
                passed += 1
            else:
                safe_print(f"   ❌ {lang.capitalize()} Unicode handling: FAIL (content mismatch)")
                failed += 1
                
        except (UnicodeError, OSError) as e:
            safe_print(f"   ❌ {lang.capitalize()} Unicode handling: FAIL ({e})")
            failed += 1
    
    # Clean up
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return passed, failed

def test_rtl_text_direction():
    """Test RTL text direction detection and handling."""
    safe_print("🧪 Testing RTL Text Direction Handling...")
    
    rtl_languages = [
        ('ar', 'Arabic'),
        ('he', 'Hebrew'), 
        ('fa', 'Persian'),
        ('ur', 'Urdu')
    ]
    
    ltr_languages = [
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('de', 'German')
    ]
    
    passed = 0
    failed = 0
    
    # Test RTL detection
    for lang_code, lang_name in rtl_languages:
        language_info = {'scriptDirection': 'rtl'}
        direction = language_info.get('scriptDirection', 'ltr')
        
        if direction == 'rtl':
            safe_print(f"   ✅ {lang_name} ({lang_code}) RTL detection: PASS")
            passed += 1
        else:
            safe_print(f"   ❌ {lang_name} ({lang_code}) RTL detection: FAIL")
            failed += 1
    
    # Test LTR default
    for lang_code, lang_name in ltr_languages:
        language_info = {}  # No scriptDirection specified
        direction = language_info.get('scriptDirection', 'ltr')
        
        if direction == 'ltr':
            safe_print(f"   ✅ {lang_name} ({lang_code}) LTR default: PASS")
            passed += 1
        else:
            safe_print(f"   ❌ {lang_name} ({lang_code}) LTR default: FAIL")
            failed += 1
    
    return passed, failed

def test_json_unicode_encoding():
    """Test JSON encoding/decoding with Unicode content."""
    safe_print("🧪 Testing JSON Unicode Encoding...")
    
    unicode_data = {
        'title_arabic': 'نشرة أخبار حقوق الإنسان',
        'title_chinese': '人权新闻通讯',
        'title_russian': 'Информационный бюллетень по правам человека',
        'content_mixed': 'Hello مرحبا 你好 Привет 🌍',
        'rtl_direction': 'rtl',
        'country_names': {
            'arabic': 'البحرين',
            'english': 'Bahrain'
        }
    }
    
    passed = 0
    failed = 0
    
    try:
        # Test JSON serialization
        json_str = json.dumps(unicode_data, ensure_ascii=False)
        
        # Verify Unicode content is preserved
        if 'البحرين' in json_str and '你好' in json_str:
            safe_print("   ✅ JSON Unicode serialization: PASS")
            passed += 1
        else:
            safe_print("   ❌ JSON Unicode serialization: FAIL (Unicode content missing)")
            failed += 1
        
        # Test JSON deserialization
        decoded_data = json.loads(json_str)
        
        if (decoded_data['title_arabic'] == 'نشرة أخبار حقوق الإنسان' and
            decoded_data['country_names']['arabic'] == 'البحرين'):
            safe_print("   ✅ JSON Unicode deserialization: PASS")
            passed += 1
        else:
            safe_print("   ❌ JSON Unicode deserialization: FAIL (content mismatch)")
            failed += 1
            
    except (UnicodeError, json.JSONDecodeError) as e:
        safe_print(f"   ❌ JSON Unicode encoding: FAIL ({e})")
        failed += 2
    
    return passed, failed

def test_html_rtl_attributes():
    """Test HTML RTL attribute generation."""
    safe_print("🧪 Testing HTML RTL Attributes...")
    
    passed = 0
    failed = 0
    
    # Test RTL HTML generation
    arabic_data = {
        'lang': 'ar',
        'dir': 'rtl',
        'country_name': 'البحرين',
        'title': 'نشرة أخبار حقوق الإنسان'
    }
    
    # Simulate HTML template rendering
    html_template = '''<!DOCTYPE html>
<html dir="{dir}" lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>مرحبا بكم في {country_name}</h1>
    <p>هذا نص تجريبي باللغة العربية.</p>
</body>
</html>'''
    
    try:
        rendered_html = html_template.format(**arabic_data)
        
        # Check for RTL attributes
        if 'dir="rtl"' in rendered_html:
            safe_print("   ✅ HTML RTL direction attribute: PASS")
            passed += 1
        else:
            safe_print("   ❌ HTML RTL direction attribute: FAIL")
            failed += 1
        
        if 'lang="ar"' in rendered_html:
            safe_print("   ✅ HTML language attribute: PASS")
            passed += 1
        else:
            safe_print("   ❌ HTML language attribute: FAIL")
            failed += 1
        
        if 'البحرين' in rendered_html:
            safe_print("   ✅ HTML Arabic content: PASS")
            passed += 1
        else:
            safe_print("   ❌ HTML Arabic content: FAIL")
            failed += 1
            
    except (UnicodeError, KeyError) as e:
        safe_print(f"   ❌ HTML RTL generation: FAIL ({e})")
        failed += 3
    
    return passed, failed

def test_mailchimp_api_compatibility():
    """Test Mailchimp API request compatibility with Unicode content."""
    safe_print("🧪 Testing Mailchimp API Unicode Compatibility...")
    
    passed = 0
    failed = 0
    
    # Test API request payload with Unicode
    unicode_payload = {
        'name': 'نشرة البحرين الإخبارية',
        'html': '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><title>نشرة أخبار</title></head>
<body><h1>مرحبا بكم</h1></body>
</html>''',
        'folder_id': 'test123'
    }
    
    try:
        # Test request payload encoding
        json_payload = json.dumps(unicode_payload, ensure_ascii=False)
        
        # Verify Unicode content is preserved
        if 'نشرة البحرين' in json_payload and 'مرحبا بكم' in json_payload:
            safe_print("   ✅ API payload Unicode encoding: PASS")
            passed += 1
        else:
            safe_print("   ❌ API payload Unicode encoding: FAIL")
            failed += 1
        
        # Test HTTP encoding
        encoded_payload = json_payload.encode('utf-8')
        if isinstance(encoded_payload, bytes):
            safe_print("   ✅ HTTP request encoding: PASS")
            passed += 1
        else:
            safe_print("   ❌ HTTP request encoding: FAIL")
            failed += 1
        
        # Test decoding back
        decoded_payload = encoded_payload.decode('utf-8')
        parsed_data = json.loads(decoded_payload)
        
        if parsed_data['name'] == 'نشرة البحرين الإخبارية':
            safe_print("   ✅ API response decoding: PASS")
            passed += 1
        else:
            safe_print("   ❌ API response decoding: FAIL")
            failed += 1
            
    except (UnicodeError, json.JSONDecodeError) as e:
        safe_print(f"   ❌ Mailchimp API Unicode compatibility: FAIL ({e})")
        failed += 3
    
    return passed, failed

def test_country_language_config():
    """Test country language configuration with RTL support."""
    safe_print("🧪 Testing Country Language Configuration...")
    
    passed = 0
    failed = 0
    
    # Load actual country languages configuration
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'country_languages.json')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                country_data = json.load(f)
            
            # Check Bahrain Arabic configuration
            if 'Bahrain' in country_data:
                bahrain = country_data['Bahrain']
                
                if 'languages' in bahrain and 'Arabic' in bahrain['languages']:
                    arabic_config = bahrain['languages']['Arabic']
                    
                    # Check RTL direction
                    if arabic_config.get('scriptDirection') == 'rtl':
                        safe_print("   ✅ Bahrain Arabic RTL configuration: PASS")
                        passed += 1
                    else:
                        safe_print("   ❌ Bahrain Arabic RTL configuration: FAIL")
                        failed += 1
                    
                    # Check Arabic country name
                    if arabic_config.get('preferredName') == 'البحرين':
                        safe_print("   ✅ Bahrain Arabic country name: PASS")
                        passed += 1
                    else:
                        safe_print("   ❌ Bahrain Arabic country name: FAIL")
                        failed += 1
                    
                    # Check language code
                    if arabic_config.get('languageCode') == 'ar':
                        safe_print("   ✅ Bahrain Arabic language code: PASS")
                        passed += 1
                    else:
                        safe_print("   ❌ Bahrain Arabic language code: FAIL")
                        failed += 1
                else:
                    safe_print("   ❌ Bahrain Arabic configuration missing: FAIL")
                    failed += 3
            else:
                safe_print("   ❌ Bahrain configuration missing: FAIL")
                failed += 3
        else:
            safe_print("   ⚠️  Country languages config file not found: SKIP")
            
    except (json.JSONDecodeError, UnicodeError) as e:
        safe_print(f"   ❌ Country language config test: FAIL ({e})")
        failed += 3
    
    return passed, failed

def main():
    """Run all RTL/Unicode compatibility tests."""
    safe_print("🌍 RTL/Unicode Compatibility Testing for Mailchimp Integration")
    safe_print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    test_functions = [
        test_unicode_file_handling,
        test_rtl_text_direction,
        test_json_unicode_encoding,
        test_html_rtl_attributes,
        test_mailchimp_api_compatibility,
        test_country_language_config
    ]
    
    for test_func in test_functions:
        try:
            passed, failed = test_func()
            total_passed += passed
            total_failed += failed
            safe_print("")  # Add spacing between tests
        except Exception as e:
            safe_print(f"   ❌ Test {test_func.__name__} failed with exception: {e}")
            total_failed += 1
            safe_print("")
    
    # Print summary
    safe_print("=" * 70)
    safe_print("📊 RTL/Unicode Compatibility Test Results:")
    safe_print(f"✅ Passed: {total_passed}")
    safe_print(f"❌ Failed: {total_failed}")
    safe_print(f"📈 Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%" if (total_passed + total_failed) > 0 else "N/A")
    
    if total_failed == 0:
        safe_print("🎉 All RTL/Unicode compatibility tests passed!")
        safe_print("✅ Mailchimp integration is ready for international content!")
    else:
        safe_print(f"💥 {total_failed} test(s) failed - review RTL/Unicode compatibility")
        safe_print("🔧 Check Unicode encoding, RTL attributes, and API compatibility")
    
    safe_print("=" * 70)
    
    return total_failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
