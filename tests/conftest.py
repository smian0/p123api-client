"""Common test configuration and fixtures."""

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

# Apply VCR patch
patch_vcr_response()

# Sensitive patterns to mask
SENSITIVE_PATTERNS = [
    (r'"apiKey"\s*:\s*"[^"]*"', '"apiKey": "MASKED"'),
    (r'"apiId"\s*:\s*"[^"]*"', '"apiId": "MASKED"'),
    (r'"token"\s*:\s*"[^"]*"', '"token": "MASKED"'),
    (r'"accessToken"\s*:\s*"[^"]*"', '"accessToken": "MASKED"'),
    (r'"refreshToken"\s*:\s*"[^"]*"', '"refreshToken": "MASKED"'),
    (r'"password"\s*:\s*"[^"]*"', '"password": "MASKED"'),
    (r'"secret"\s*:\s*"[^"]*"', '"secret": "MASKED"'),
    # Add patterns for any other sensitive fields
]


def mask_sensitive_data(data_str):
    """Mask sensitive data using regex patterns."""
    if not isinstance(data_str, str):
        return data_str

    masked = data_str
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, replacement, masked)
    return masked


def sanitize_dict(data):
    """Recursively sanitize dictionary values."""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    sensitive_keys = {
        "apiKey",
        "apiId",
        "token",
        "accessToken",
        "refreshToken",
        "password",
        "secret",
        "api_key",
        "api_id",
        "auth_token",
    }

    for key, value in data.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "MASKED"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def before_record_request(request):
    """Filter out sensitive data from request bodies."""
    if request.body:
        try:
            if isinstance(request.body, str):
                # Try to handle as JSON first
                try:
                    import json

                    body = json.loads(request.body)
                    if isinstance(body, dict):
                        body = sanitize_dict(body)
                        request.body = json.dumps(body)
                except json.JSONDecodeError:
                    # If not JSON, apply regex masking
                    request.body = mask_sensitive_data(request.body)
            elif isinstance(request.body, bytes):
                try:
                    import json

                    body = json.loads(request.body.decode("utf-8"))
                    if isinstance(body, dict):
                        body = sanitize_dict(body)
                        request.body = json.dumps(body).encode("utf-8")
                except json.JSONDecodeError:
                    # If not JSON, decode, mask, and re-encode
                    decoded = request.body.decode("utf-8")
                    masked = mask_sensitive_data(decoded)
                    request.body = masked.encode("utf-8")
        except Exception:
            # If any error occurs, mask the entire body
            request.body = "MASKED"
    return request


def before_record_response(response):
    """Mask sensitive data in response bodies."""
    if response and response["body"]["string"]:
        try:
            import json

            # Try to parse as JSON
            try:
                # Convert bytes to string if needed
                body_str = response["body"]["string"]
                if isinstance(body_str, bytes):
                    body_str = body_str.decode("utf-8")

                body = json.loads(body_str)
                if isinstance(body, dict):
                    body = sanitize_dict(body)
                    response["body"]["string"] = json.dumps(body).encode("utf-8")
                elif isinstance(body, list):
                    body = [
                        sanitize_dict(item) if isinstance(item, dict) else item for item in body
                    ]
                    response["body"]["string"] = json.dumps(body).encode("utf-8")
                else:
                    # If not a dict/list, mask the entire response
                    response["body"]["string"] = b"MASKED"
            except json.JSONDecodeError:
                # If not JSON, apply regex masking
                if isinstance(response["body"]["string"], bytes):
                    decoded = response["body"]["string"].decode("utf-8")
                    masked = mask_sensitive_data(decoded)
                    response["body"]["string"] = masked.encode("utf-8")
                else:
                    response["body"]["string"] = mask_sensitive_data(
                        response["body"]["string"]
                    ).encode("utf-8")
        except Exception:
            # If any error occurs, mask the entire response
            response["body"]["string"] = b"MASKED"
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
    """VCR configuration fixture."""
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
        "record_mode": "once",
        "serializer": "yaml",
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
