import json
from pathlib import Path

PATH = Path("data/country_languages.json")

class DataManager:
    """
    Manages loading and accessing country-language data from a JSON file.

    This class implements a singleton pattern for data loading, where data is
    read from the specified JSON file once upon initialization and cached in
    memory. This prevents redundant file I/O on subsequent data requests.
    It includes error handling for missing files or malformed JSON.

    Attributes:
        path (Path): The file path to the country-language JSON data source.
        _data (dict | None): Cached data loaded from the JSON file. Private.
    """
    def __init__(self, file_path: Path = PATH) -> None:
        """
        Initializes the DataManager and triggers the initial data load.

        Args:
            file_path (Path): Path to the JSON data file. Defaults to the
                              statically defined PATH.
        """
        self.path = file_path
        self._data: dict | None = None
        self._load_data()

    def _load_data(self) -> None:
        """
        Loads data from the JSON file into the instance's private _data attribute.

        Handles potential FileNotFoundError and json.JSONDecodeError, setting
        _data to an empty dictionary in case of an error to ensure stability.
        Logs an error message to standard error upon failure.
        """
        try:
            with self.path.open('r', encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Data file not found at {self.path}")
            self._data = {}
        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from {self.path}")
            self._data = {}

    def get_countries(self) -> dict:
        """
        Returns the cached dictionary of country-language data.

        If the data has not been loaded successfully, it returns an empty dict.

        Returns:
            dict: A dictionary mapping countries to their languages.
        """
        return self._data if self._data is not None else {}

    def refresh_data(self) -> None:
        """
        Forces a reload of the data from the source file.
        """
        print("Refreshing country-language data...")
        self._load_data()