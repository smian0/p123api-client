"""Test configuration for screen run tests."""

import re
from pathlib import Path

import pytest

from ..vcr_patch import patch_vcr_response

# Apply VCR patch
patch_vcr_response()

# Make sure cassette directory exists
CASSETTE_DIR = Path(__file__).parent / "cassettes"
CASSETTE_DIR.mkdir(exist_ok=True, parents=True)

# Sensitive patterns to mask
SENSITIVE_PATTERNS = [
    (r'"apiKey"\s*:\s*"[^"]*"', '"apiKey": "MASKED"'),
    (r'"apiId"\s*:\s*"[^"]*"', '"apiId": "MASKED"'),
    (r'"token"\s*:\s*"[^"]*"', '"token": "MASKED"'),
    (r'"accessToken"\s*:\s*"[^"]*"', '"accessToken": "MASKED"'),
    (r'"refreshToken"\s*:\s*"[^"]*"', '"refreshToken": "MASKED"'),
]


def mask_sensitive_data(data_str):
    """Mask sensitive data using regex patterns."""
    if not isinstance(data_str, str):
        return data_str

    masked = data_str
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, replacement, masked)
    return masked


def before_record_request(request):
    """Process request before recording."""
    # Mask authorization headers
    if "authorization" in request.headers:
        request.headers["authorization"] = "MASKED"

    # Mask other sensitive headers
    for header in ["x-api-key", "api-key"]:
        if header in request.headers:
            request.headers[header] = "MASKED"

    # Mask body if it's a string and contains sensitive data
    if request.body:
        try:
            body_str = request.body.decode("utf-8")
            masked_body = mask_sensitive_data(body_str)
            request.body = masked_body.encode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            # Not a UTF-8 string or not a bytes object
            pass

    return request


def before_record_response(response):
    """Process response before recording."""
    # Check if the response body contains sensitive data
    if "body" in response and "string" in response["body"]:
        try:
            body_str = response["body"]["string"].decode("utf-8")
            masked_body = mask_sensitive_data(body_str)
            response["body"]["string"] = masked_body.encode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            # Not a UTF-8 string or not a bytes object
            pass

    return response


@pytest.fixture(scope="module")
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
        ],
        "filter_post_data_parameters": [
            ("apiKey", "MASKED"),
            ("apiId", "MASKED"),
            ("token", "MASKED"),
        ],
        "record_mode": "once",
        "serializer": "yaml",
        "path_transformer": lambda path: f"{path}.yaml" if not path.endswith(".yaml") else path,
        "cassette_library_dir": str(CASSETTE_DIR),
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "decode_compressed_response": True,
        "before_record_request": before_record_request,
        "before_record_response": before_record_response,
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """VCR cassette directory fixture."""
    # Use the cassettes directory in the same directory as the test file
    return str(CASSETTE_DIR)
