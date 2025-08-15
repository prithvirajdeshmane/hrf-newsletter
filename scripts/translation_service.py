"""
Google Translate API service for newsletter translation.

This module provides a class-based translation service that handles:
- Text translation using Google Cloud Translate API
- Translation caching to minimize API calls
- Retry mechanisms with fallback to original text
- Special character handling (©, accents, etc.)
- Country name localization using preferredName
- Batch translation optimization
"""

import os
import json
import time
import html
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import logging
from google.cloud import translate_v2 as translate
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsletterTranslationService:
    """
    Translation service for newsletter content using Google Cloud Translate API.
    
    Features:
    - Caches translations to avoid redundant API calls
    - Implements retry mechanism with exponential backoff
    - Handles special characters and encoding properly
    - Optimizes API usage through batching
    - Provides fallback to original text on failure
    """
    
    def __init__(self, project_id: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize the translation service.
        
        Args:
            project_id: Google Cloud project ID (optional, can be set via environment)
            credentials_path: Path to service account JSON file (optional, can be set via environment)
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Initialize translation client
        self._client = None
        self._initialize_client()
        
        # Cache for translations
        self.cache_dir = Path("cache/translations")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._translation_cache = self._load_cache()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        # Static text translations cache
        self._static_translations = {}
    
    def _initialize_client(self) -> None:
        """Initialize Google Translate client with proper authentication."""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            
            self._client = translate.Client()
            logger.info("Google Translate client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate client: {e}")
            self._client = None
    
    def _load_cache(self) -> Dict[str, str]:
        """Load translation cache from disk."""
        cache_file = self.cache_dir / "translation_cache.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load translation cache: {e}")
        return {}
    
    def _save_cache(self) -> None:
        """Save translation cache to disk."""
        cache_file = self.cache_dir / "translation_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save translation cache: {e}")
    
    def _generate_cache_key(self, text: str, target_language: str) -> str:
        """Generate a unique cache key for text and target language."""
        content = f"{text}|{target_language}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cached_translation(self, text: str, target_language: str) -> Optional[str]:
        """Get cached translation if available."""
        cache_key = self._generate_cache_key(text, target_language)
        return self._translation_cache.get(cache_key)
    
    def _cache_translation(self, text: str, target_language: str, translation: str) -> None:
        """Cache a translation."""
        cache_key = self._generate_cache_key(text, target_language)
        self._translation_cache[cache_key] = translation
        self._save_cache()
    
    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate a single text string with caching and retry logic.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'fr', 'de', 'es')
            
        Returns:
            Translated text or original text if translation fails
        """
        if not text or not text.strip():
            return text
        
        # Skip translation for English
        if target_language == 'en':
            return text
        
        # Check cache first
        cached = self._get_cached_translation(text, target_language)
        if cached:
            logger.debug(f"Using cached translation for: {text[:50]}...")
            return cached
        
        # Attempt translation with retry logic
        for attempt in range(self.max_retries):
            try:
                if not self._client:
                    logger.warning("Translation client not available, using original text")
                    return text
                
                result = self._client.translate(
                    text,
                    target_language=target_language,
                    source_language='en'
                )
                
                translated_text = result['translatedText']
                
                # Decode HTML entities from the translation
                translated_text = html.unescape(result['translatedText'])
                
                # Cache the successful translation
                self._cache_translation(text, target_language, translated_text)
                
                logger.debug(f"Translated '{text[:50]}...' to {target_language}")
                return translated_text
                
            except google_exceptions.GoogleAPIError as e:
                logger.warning(f"Google API error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Translation failed after {self.max_retries} attempts: {e}")
                    return text
            
            except Exception as e:
                logger.error(f"Unexpected error during translation: {e}")
                return text
        
        return text
    
    def _batch_translate(self, texts: List[str], target_language: str) -> List[str]:
        """
        Translate multiple texts in a single API call for efficiency.
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            
        Returns:
            List of translated texts in the same order
        """
        if not texts or target_language == 'en':
            return texts
        
        # Filter out empty texts and track their positions
        non_empty_texts = []
        text_positions = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                text_positions.append(i)
        
        if not non_empty_texts:
            return texts
        
        # Check cache for all texts
        cached_results = []
        texts_to_translate = []
        translate_positions = []
        
        for i, text in enumerate(non_empty_texts):
            cached = self._get_cached_translation(text, target_language)
            if cached:
                cached_results.append((text_positions[i], cached))
            else:
                texts_to_translate.append(text)
                translate_positions.append(text_positions[i])
        
        # Translate uncached texts
        if texts_to_translate and self._client:
            try:
                results = self._client.translate(
                    texts_to_translate,
                    target_language=target_language,
                    source_language='en'
                )
                
                # Handle both single result and list of results
                if not isinstance(results, list):
                    results = [results]
                
                for i, result in enumerate(results):
                    original_text = texts_to_translate[i]
                    translated_text = result['translatedText']
                    
                    # Decode HTML entities (e.g., &#39; -> ')
                    translated_text = html.unescape(translated_text)
                    
                    position = translate_positions[i]
                    
                    # Cache the translation
                    self._cache_translation(original_text, target_language, translated_text)
                    cached_results.append((position, translated_text))
                    
            except Exception as e:
                logger.error(f"Batch translation failed: {e}")
                # Fallback to original texts
                for i, text in enumerate(texts_to_translate):
                    position = translate_positions[i]
                    cached_results.append((position, text))
        
        # Reconstruct the result list
        result_texts = list(texts)
        for position, translated_text in cached_results:
            result_texts[position] = translated_text
        
        return result_texts
    
    def get_country_display_name(self, country_name: str, language_data: Dict[str, Any]) -> str:
        """
        Get the appropriate country display name for the target language.
        
        Args:
            country_name: Original country name
            language_data: Language information containing preferredName
            
        Returns:
            Country name in target language (preferredName if available, otherwise original)
        """
        preferred_name = language_data.get('preferredName', '').strip()
        return preferred_name if preferred_name else country_name
    
    def get_static_text_translations(self, target_language: str) -> Dict[str, str]:
        """
        Get translations for static template text.
        
        Args:
            target_language: Target language code
            
        Returns:
            Dictionary of translated static texts
        """
        if target_language == 'en':
            return {
                'learn_more': 'Learn more',
                'read_story': 'Read Story',
                'footer_copyright': '© 2025 Human Rights Foundation. All rights reserved.'
            }
        
        # Check if we have cached static translations for this language
        cache_key = f"static_{target_language}"
        if cache_key in self._static_translations:
            return self._static_translations[cache_key]
        
        # Translate static texts
        static_texts = {
            'learn_more': self.translate_text('Learn more', target_language),
            'read_story': self.translate_text('Read Story', target_language),
            'footer_copyright': self.translate_text('© 2025 Human Rights Foundation. All rights reserved.', target_language)
        }
        
        # Cache the static translations
        self._static_translations[cache_key] = static_texts
        
        return static_texts
    
    def translate_newsletter_content(self, content: Dict[str, Any], target_language: str, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate all newsletter content for a specific language.
        
        Args:
            content: Newsletter content dictionary
            target_language: Target language code
            country_data: Country and language information
            
        Returns:
            Translated content dictionary
        """
        if target_language == 'en':
            return content
        
        logger.info(f"Translating newsletter content to {target_language}")
        
        # Create a copy to avoid modifying the original
        translated_content = content.copy()
        
        # Get static text translations
        static_translations = self.get_static_text_translations(target_language)
        
        # Translate hero content
        if 'hero' in translated_content:
            hero = translated_content['hero']
            if isinstance(hero, dict):
                # Collect texts for batch translation
                hero_texts = []
                hero_keys = []
                
                for key in ['image_alt', 'headline', 'description']:
                    if key in hero and hero[key]:
                        hero_texts.append(hero[key])
                        hero_keys.append(key)
                
                # Batch translate hero texts
                if hero_texts:
                    translated_hero_texts = self._batch_translate(hero_texts, target_language)
                    for i, key in enumerate(hero_keys):
                        hero[key] = translated_hero_texts[i]
                
                # Update static link text
                hero['link_text'] = static_translations['learn_more']
        
        # Translate stories
        if 'stories' in translated_content and isinstance(translated_content['stories'], list):
            for story in translated_content['stories']:
                if isinstance(story, dict):
                    # Collect texts for batch translation
                    story_texts = []
                    story_keys = []
                    
                    for key in ['image_alt', 'headline', 'description']:
                        if key in story and story[key]:
                            story_texts.append(story[key])
                            story_keys.append(key)
                    
                    # Batch translate story texts
                    if story_texts:
                        translated_story_texts = self._batch_translate(story_texts, target_language)
                        for i, key in enumerate(story_keys):
                            story[key] = translated_story_texts[i]
                    
                    # Translate CTA if present
                    if 'cta' in story and isinstance(story['cta'], dict):
                        cta_text = story['cta'].get('text', '')
                        if cta_text:
                            story['cta']['text'] = self.translate_text(cta_text, target_language)
                    
                    # Update static link text (Read Story)
                    story['link_text'] = static_translations['read_story']
        
        # Translate CTAs
        if 'ctas' in translated_content and isinstance(translated_content['ctas'], list):
            for cta in translated_content['ctas']:
                if isinstance(cta, dict) and 'text' in cta:
                    cta['text'] = self.translate_text(cta['text'], target_language)
        
        # Add static translations to content
        translated_content['static_translations'] = static_translations
        
        # Get country display name using the correct language key
        languages_dict = country_data.get('languages', {})
        
        # Find the language data by matching language code
        language_info = {}
        for lang_name, lang_data in languages_dict.items():
            if lang_data.get('languageCode') == target_language:
                language_info = lang_data
                break
        
        translated_content['country_display_name'] = self.get_country_display_name(
            content.get('country', ''), language_info
        )
        
        logger.info(f"Successfully translated newsletter content to {target_language}")
        return translated_content
    
    def is_available(self) -> bool:
        """Check if the translation service is available and properly configured."""
        return self._client is not None
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages from Google Translate.
        
        Returns:
            List of language dictionaries with 'language' and 'name' keys
        """
        if not self._client:
            return []
        
        try:
            languages = self._client.get_languages()
            return languages
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
