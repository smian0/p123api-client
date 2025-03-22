"""Patch for VCR.py to handle urllib3 compatibility issues."""

from vcr.stubs import VCRHTTPResponse


def patch_vcr_response():
    """Add version_string attribute to VCRHTTPResponse."""
    if not hasattr(VCRHTTPResponse, "version_string"):
        VCRHTTPResponse.version_string = "HTTP/1.1"  # Default to HTTP/1.1
