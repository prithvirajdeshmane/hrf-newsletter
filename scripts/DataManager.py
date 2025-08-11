import json
from pathlib import Path

PATH = Path("data/country_languages.json")

class DataManager:
    """
    Handles loading and accessing country-language data from a JSON file using pathlib.Path for robust path management.
    """
    def __init__(self, file_path: Path = PATH) -> None:
        """
        Initialize DataManager with the path to the data file.
        Args:
            file_path (Path): Path to the JSON data file.
        """
        self.path = file_path

    def get_countries(self) -> dict:
        """
        Load and return the country-language data from the JSON file.
        Returns:
            dict: Dictionary mapping countries to their languages.
        """
        with self.path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return list(data.keys())