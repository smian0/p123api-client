"""Common test configuration and fixtures."""

import os
import re
from pathlib import Path

import pytest

from p123api_client.common.settings import Settings
from p123api_client.models.enums import (
    UNIVERSE_SP500,
    OutputType,
    PitMethod,
    RebalFreq,
    TransType,
)
from p123api_client.rank_update.rank_update_api import RankUpdateAPI
from p123api_client.screen_run.screen_run_api import ScreenRunAPI
from p123api_client.strategy.strategy_api import StrategyAPI

from .vcr_patch import patch_vcr_response

# Import visual test hooks

# Apply VCR patch
patch_vcr_response()


# Add command line option for displaying test failures
def pytest_addoption(parser):
    """Add custom command line options for visual test output."""
    parser.addoption(
        "--show-failures",
        action="store_true",
        default=False,
        help="Run tests that demonstrate failure formatting",
    )
    parser.addoption(
        "--visual-output",
        action="store_true",
        default=False,
        help="Enable rich visual output formatting for tests",
    )


# VCR configuration from environment variables
VCR_RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "once")
VCR_ENABLED = os.environ.get("VCR_ENABLED", "true").lower() != "false"

# Regular expressions for sensitive data patterns
SENSITIVE_PATTERNS = [
    (re.compile(r'("token":\s*)"[^"]*"'), r'\1"MASKED"'),
    (re.compile(r'("apiKey":\s*)"[^"]*"'), r'\1"MASKED"'),
    (re.compile(r'("authorization":\s*)"[^"]*"'), r'\1"MASKED"'),
    (re.compile(r'("api-key":\s*)"[^"]*"'), r'\1"MASKED"'),
    (re.compile(r'("x-api-key":\s*)"[^"]*"'), r'\1"MASKED"'),
]

# Additional patterns for URLs containing sensitive data
URL_PATTERNS = [
    (re.compile(r"(token=)[^&]*"), r"\1MASKED"),
    (re.compile(r"(api_key=)[^&]*"), r"\1MASKED"),
    (re.compile(r"(apiKey=)[^&]*"), r"\1MASKED"),
]


def before_record_request(request):
    """Mask sensitive data in request URLs and headers before recording."""
    for pattern, replacement in URL_PATTERNS:
        request.uri = pattern.sub(replacement, request.uri)
    return request


def before_record_response(response):
    """Mask sensitive data in responses before recording."""
    if response.get("body", {}).get("string"):
        body_str = response["body"]["string"].decode("utf-8")
        for pattern, replacement in SENSITIVE_PATTERNS:
            body_str = pattern.sub(replacement, body_str)
        response["body"]["string"] = body_str.encode("utf-8")
    return response


# Base VCR configuration
VCR_CONFIG = {
    "filter_headers": [
        ("authorization", "MASKED"),
        ("x-api-key", "MASKED"),
        ("api-key", "MASKED"),
        ("content-length", "MASKED"),
        ("cookie", "MASKED"),
        ("set-cookie", "MASKED"),
        ("x-access-token", "MASKED"),
        ("x-refresh-token", "MASKED"),
    ],
    "filter_post_data_parameters": [
        ("apiKey", "MASKED"),
        ("apiId", "MASKED"),
        ("token", "MASKED"),
        ("password", "MASKED"),
        ("secret", "MASKED"),
    ],
    "record_mode": "new_episodes",  # Changed from "all" to "once"
    "serializer": "yaml",
    "path_transformer": lambda path: f"{path}.yaml" if not path.endswith(".yaml") else path,
    "match_on": ["method", "scheme", "host", "port", "path", "query"],
    "decode_compressed_response": True,
    "before_record_request": before_record_request,
    "before_record_response": before_record_response,
}


