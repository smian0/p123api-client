"""
Configuration settings for the P123 API client.
Uses pydantic BaseSettings for automatic environment variable loading.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self, env_file: str | None = None, testing: bool = False):
        """Initialize settings from .env file

        Args:
            env_file: Optional path to .env file
            testing: If True, will look for .env.test in tests directory
        """
        if testing:
            # Look for test env file in project root
            package_root = Path(__file__).parent.parent.parent.parent
            env_path = package_root / ".env.test"
        elif env_file:
            env_path = Path(env_file)
        else:
            # Look for .env in package root
            package_root = Path(__file__).parent.parent.parent
            env_path = package_root / ".env"

        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found at {env_path}")

        load_dotenv(env_path)

        # Load required settings
        self.api_id = os.getenv("P123_API_ID")
        if not self.api_id:
            raise ValueError("P123_API_ID environment variable is required")

        self.api_key = os.getenv("P123_API_KEY")
        if not self.api_key:
            raise ValueError("P123_API_KEY environment variable is required")

        # Load optional settings with defaults
        self.rate_limit = int(os.getenv("P123_RATE_LIMIT", "60"))
        self.request_timeout = int(os.getenv("P123_REQUEST_TIMEOUT", "30"))
