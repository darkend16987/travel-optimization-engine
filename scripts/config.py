#!/usr/bin/env python3
"""Shared configuration for Travel Optimization Engine API clients."""

import os
import sys


# --- Custom Exception ---
class TravelAPIError(Exception):
    """Base exception for Travel Optimization Engine API errors."""
    pass


class APIKeyMissingError(TravelAPIError):
    """Raised when a required API key is not set."""
    pass


class APIRequestError(TravelAPIError):
    """Raised when an API request fails after all retries."""
    pass


# --- API Credentials (lazy-loaded from environment variables) ---
# Keys are read via functions to avoid loading secrets at module import time,
# which reduces the risk of accidental leakage through logging or stack traces.

def get_amadeus_key():
    """Get Amadeus API key from environment. Reads at call time, not import time."""
    return os.environ.get("AMADEUS_API_KEY", "")


def get_amadeus_secret():
    """Get Amadeus API secret from environment. Reads at call time, not import time."""
    return os.environ.get("AMADEUS_API_SECRET", "")


def get_kiwi_key():
    """Get Kiwi API key from environment. Reads at call time, not import time."""
    return os.environ.get("KIWI_API_KEY", "")


def get_serpapi_key():
    """Get SerpApi API key from environment. Reads at call time, not import time."""
    return os.environ.get("SERPAPI_KEY", "")


def get_gemini_key():
    """Get Gemini API key from environment. Reads at call time."""
    return os.environ.get("GEMINI_API_KEY", "")


# --- Base URLs ---
# Amadeus: switch to production by setting AMADEUS_ENV=production
def get_amadeus_base_url():
    """Get Amadeus base URL based on AMADEUS_ENV environment variable."""
    env = os.environ.get("AMADEUS_ENV", "test")
    if env == "production":
        return "https://api.amadeus.com"
    return "https://test.api.amadeus.com"


# Kiwi Tequila
KIWI_BASE_URL = "https://api.tequila.kiwi.com"

# --- Default Search Parameters ---
DEFAULTS = {
    "adults": 1,
    "children": 0,
    "infants": 0,
    "currency": "USD",
    "max_stops": 2,
    "cabin_class": "ECONOMY",  # ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
    "max_results": 20,
    "request_timeout": 30,  # seconds
    "max_retries": 3,
    "max_retry_after": 120,  # max seconds to sleep on Retry-After header
}

# --- Backward compatibility aliases ---
# DEPRECATED: Use getter functions instead. These read env vars at import time.
AMADEUS_API_KEY = os.environ.get("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET = os.environ.get("AMADEUS_API_SECRET", "")
KIWI_API_KEY = os.environ.get("KIWI_API_KEY", "")
AMADEUS_ENV = os.environ.get("AMADEUS_ENV", "test")
AMADEUS_BASE_URL = (
    "https://api.amadeus.com" if AMADEUS_ENV == "production"
    else "https://test.api.amadeus.com"
)


def validate_keys(*required_keys):
    """Check that required API keys are set. Exit with message if missing."""
    missing = []
    key_map = {
        "amadeus": (get_amadeus_key(), get_amadeus_secret()),
        "kiwi": (get_kiwi_key(),),
        "serpapi": (get_serpapi_key(),),
        "gemini": (get_gemini_key(),),
    }
    for key_name in required_keys:
        values = key_map.get(key_name, ())
        if any(not v for v in values):
            missing.append(key_name.upper())
    if missing:
        print(f"ERROR: Missing API keys for: {', '.join(missing)}", file=sys.stderr)
        print("Set environment variables: AMADEUS_API_KEY, AMADEUS_API_SECRET, KIWI_API_KEY, SERPAPI_KEY", file=sys.stderr)
        sys.exit(1)


def _parse_retry_after(header_value, default):
    """Safely parse Retry-After header, which may be seconds or HTTP-date.

    Returns number of seconds to wait, capped at DEFAULTS['max_retry_after'].
    """
    if header_value is None:
        return min(default, DEFAULTS["max_retry_after"])
    try:
        seconds = int(header_value)
    except (ValueError, TypeError):
        # Retry-After might be an HTTP-date (RFC 7231); fall back to default
        seconds = default
    return min(max(seconds, 0), DEFAULTS["max_retry_after"])
