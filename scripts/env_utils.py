"""
Utility functions for managing Mailchimp credentials in a .env file.
"""
from pathlib import Path
from typing import Tuple

def env_file_path() -> Path:
    """Return the Path to the .env file in the project root."""
    return Path(__file__).parent.parent / ".env"

def credentials_present() -> bool:
    """
    Check if .env exists and contains non-empty MAILCHIMP_API_KEY and MAILCHIMP_SERVER_PREFIX.
    Returns:
        bool: True if both credentials are present and non-empty.
    """
    path = env_file_path()
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    creds = {"MAILCHIMP_API_KEY": None, "MAILCHIMP_SERVER_PREFIX": None}
    for line in lines:
        if line.strip().startswith("MAILCHIMP_API_KEY="):
            creds["MAILCHIMP_API_KEY"] = line.split("=", 1)[1].strip()
        if line.strip().startswith("MAILCHIMP_SERVER_PREFIX="):
            creds["MAILCHIMP_SERVER_PREFIX"] = line.split("=", 1)[1].strip()
    return all(creds[k] for k in creds)

def save_credentials(api_key: str, server_prefix: str) -> None:
    """
    Save Mailchimp credentials to the .env file, creating or updating as needed.
    Args:
        api_key (str): Mailchimp API key
        server_prefix (str): Mailchimp server prefix
    """
    path = env_file_path()
    lines = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    # Remove any existing credential lines
    lines = [line for line in lines if not (line.strip().startswith("MAILCHIMP_API_KEY=") or line.strip().startswith("MAILCHIMP_SERVER_PREFIX="))]
    lines.append(f"MAILCHIMP_API_KEY={api_key}")
    lines.append(f"MAILCHIMP_SERVER_PREFIX={server_prefix}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
