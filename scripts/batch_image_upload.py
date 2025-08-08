#!/usr/bin/env python3
"""
Optimized Batch Image Upload System for Mailchimp Integration

This module provides a comprehensive solution for uploading multiple images to Mailchimp
with guaranteed 1MB size compliance, parallel processing, retry logic, and progress tracking.
"""

import os
import asyncio
import logging
import hashlib
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Import our enhanced image utilities
from image_utils import ensure_under_1mb, validate_mailchimp_size_limit, CriticalImageError, ImageCompressionError
from mailchimp_image_upload import upload_image_to_mailchimp, MailchimpImageUploadError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class ImageAsset:
    """Represents an image asset with metadata for processing."""
    source_path: str
    usage_context: str = 'inline'  # hero, inline, thumbnail, footer
    priority: str = 'normal'       # critical, important, normal, optional
    content_hash: Optional[str] = None
    original_reference: Optional[str] = None
    optimized_path: Optional[str] = None
    cached_url: Optional[str] = None
    
    def __post_init__(self):
        if self.content_hash is None:
            self.content_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate content hash for deduplication."""
        if not os.path.exists(self.source_path):
            return ""
        
        hash_md5 = hashlib.md5()
        with open(self.source_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

@dataclass
class UploadResult:
    """Result of an image upload operation."""
    image_asset: ImageAsset
    hosted_url: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    from_cache: bool = False
    skipped: bool = False
    upload_time_seconds: float = 0.0
    file_size_mb: float = 0.0

@dataclass
class BatchUploadSummary:
    """Summary of batch upload operation."""
    total_images: int = 0
    successful_uploads: int = 0
    cached_hits: int = 0
    failed_uploads: int = 0
    skipped_images: int = 0
    total_time_seconds: float = 0.0
    total_size_mb: float = 0.0
    url_mappings: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

class ImageUploadCache:
    """Manages caching of uploaded images to avoid duplicates."""
    
    def __init__(self, cache_file: str = "image_upload_cache.json"):
        self.cache_file = cache_file
        self.memory_cache = {}
        self.persistent_cache = self._load_cache_from_disk()
    
    def _load_cache_from_disk(self) -> Dict[str, str]:
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load cache from disk: {e}")
        return {}
    
    def _save_cache_to_disk(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.persistent_cache, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save cache to disk: {e}")
    
    def get_cached_url(self, content_hash: str) -> Optional[str]:
        """Get cached URL for content hash."""
        # Check memory first, then disk
        if content_hash in self.memory_cache:
            return self.memory_cache[content_hash]
        return self.persistent_cache.get(content_hash)
    
    def cache_upload(self, content_hash: str, mailchimp_url: str):
        """Cache an upload result."""
        self.memory_cache[content_hash] = mailchimp_url
        self.persistent_cache[content_hash] = mailchimp_url
        self._save_cache_to_disk()

class ProgressTracker:
    """Tracks progress of batch upload operations."""
    
    def __init__(self, total_images: int):
        self.total = total_images
        self.completed = 0
        self.failed = 0
        self.cached = 0
        self.skipped = 0
        self.current_operations = {}
        self.start_time = time.time()
    
    def update_status(self, image_asset: ImageAsset, status: str):
        """Update status for an image."""
        self.current_operations[image_asset.source_path] = status
        logging.info(f"Progress: {status} - {os.path.basename(image_asset.source_path)}")
    
    def mark_complete(self, image_asset: ImageAsset, hosted_url: Optional[str] = None, from_cache: bool = False):
        """Mark an image as completed."""
        if from_cache:
            self.cached += 1
        else:
            self.completed += 1
        
        if image_asset.source_path in self.current_operations:
            del self.current_operations[image_asset.source_path]
    
    def mark_failed(self, image_asset: ImageAsset, error: str):
        """Mark an image as failed."""
        self.failed += 1
        if image_asset.source_path in self.current_operations:
            del self.current_operations[image_asset.source_path]
        logging.error(f"Upload failed: {os.path.basename(image_asset.source_path)} - {error}")
    
    def mark_skipped(self, image_asset: ImageAsset, reason: str):
        """Mark an image as skipped."""
        self.skipped += 1
        if image_asset.source_path in self.current_operations:
            del self.current_operations[image_asset.source_path]
        logging.warning(f"Upload skipped: {os.path.basename(image_asset.source_path)} - {reason}")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        elapsed_time = time.time() - self.start_time
        processed = self.completed + self.failed + self.cached + self.skipped
        percentage = (processed / self.total * 100) if self.total > 0 else 0
        
        return {
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'cached': self.cached,
            'skipped': self.skipped,
            'percentage': percentage,
            'elapsed_time': elapsed_time,
            'current_operations': list(self.current_operations.values())
        }

class OptimizedImageUploader:
    """Main class for optimized batch image uploads to Mailchimp."""
    
    def __init__(self, max_concurrent_uploads: int = 5, max_retries: int = 3):
        self.max_concurrent_uploads = max_concurrent_uploads
        self.max_retries = max_retries
        self.upload_cache = ImageUploadCache()
        
        # Load environment variables
        load_dotenv()
        
        # Validate Mailchimp credentials
        self.api_key = os.getenv('MAILCHIMP_API_KEY')
        self.server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX')
        
        if not all([self.api_key, self.server_prefix]):
            raise ValueError("MAILCHIMP_API_KEY and MAILCHIMP_SERVER_PREFIX must be set in .env file")
    
    async def process_newsletter_images(self, image_paths: List[str], 
                                      usage_contexts: Optional[Dict[str, str]] = None,
                                      priorities: Optional[Dict[str, str]] = None,
                                      relative_path_mappings: Optional[Dict[str, str]] = None) -> BatchUploadSummary:
        """
        Main entry point for processing newsletter images.
        
        Args:
            image_paths: List of paths to images to upload
            usage_contexts: Optional mapping of image paths to usage contexts
            priorities: Optional mapping of image paths to priorities
            relative_path_mappings: Optional mapping of full paths to relative paths for URL replacement
            
        Returns:
            BatchUploadSummary with results of the operation
        """
        start_time = time.time()
        
        # Phase 1: Create image assets
        image_assets = []
        for path in image_paths:
            if os.path.exists(path):
                # Get relative path for URL mapping (if provided)
                relative_path = relative_path_mappings.get(path) if relative_path_mappings else None
                
                asset = ImageAsset(
                    source_path=path,
                    usage_context=usage_contexts.get(path, 'inline') if usage_contexts else 'inline',
                    priority=priorities.get(path, 'normal') if priorities else 'normal',
                    original_reference=relative_path
                )
                image_assets.append(asset)
            else:
                logging.warning(f"Image file not found: {path}")
        
        if not image_assets:
            logging.warning("No valid images found to process")
            return BatchUploadSummary()
        
        logging.info(f"Starting batch upload of {len(image_assets)} images")
        
        # Phase 2: Optimize and deduplicate
        optimized_assets = await self._optimize_and_deduplicate(image_assets)
        
        # Phase 3: Batch upload with progress tracking
        upload_results = await self._batch_upload_with_progress(optimized_assets)
        
        # Phase 4: Generate summary
        total_time = time.time() - start_time
        summary = self._generate_summary(upload_results, total_time)
        
        logging.info(f"Batch upload completed in {total_time:.2f}s: "
                    f"{summary.successful_uploads + summary.cached_hits}/{summary.total_images} successful")
        
        return summary
    
    async def _optimize_and_deduplicate(self, image_assets: List[ImageAsset]) -> List[ImageAsset]:
        """Optimize images and remove duplicates."""
        optimized_assets = []
        seen_hashes = set()
        
        # Sort by priority (critical first)
        priority_order = {'critical': 0, 'important': 1, 'normal': 2, 'optional': 3}
        image_assets.sort(key=lambda x: priority_order.get(x.priority, 2))
        
        for asset in image_assets:
            # Skip duplicates
            if asset.content_hash in seen_hashes:
                logging.info(f"Skipping duplicate: {os.path.basename(asset.source_path)}")
                continue
            
            seen_hashes.add(asset.content_hash)
            
            # Check cache first
            cached_url = self.upload_cache.get_cached_url(asset.content_hash)
            if cached_url:
                asset.cached_url = cached_url
                logging.info(f"Cache hit: {os.path.basename(asset.source_path)}")
                optimized_assets.append(asset)
                continue
            
            # Optimize for Mailchimp 1MB limit
            try:
                optimized_path = await asyncio.get_event_loop().run_in_executor(
                    None, ensure_under_1mb, asset.source_path
                )
                asset.optimized_path = optimized_path
                optimized_assets.append(asset)
                
            except CriticalImageError as e:
                logging.error(f"Cannot optimize {os.path.basename(asset.source_path)}: {e}")
                if asset.priority == 'critical':
                    # Critical images must be handled
                    raise e
                # Skip non-critical images that can't be optimized
                continue
            except Exception as e:
                logging.error(f"Optimization failed for {os.path.basename(asset.source_path)}: {e}")
                continue
        
        return optimized_assets
    
    async def _batch_upload_with_progress(self, optimized_assets: List[ImageAsset]) -> List[UploadResult]:
        """Upload images in parallel with progress tracking."""
        progress_tracker = ProgressTracker(len(optimized_assets))
        upload_results = []
        
        # Create semaphore to limit concurrent uploads
        semaphore = asyncio.Semaphore(self.max_concurrent_uploads)
        
        # Create upload tasks
        tasks = []
        for asset in optimized_assets:
            if asset.cached_url:
                # Handle cached assets immediately
                result = UploadResult(
                    image_asset=asset,
                    hosted_url=asset.cached_url,
                    success=True,
                    from_cache=True
                )
                upload_results.append(result)
                progress_tracker.mark_complete(asset, from_cache=True)
            else:
                # Create upload task
                task = asyncio.create_task(
                    self._upload_with_retry(asset, semaphore, progress_tracker)
                )
                tasks.append(task)
        
        # Wait for all uploads to complete
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_results:
                if isinstance(result, Exception):
                    logging.error(f"Upload task failed with exception: {result}")
                else:
                    upload_results.append(result)
        
        return upload_results
    
    async def _upload_with_retry(self, asset: ImageAsset, semaphore: asyncio.Semaphore, 
                               progress_tracker: ProgressTracker) -> UploadResult:
        """Upload single image with retry logic."""
        async with semaphore:
            for attempt in range(self.max_retries):
                try:
                    progress_tracker.update_status(asset, f"Uploading (attempt {attempt + 1})")
                    
                    # Validate size before upload (final safety check)
                    image_path = asset.optimized_path or asset.source_path
                    validate_mailchimp_size_limit(image_path)
                    
                    # Perform upload (run in thread pool to avoid blocking)
                    start_time = time.time()
                    hosted_url = await asyncio.get_event_loop().run_in_executor(
                        None, upload_image_to_mailchimp, image_path
                    )
                    upload_time = time.time() - start_time
                    
                    # Cache the result
                    self.upload_cache.cache_upload(asset.content_hash, hosted_url)
                    
                    # Create successful result
                    result = UploadResult(
                        image_asset=asset,
                        hosted_url=hosted_url,
                        success=True,
                        upload_time_seconds=upload_time,
                        file_size_mb=os.path.getsize(image_path) / (1024 * 1024)
                    )
                    
                    progress_tracker.mark_complete(asset, hosted_url)
                    return result
                    
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        progress_tracker.update_status(asset, f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        # Final attempt failed
                        error_msg = str(e)
                        progress_tracker.mark_failed(asset, error_msg)
                        
                        return UploadResult(
                            image_asset=asset,
                            success=False,
                            error=error_msg
                        )
    
    def _generate_summary(self, upload_results: List[UploadResult], total_time: float) -> BatchUploadSummary:
        """Generate summary of upload operation."""
        summary = BatchUploadSummary(
            total_images=len(upload_results),
            total_time_seconds=total_time
        )
        
        for result in upload_results:
            if result.success:
                if result.from_cache:
                    summary.cached_hits += 1
                else:
                    summary.successful_uploads += 1
                
                # Add to URL mappings
                if result.hosted_url:
                    summary.url_mappings[result.image_asset.source_path] = result.hosted_url
                    summary.url_mappings[result.image_asset.original_reference or result.image_asset.source_path] = result.hosted_url
                
                summary.total_size_mb += result.file_size_mb
                
            elif result.skipped:
                summary.skipped_images += 1
            else:
                summary.failed_uploads += 1
                if result.error:
                    summary.errors.append(f"{os.path.basename(result.image_asset.source_path)}: {result.error}")
        
        return summary

# Convenience functions for easy integration
async def upload_images_for_newsletter(image_paths: List[str], **kwargs) -> BatchUploadSummary:
    """Convenience function to upload images for newsletter generation."""
    uploader = OptimizedImageUploader()
    return await uploader.process_newsletter_images(image_paths, **kwargs)

def replace_image_urls_in_html(html_content: str, url_mappings: Dict[str, str]) -> str:
    """Replace local image URLs with Mailchimp URLs in HTML content."""
    updated_html = html_content
    
    for original_ref, mailchimp_url in url_mappings.items():
        # Handle different reference types
        if original_ref.startswith('data:image/'):
            # Base64 inline images
            updated_html = updated_html.replace(original_ref, mailchimp_url)
        elif original_ref.startswith('file://') or os.path.isabs(original_ref):
            # Absolute file paths
            updated_html = updated_html.replace(f'src="{original_ref}"', f'src="{mailchimp_url}"')
            updated_html = updated_html.replace(f"src='{original_ref}'", f"src='{mailchimp_url}'")
        else:
            # Relative paths
            updated_html = updated_html.replace(f'src="{original_ref}"', f'src="{mailchimp_url}"')
            updated_html = updated_html.replace(f"src='{original_ref}'", f"src='{mailchimp_url}'")
    
    return updated_html

if __name__ == '__main__':
    # Example usage
    async def test_batch_upload():
        # Create some test images (this would normally be your actual images)
        test_images = []
        
        # You would replace this with your actual image paths
        # test_images = ['path/to/hero.jpg', 'path/to/story1.jpg', 'path/to/footer.png']
        
        if test_images:
            uploader = OptimizedImageUploader()
            summary = await uploader.process_newsletter_images(test_images)
            
            print(f"Upload Summary:")
            print(f"  Total: {summary.total_images}")
            print(f"  Successful: {summary.successful_uploads}")
            print(f"  Cached: {summary.cached_hits}")
            print(f"  Failed: {summary.failed_uploads}")
            print(f"  Time: {summary.total_time_seconds:.2f}s")
            
            if summary.errors:
                print("Errors:")
                for error in summary.errors:
                    print(f"  - {error}")
        else:
            print("No test images specified. Add image paths to test the system.")
    
    # Run the test
    asyncio.run(test_batch_upload())
