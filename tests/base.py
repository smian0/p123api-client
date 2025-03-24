"""Base test case for P123 API client tests."""

import logging
import os
import unittest

import yaml

from p123api_client.common.settings import Settings


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities."""

    @classmethod
    def setUpClass(cls) -> None:
        # Configure basic logging
        logging.basicConfig(level=logging.INFO)

        # Load test configuration
        config_path = os.path.join(os.path.dirname(__file__), "common", "api_config.yaml")
        try:
            with open(config_path) as file:
                cls.config = yaml.safe_load(file)
        except FileNotFoundError:
            import pytest
            pytest.skip(f"Config file not found: {config_path}")

        # Load test settings
        cls.settings = Settings(testing=True)

        # Check if we have valid test credentials
        if not cls.settings.api_key or not cls.settings.api_id:
            raise unittest.SkipTest("Missing API credentials for testing")

    def setUp(self) -> None:
        # Log the start of each test
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"\n{'=' * 80}\nStarting test: {self._testMethodName}\n{'=' * 80}")

    def tearDown(self) -> None:
        # Log test completion
        self.logger.info(f"\n{'-' * 80}\nCompleted test: {self._testMethodName}\n{'-' * 80}")

    def run(self, result=None):
        """Override run to add more detailed error logging."""
        try:
            super().run(result)
        except Exception as e:
            self.logger.error(f"Test {self._testMethodName} failed: {e}")
            raise


# Alias for backward compatibility
BaseTest = BaseTestCase
