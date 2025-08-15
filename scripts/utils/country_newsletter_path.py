"""
CountryNewsletterPath utility class for all country-specific newsletter path logic.
Encapsulates slugification and folder/file path generation for maintainability and OOP compliance.
"""
from pathlib import Path
from typing import Optional
import re
from config import GENERATED_NEWSLETTERS_DIR

class CountryNewsletterPath:
    """
    Handles all file and folder path logic for a given country in the newsletter system.
    Ensures all paths are slugified and consistent.
    """
    def __init__(self, country: str):
        self.country = country
        self.slug = self._slugify(country)

    def newsletter_dir(self) -> Path:
        """Returns the Path to the country's newsletter folder (slugified)."""
        return Path(GENERATED_NEWSLETTERS_DIR) / self.slug

    def mailchimp_dir(self) -> Path:
        """Returns the Path to the country's Mailchimp versions folder."""
        return self.newsletter_dir() / "mailchimp_versions"

    def newsletter_file(self, filename: str) -> Path:
        """Returns the Path to a specific newsletter file in the country folder."""
        return self.newsletter_dir() / filename

    def ensure_newsletter_dir(self) -> Path:
        """Creates the newsletter directory if it doesn't exist and returns the Path."""
        dir_path = self.newsletter_dir()
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_newsletter_filename(self, language_name: str, timestamp: str) -> str:
        """Generate newsletter filename with readable format."""
        from datetime import datetime
        
        # Convert timestamp to readable format (e.g., Aug08_1427)
        dt = datetime.strptime(timestamp, "%m%d%y_%H%M%S")
        readable_timestamp = dt.strftime("%b%d_%H%M")
        
        # Use language name directly (already safe from JSON)
        safe_language = self._slugify(language_name)
        
        # Generate filename: Country_Language_MonthDay_Time.html
        filename = f"{self.slug}_{safe_language}_{readable_timestamp}.html"
        
        return filename

    def _slugify(self, text: str) -> str:
        """
        Convert a string into a URL- and filename-safe slug.
        Replaces spaces with underscores and removes invalid characters.
        """
        text = text.replace(' ', '_')
        return re.sub(r'[<>:"/\\|?*]', '_', text)

    def ensure_mailchimp_dir(self) -> Path:
        """Creates the mailchimp_versions directory if it doesn't exist and returns the Path."""
        dir_path = self.mailchimp_dir()
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
