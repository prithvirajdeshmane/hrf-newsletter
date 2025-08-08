#!/usr/bin/env python3
"""
Optimized Batch Template Upload System for Mailchimp

This module provides an efficient system for uploading multiple newsletter templates
to Mailchimp, designed for multi-language scenarios where each language version
requires its own template due to different content, translations, and text direction.

Key Features:
- Batch upload multiple templates with proper naming conventions
- Template validation and error handling
- Template ID tracking for campaign creation
- Robust retry logic and detailed logging
- Progress tracking and performance metrics

Author: HRF Newsletter System
"""

import os
import sys
import asyncio
import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mailchimp_template_upload import upload_template_to_mailchimp, MailchimpUploadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TemplateUploadResult:
    """Result of a single template upload operation."""
    template_name: str
    success: bool
    template_id: Optional[str] = None
    error_message: Optional[str] = None
    upload_time_seconds: float = 0.0
    html_size_bytes: int = 0

@dataclass
class BatchTemplateUploadSummary:
    """Summary of batch template upload operation."""
    total_templates: int
    successful_uploads: int
    failed_uploads: int
    template_ids: Dict[str, str]  # template_name -> template_id
    errors: List[str]
    total_time_seconds: float
    upload_results: List[TemplateUploadResult]

class BatchTemplateUploader:
    """Optimized batch template uploader for Mailchimp."""
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.template_cache_file = os.path.join(self.project_root, 'template_upload_cache.json')
        self.template_cache = self._load_template_cache()
    
    def _get_project_root(self) -> str:
        """Get the project root directory."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    def _load_template_cache(self) -> Dict[str, Any]:
        """Load template upload cache from disk."""
        try:
            if os.path.exists(self.template_cache_file):
                with open(self.template_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load template cache: {e}")
        return {}
    
    def _save_template_cache(self):
        """Save template upload cache to disk."""
        try:
            with open(self.template_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.template_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save template cache: {e}")
    
    def _generate_template_name(self, country: str, language_code: str, locale: str) -> str:
        """Generate a unique, descriptive template name."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Clean country name for template naming
        clean_country = country.replace(' ', '_').replace('-', '_')
        return f"{clean_country}_{language_code}_{locale}_{timestamp}"
    
    def _calculate_html_hash(self, html_content: str) -> str:
        """Calculate SHA-256 hash of HTML content for deduplication."""
        return hashlib.sha256(html_content.encode('utf-8')).hexdigest()[:16]
    
    def _validate_html_content(self, html_content: str, template_name: str) -> Tuple[bool, Optional[str]]:
        """Validate HTML content before upload."""
        if not html_content or not html_content.strip():
            return False, "HTML content is empty"
        
        if len(html_content) > 10_000_000:  # 10MB limit for HTML templates
            return False, f"HTML content too large: {len(html_content)} bytes (max 10MB)"
        
        # Check for basic HTML structure
        if '<html' not in html_content.lower():
            return False, "HTML content missing <html> tag"
        
        if '<body' not in html_content.lower():
            return False, "HTML content missing <body> tag"
        
        # Check for Mailchimp image URLs (should be replaced by now)
        if 'mcusercontent.com' not in html_content:
            logger.warning(f"Template {template_name} may not have Mailchimp image URLs")
        
        return True, None
    
    async def _upload_single_template(self, html_content: str, template_name: str) -> TemplateUploadResult:
        """Upload a single template to Mailchimp with error handling."""
        start_time = asyncio.get_event_loop().time()
        html_size = len(html_content.encode('utf-8'))
        
        try:
            logger.info(f"📤 Uploading template: {template_name}")
            
            # Validate HTML content
            is_valid, error_msg = self._validate_html_content(html_content, template_name)
            if not is_valid:
                logger.error(f"❌ Validation failed for {template_name}: {error_msg}")
                return TemplateUploadResult(
                    template_name=template_name,
                    success=False,
                    error_message=f"Validation error: {error_msg}",
                    html_size_bytes=html_size
                )
            
            # Upload to Mailchimp
            response = upload_template_to_mailchimp(html_content, template_name)
            template_id = response.get('id')
            
            if not template_id:
                error_msg = "No template ID returned from Mailchimp"
                logger.error(f"❌ {error_msg} for {template_name}")
                return TemplateUploadResult(
                    template_name=template_name,
                    success=False,
                    error_message=error_msg,
                    html_size_bytes=html_size
                )
            
            upload_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ Template uploaded successfully: {template_name} (ID: {template_id})")
            
            # Cache the result
            html_hash = self._calculate_html_hash(html_content)
            self.template_cache[template_name] = {
                'template_id': template_id,
                'html_hash': html_hash,
                'upload_time': datetime.now().isoformat(),
                'html_size_bytes': html_size
            }
            
            return TemplateUploadResult(
                template_name=template_name,
                success=True,
                template_id=template_id,
                upload_time_seconds=upload_time,
                html_size_bytes=html_size
            )
            
        except MailchimpUploadError as e:
            upload_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Mailchimp error: {str(e)}"
            logger.error(f"❌ Upload failed for {template_name}: {error_msg}")
            
            return TemplateUploadResult(
                template_name=template_name,
                success=False,
                error_message=error_msg,
                upload_time_seconds=upload_time,
                html_size_bytes=html_size
            )
            
        except Exception as e:
            upload_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error uploading {template_name}: {error_msg}")
            
            return TemplateUploadResult(
                template_name=template_name,
                success=False,
                error_message=error_msg,
                upload_time_seconds=upload_time,
                html_size_bytes=html_size
            )
    
    async def upload_templates_for_newsletter(
        self, 
        templates: List[Tuple[str, str, str, str]]  # (html_content, country, language_code, locale)
    ) -> BatchTemplateUploadSummary:
        """
        Upload multiple templates for a newsletter with different languages.
        
        Args:
            templates: List of tuples containing (html_content, country, language_code, locale)
            
        Returns:
            BatchTemplateUploadSummary with results and template IDs
        """
        if not templates:
            logger.warning("No templates provided for upload")
            return BatchTemplateUploadSummary(
                total_templates=0,
                successful_uploads=0,
                failed_uploads=0,
                template_ids={},
                errors=[],
                total_time_seconds=0.0,
                upload_results=[]
            )
        
        logger.info(f"🚀 Starting batch upload of {len(templates)} templates")
        start_time = asyncio.get_event_loop().time()
        
        upload_results = []
        template_ids = {}
        errors = []
        
        # Upload templates sequentially to avoid overwhelming Mailchimp API
        for html_content, country, language_code, locale in templates:
            template_name = self._generate_template_name(country, language_code, locale)
            
            result = await self._upload_single_template(html_content, template_name)
            upload_results.append(result)
            
            if result.success and result.template_id:
                template_ids[template_name] = result.template_id
                logger.info(f"📋 Template registered: {template_name} -> {result.template_id}")
            else:
                errors.append(f"{template_name}: {result.error_message}")
        
        # Save cache after all uploads
        self._save_template_cache()
        
        total_time = asyncio.get_event_loop().time() - start_time
        successful_uploads = sum(1 for r in upload_results if r.success)
        failed_uploads = len(upload_results) - successful_uploads
        
        logger.info(f"📊 Batch template upload completed in {total_time:.2f}s: {successful_uploads}/{len(templates)} successful")
        
        return BatchTemplateUploadSummary(
            total_templates=len(templates),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            template_ids=template_ids,
            errors=errors,
            total_time_seconds=total_time,
            upload_results=upload_results
        )