@pytest.fixture(scope="session")
def vcr_config():
    """VCR configuration fixture.

    This configuration can be controlled via environment variables:
    - VCR_ENABLED: Set to "false" to disable VCR completely (default: "true")
    - VCR_RECORD_MODE: Set to control recording mode (default: "once")
        - "once": Record once, then replay
        - "none": Never record, replay only
        - "new_episodes": Record new interactions, replay existing ones
        - "all": Always record

    Usage in CI environments:

    To run tests with real API calls (e.g., on main branch):
    ```
    VCR_ENABLED=false pytest tests/
    ```

    To run tests using only existing cassettes (e.g., on pull requests):
    ```
    VCR_RECORD_MODE=none pytest tests/
    ```

    To update cassettes with new API responses:
    ```
    VCR_RECORD_MODE=all pytest tests/
    ```
    """
    if not VCR_ENABLED:
        # If VCR is disabled, use mock mode to prevent any recording/playback
        return {
            "record_mode": "none",
            "ignore_hosts": ["api.portfolio123.com"],  # Ignore all P123 API calls
        }

    return {
        "filter_headers": [
            ("authorization", "MASKED"),
            ("x-api-key", "MASKED"),
            ("api-key", "MASKED"),
            ("content-length", "MASKED"),
            ("cookie", "MASKED"),
            ("set-cookie", "MASKED"),
            ("x-access-token", "MASKED"),
            ("x-refresh-token", "MASKED"),
        ],
        "filter_post_data_parameters": [
            ("apiKey", "MASKED"),
            ("apiId", "MASKED"),
            ("token", "MASKED"),
            ("password", "MASKED"),
            ("secret", "MASKED"),
        ],
        "record_mode": VCR_RECORD_MODE,
        "serializer": "yaml",
        "path_transformer": lambda path: f"{path}.yaml" if not path.endswith(".yaml") else path,
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "decode_compressed_response": True,
        "before_record_request": before_record_request,
        "before_record_response": before_record_response,
    }


@pytest.fixture(scope="session")
def settings():
    """Load test settings."""
    return Settings(testing=True)


@pytest.fixture(scope="session")
def api_credentials(settings):
    """Get API credentials from settings."""
    return {
        "api_id": settings.api_id or "test_api_id",
        "api_key": settings.api_key or "test_api_key",
    }


@pytest.fixture
def strategy_api(api_credentials):
    """Create a StrategyAPI client for testing."""
    return StrategyAPI(**api_credentials)


@pytest.fixture
def rank_update_api(api_credentials):
    """Create a rank update API client for testing."""
    api_id, api_key = api_credentials
    return RankUpdateAPI(api_id=api_id, api_key=api_key)


@pytest.fixture
def screen_run_api(api_credentials):
    """Create a screen run API client for testing."""
    api_id = api_credentials.get("api_id")
    api_key = api_credentials.get("api_key")

    if not api_id or not api_key:
        pytest.skip("Missing API credentials for screen run tests")

    return ScreenRunAPI(api_id=api_id, api_key=api_key)


@pytest.fixture(scope="session")
def rank_perf_config():
    """Default configuration for rank performance tests."""
    return {
        "pit_method": PitMethod.PRELIM,
        "trans_type": TransType.LONG,
        "rebal_freq": RebalFreq.EVERY_WEEK,
        "min_holding_period": 1,
        "max_holding_period": 20,
        "commission": 0.001,
        "slippage": 0.25,
        "min_pos_size": 0.01,
        "max_pos_size": 0.1,
        "max_turnover": 1.0,
        "max_positions": 100,
        "output_dir": "tests/rank_perf/test_output",
        "output_format": OutputType.ANNUALIZED,
        "universe": UNIVERSE_SP500,
    }


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "api": {
            "id": "MASKED",
            "key": "MASKED",
            "base_url": "https://api.portfolio123.com",
            "timeout": 30,
            "verify_ssl": True,
        },
        "test": {
            "ranking_system": "Small and Micro Cap Focus",
            "universe": "SP500",
            "tickers": "AAPL,MSFT,GOOGL",
        },
    }


@pytest.fixture(scope="session")
def test_output_dirs():
    """Test output directories configuration."""
    return {"rank_perf": "tests/rank_perf/test_output"}


