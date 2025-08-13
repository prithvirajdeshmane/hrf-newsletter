"""
Utility functions for managing Mailchimp credentials in a .env file using the
`python-dotenv` library for robust and safe file operations.
"""
from dotenv import find_dotenv, get_key, set_key

# Find the .env file in the project root. The path is loaded once and reused.
env_path = find_dotenv()

def credentials_present() -> bool:
    """
    Checks if Mailchimp credentials exist and are non-empty in the .env file.

    This function leverages `dotenv.get_key` to safely read the values.

    Returns:
        bool: True if both MAILCHIMP_API_KEY and MAILCHIMP_SERVER_PREFIX are
              present and have non-empty values, False otherwise.
    """
    # If the .env file doesn't exist, find_dotenv() returns an empty string.
    if not env_path:
        return False

    api_key = get_key(env_path, "MAILCHIMP_API_KEY")
    server_prefix = get_key(env_path, "MAILCHIMP_SERVER_PREFIX")

    return bool(api_key and server_prefix)

def save_credentials(api_key: str, server_prefix: str) -> None:
    """
    Saves or updates Mailchimp credentials in the .env file.

    This function uses `dotenv.set_key` to safely write the key-value pairs,
    creating the file if it doesn't exist and preserving other existing values.

    Args:
        api_key (str): The Mailchimp API key to save.
        server_prefix (str): The Mailchimp server prefix (e.g., 'us21') to save.
    """
    # If .env doesn't exist, find_dotenv() returns '' but set_key needs a path.
    # We'll default to creating a '.env' file in the current dir's parent.
    path = env_path or find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True) or '.env'

    set_key(path, "MAILCHIMP_API_KEY", api_key)
    set_key(path, "MAILCHIMP_SERVER_PREFIX", server_prefix)