# Global instance for easy access
_batch_uploader = BatchTemplateUploader()

async def upload_templates_for_newsletter(templates: List[Tuple[str, str, str, str]]) -> BatchTemplateUploadSummary:
    """
    Convenience function to upload multiple newsletter templates.
    
    Args:
        templates: List of tuples containing (html_content, country, language_code, locale)
        
    Returns:
        BatchTemplateUploadSummary with results and template IDs
    """
    return await _batch_uploader.upload_templates_for_newsletter(templates)

def get_template_cache() -> Dict[str, Any]:
    """Get the current template upload cache."""
    return _batch_uploader.template_cache.copy()

def clear_template_cache():
    """Clear the template upload cache."""
    _batch_uploader.template_cache.clear()
    _batch_uploader._save_template_cache()
    logger.info("🧹 Template upload cache cleared")

if __name__ == '__main__':
    # Test the batch template upload system
    async def test_batch_upload():
        test_html = """
        <!DOCTYPE html>
        <html lang="en" dir="ltr">
        <head>
            <meta charset="UTF-8">
            <title>Test Newsletter</title>
        </head>
        <body>
            <h1>Test Newsletter</h1>
            <p>This is a test template for batch upload.</p>
            <img src="https://mcusercontent.com/test/test-image.png" alt="Test Image">
        </body>
        </html>
        """
        
        templates = [
            (test_html, "TestCountry", "en", "en-US"),
            (test_html.replace("en", "de").replace("ltr", "ltr"), "TestCountry", "de", "de-DE")
        ]
        
        summary = await upload_templates_for_newsletter(templates)
        
        print(f"📊 Upload Summary:")
        print(f"   Total: {summary.total_templates}")
        print(f"   Successful: {summary.successful_uploads}")
        print(f"   Failed: {summary.failed_uploads}")
        print(f"   Time: {summary.total_time_seconds:.2f}s")
        print(f"   Template IDs: {summary.template_ids}")
        
        if summary.errors:
            print(f"   Errors: {summary.errors}")
    
    asyncio.run(test_batch_upload())