def pytest_sessionfinish(session):
    """Run after all tests complete to verify no sensitive data is leaked in cassettes."""
    import glob

    # Patterns to check for sensitive data
    sensitive_patterns = [
        r'"apiKey"\s*:\s*"[^"]*(?<!MASKED)"',  # apiKey not ending in MASKED
        r'"apiId"\s*:\s*"[^"]*(?<!MASKED)"',  # apiId not ending in MASKED
        r'"token"\s*:\s*"[^"]*(?<!MASKED)"',  # token not ending in MASKED
        r'"accessToken"\s*:\s*"[^"]*(?<!MASKED)"',
        r'"refreshToken"\s*:\s*"[^"]*(?<!MASKED)"',
        r'"password"\s*:\s*"[^"]*(?<!MASKED)"',
        r'"secret"\s*:\s*"[^"]*(?<!MASKED)"',
        r'"apiId"\s*:\s*"144"',  # Specific API ID format
    ]

    # Find all cassette files
    cassettes = []
    for test_dir in glob.glob("tests/**/cassettes", recursive=True):
        cassettes.extend(glob.glob(f"{test_dir}/**/*.yaml", recursive=True))
        # Also check for files without .yaml extension
        cassettes.extend(
            [
                f
                for f in glob.glob(f"{test_dir}/**/*", recursive=True)
                if not f.endswith(".yaml") and Path(f).is_file()
            ]
        )

    leaked_data = []
    for cassette_path in cassettes:
        try:
            with open(cassette_path) as f:
                content = f.read()

            for pattern in sensitive_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    leaked_data.append(
                        {
                            "file": cassette_path,
                            "pattern": pattern,
                            "match": match.group(0),
                            "line_number": content[: match.start()].count("\n") + 1,
                        }
                    )
        except Exception as e:
            print(f"Error checking {cassette_path}: {e}")

    if leaked_data:
        error_msg = ["Found leaked sensitive data in cassettes:"]
        for leak in leaked_data:
            error_msg.append(
                f"\nFile: {leak['file']}"
                f"\nLine {leak['line_number']}: Matched pattern '{leak['pattern']}'"
                f"\nFound: {leak['match']}"
            )
        pytest.fail("\n".join(error_msg))


@pytest.fixture
def auto_vcr(request):
    """Automatically apply VCR to tests based on environment variables.

    Usage:
    ```
    def test_something(auto_vcr):
        # VCR will be auto-configured based on environment variables
        # Test code here...
    ```

    With this fixture, you don't need to manually specify @pytest.mark.vcr()
    for each test, and VCR behavior can be controlled globally.
    """
    if not VCR_ENABLED:
        # Skip VCR if disabled
        print(f"VCR is disabled by environment variable VCR_ENABLED={VCR_ENABLED}")
        return None

    from vcr.config import VCR

    # Get test name for cassette
    test_name = request.node.name
    module_path = Path(request.module.__file__)
    module_name = request.module.__name__.split(".")[-1]

    # Determine the cassette directory
    # VCR pattern: {directory of test module}/cassettes/{test_module}
    cassette_dir = module_path.parent / "cassettes"
    cassette_dir.mkdir(parents=True, exist_ok=True)

    # Get the class name if it exists
    class_name = ""
    if request.cls:
        class_name = request.cls.__name__
        cassette_name = f"{class_name}.{test_name}"
    else:
        cassette_name = f"{module_name}.{test_name}"

    # Get cassette path with yaml extension
    cassette_path = str(cassette_dir / cassette_name)
    if not cassette_path.endswith(".yaml"):
        cassette_path += ".yaml"

    print(f"Using VCR cassette: {cassette_path} (mode: {VCR_RECORD_MODE})")

    # Create VCR instance with the same config as pytest-vcr would use
    vcr_config = request.getfixturevalue("vcr_config")
    vcr_obj = VCR(**vcr_config)

    # Create a cassette context
    cassette = vcr_obj.use_cassette(cassette_path)
    cassette.__enter__()

    # Add cleanup to ensure cassette is closed
    request.addfinalizer(lambda: cassette.__exit__(None, None, None))

    return cassette


@pytest.fixture(scope="session")
def vcr_cassette_dir():
    """VCR cassette directory fixture."""
    return os.path.join(os.path.dirname(__file__), "cassettes/auto_vcr")


# Configure pytest to access command line options directly
@pytest.fixture(scope="session")
def config():
    """Get the configuration from the pytest config object."""
    return pytest.config
