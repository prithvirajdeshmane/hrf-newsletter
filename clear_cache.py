#!/usr/bin/env python3
"""
HRF Newsletter Generator - Cache Clearing Utility

This script clears various caches that might interfere with the Flask application:
- Python bytecode cache (.pyc files and __pycache__ directories)
- Flask temporary files
- Generated newsletter files (optional)
- Browser cache instructions

Usage: python clear_cache.py
"""

import os
import shutil
from pathlib import Path
from typing import List


def clear_python_cache() -> int:
    """
    Clear Python bytecode cache files and directories.
    
    Returns:
        int: Number of cache items removed
    """
    removed_count = 0
    project_root = Path(__file__).parent
    
    print("--- Clearing Python bytecode cache...")
    
    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            removed_count += 1
            print(f"   Removed: {pyc_file.relative_to(project_root)}")
        except Exception as e:
            print(f"   ⚠️  Failed to remove {pyc_file}: {e}")
    
    # Remove __pycache__ directories
    for pycache_dir in project_root.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            removed_count += 1
            print(f"   Removed directory: {pycache_dir.relative_to(project_root)}")
        except Exception as e:
            print(f"   ⚠️  Failed to remove {pycache_dir}: {e}")
    
    return removed_count


def clear_flask_cache() -> int:
    """
    Clear Flask-related cache and temporary files.
    
    Returns:
        int: Number of cache items removed
    """
    removed_count = 0
    project_root = Path(__file__).parent
    
    print("--- Clearing Flask cache...")
    
    # Common Flask cache directories
    cache_dirs = [
        project_root / "instance" / "cache",
        project_root / ".cache",
        project_root / "flask_session",
        project_root / ".flask_cache"
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                removed_count += 1
                print(f"   Removed directory: {cache_dir.relative_to(project_root)}")
            except Exception as e:
                print(f"   ⚠️  Failed to remove {cache_dir}: {e}")
    
    return removed_count


def clear_generated_newsletters(confirm: bool = False) -> int:
    """
    Clear generated newsletter files (optional with confirmation).
    
    Args:
        confirm: If True, clear without asking for confirmation
        
    Returns:
        int: Number of files removed
    """
    removed_count = 0
    project_root = Path(__file__).parent
    newsletters_dir = project_root / "generated_newsletters"
    
    if not newsletters_dir.exists():
        return 0
    
    if not confirm:
        response = input("--- Clear generated newsletters? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("   Skipping generated newsletters cleanup.")
            return 0
    
    print("--- Clearing generated newsletters...")
    
    try:
        # Count files before removal
        for file_path in newsletters_dir.rglob("*.html"):
            removed_count += 1
        
        shutil.rmtree(newsletters_dir)
        print(f"   Removed {removed_count} newsletter files")
    except Exception as e:
        print(f"   ⚠️  Failed to remove newsletters directory: {e}")
        removed_count = 0
    
    return removed_count


def clear_user_images() -> int:
    """
    Clear user-uploaded images from static/images/user-images directory.
    
    Returns:
        int: Number of files removed
    """
    removed_count = 0
    project_root = Path(__file__).parent
    user_images_dir = project_root / "static" / "images" / "user-images"
    
    if not user_images_dir.exists():
        return 0
    
    print("--- Clearing user-uploaded images...")
    
    try:
        # Count files before removal
        for file_path in user_images_dir.rglob("*"):
            if file_path.is_file():
                removed_count += 1
        
        shutil.rmtree(user_images_dir)
        print(f"   Removed {removed_count} user image files")
    except Exception as e:
        print(f"   ⚠️  Failed to remove user images directory: {e}")
        removed_count = 0
    
    return removed_count


def clear_translation_cache() -> int:
    """
    Clear the translation cache directory.

    Returns:
        int: Number of items removed (1 if directory is removed, 0 otherwise)
    """
    removed_count = 0
    project_root = Path(__file__).parent
    translation_cache_dir = project_root / "cache" / "translations"

    if not translation_cache_dir.exists():
        return 0

    print("--- Clearing translation cache...")

    try:
        shutil.rmtree(translation_cache_dir)
        removed_count = 1
        print(f"   Removed directory: {translation_cache_dir.relative_to(project_root)}")
    except Exception as e:
        print(f"   ⚠️  Failed to remove translation cache directory: {e}")

    return removed_count


def show_browser_cache_instructions() -> None:
    """Display instructions for clearing browser cache."""
    print("\n--- Browser Cache Instructions:")
    print("   • Hard refresh: Ctrl + F5 or Ctrl + Shift + R")
    print("   • Clear browser cache for your domain in browser settings")
    print("   • Or open Developer Tools (F12) → Network tab → check 'Disable cache'")


def main() -> None:
    """Main function to orchestrate cache clearing."""
    print("=" * 60)
    print("HRF Newsletter Generator - Cache Clearing Utility")
    print("=" * 60)
    
    total_removed = 0
    
    # Clear Python cache
    python_cache_removed = clear_python_cache()
    total_removed += python_cache_removed
    
    # Clear Flask cache
    flask_cache_removed = clear_flask_cache()
    total_removed += flask_cache_removed
    
    # Clear user-uploaded images
    user_images_removed = clear_user_images()
    total_removed += user_images_removed

    # Clear translation cache
    translation_cache_removed = clear_translation_cache()
    total_removed += translation_cache_removed
    
    # Optionally clear generated newsletters
    newsletters_removed = clear_generated_newsletters()
    total_removed += newsletters_removed
    
    # Show browser cache instructions
    show_browser_cache_instructions()
    
    print("\n" + "=" * 60)
    print(f"SUCCESS: Cache clearing complete! Removed {total_removed} items.")
    print("=" * 60)
    
    if total_removed > 0:
        print("\n[INFO] Recommendations:")
        print("   1. Restart your Flask application")
        print("   2. Hard refresh your browser (Ctrl + F5)")
        print("   3. Check if the issue is resolved")
    else:
        print("\n[INFO] No cache files found to remove.")
    
    print("\n--> Ready to run: python app.py")


if __name__ == "__main__":
    main()
