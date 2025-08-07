#!/usr/bin/env python3
"""Test script to check if all imports work correctly."""

import sys
import traceback

def test_import(module_name, from_module=None):
    """Test importing a module and report success/failure."""
    try:
        if from_module:
            exec(f"from {from_module} import {module_name}")
            print(f"[OK] Successfully imported {module_name} from {from_module}")
        else:
            exec(f"import {module_name}")
            print(f"[OK] Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import {module_name}: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False

def main():
    print("Testing imports for newsletter generator...")
    print("=" * 50)
    
    # Test standard library imports
    standard_imports = [
        'os', 'json', 'sys', 'webbrowser', 'threading', 'copy', 're', 'shutil'
    ]
    
    for module in standard_imports:
        test_import(module)
    
    # Test datetime
    test_import('datetime', 'datetime')
    
    # Test third-party imports
    third_party = [
        ('Environment, FileSystemLoader', 'jinja2'),
        ('Flask, request, jsonify, send_from_directory', 'flask'),
        ('load_dotenv, set_key', 'dotenv'),
        ('Translator', 'googletrans'),
        ('urlparse', 'urllib.parse'),
        ('requests', None)
    ]
    
    for import_items, from_module in third_party:
        if from_module:
            test_import(import_items, from_module)
        else:
            test_import(import_items)
    
    print("\n" + "=" * 50)
    print("Testing local module imports...")
    
    # Test local imports
    local_imports = [
        ('upload_template_to_mailchimp, MailchimpUploadError', 'mailchimp_template_upload'),
        ('upload_image_to_mailchimp, MailchimpImageUploadError', 'mailchimp_image_upload'),
        ('compress_image_if_needed', 'image_utils')
    ]
    
    for import_items, from_module in local_imports:
        test_import(import_items, from_module)
    
    print("\n" + "=" * 50)
    print("Import testing complete!")

if __name__ == '__main__':
    main()
