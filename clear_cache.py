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
    
    print("🧹 Clearing Python bytecode cache...")
    
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
    
    print("🌶️  Clearing Flask cache...")
    
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
        response = input("🗂️  Clear generated newsletters? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("   Skipping generated newsletters cleanup.")
            return 0
    
    print("🗂️  Clearing generated newsletters...")
    
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


def show_browser_cache_instructions() -> None:
    """Display instructions for clearing browser cache."""
    print("\n🌐 Browser Cache Instructions:")
    print("   • Hard refresh: Ctrl + F5 or Ctrl + Shift + R")
    print("   • Clear browser cache for localhost in browser settings")
    print("   • Or open Developer Tools (F12) → Network tab → check 'Disable cache'")


def main() -> None:
    """Main function to orchestrate cache clearing."""
    print("=" * 60)
    print("🧹 HRF Newsletter Generator - Cache Clearing Utility")
    print("=" * 60)
    
    total_removed = 0
    
    # Clear Python cache
    python_cache_removed = clear_python_cache()
    total_removed += python_cache_removed
    
    # Clear Flask cache
    flask_cache_removed = clear_flask_cache()
    total_removed += flask_cache_removed
    
    # Optionally clear generated newsletters
    newsletters_removed = clear_generated_newsletters()
    total_removed += newsletters_removed
    
    # Show browser cache instructions
    show_browser_cache_instructions()
    
    print("\n" + "=" * 60)
    print(f"✅ Cache clearing complete! Removed {total_removed} items.")
    print("=" * 60)
    
    if total_removed > 0:
        print("\n💡 Recommendations:")
        print("   1. Restart your Flask application")
        print("   2. Hard refresh your browser (Ctrl + F5)")
        print("   3. Check if the issue is resolved")
    else:
        print("\n💡 No cache files found to remove.")
    
    print("\n🚀 Ready to run: python app.py")


if __name__ == "__main__":
    main()
