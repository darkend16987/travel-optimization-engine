#!/usr/bin/env python3
"""Kiwi Tequila API client with virtual interlining support."""

import time
import requests
import importlib.util
from pathlib import Path

# --- Safe import: load config from the same directory using importlib ---
_config_path = Path(__file__).parent / "config.py"
_spec = importlib.util.spec_from_file_location("_travel_config_kiwi", _config_path)
_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config)

get_kiwi_key = _config.get_kiwi_key
KIWI_BASE_URL = _config.KIWI_BASE_URL
DEFAULTS = _config.DEFAULTS
APIRequestError = _config.APIRequestError
_parse_retry_after = _config._parse_retry_after


def _request(endpoint, params=None, retries=None):
    """Make authenticated GET request with retry on 429."""
    if retries is None:
        retries = DEFAULTS["max_retries"]

    headers = {"apikey": get_kiwi_key()}

    for attempt in range(retries + 1):
        try:
            resp = requests.get(
                f"{KIWI_BASE_URL}{endpoint}",
                headers=headers,
                params=params,
                timeout=DEFAULTS["request_timeout"],
            )
        except requests.Timeout:
            if attempt < retries:
                time.sleep(min(2 ** attempt, DEFAULTS["max_retry_after"]))
                continue
            raise

        if resp.status_code == 429:
            retry_after = _parse_retry_after(
                resp.headers.get("Retry-After"),
                default=2 ** attempt,
            )
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        return resp.json()

    raise APIRequestError(f"Kiwi API failed after {retries + 1} attempts")


def search_flights(fly_from, fly_to, date_from, date_to, return_from=None,
                   return_to=None, adults=None, children=0, infants=0,
                   cabin_class=None, max_stopovers=None, curr=None,
                   limit=None, vehicle_type=None):
    """
    Search flights with virtual interlining support.

    Args:
        fly_from: Origin IATA code or city (e.g., "HAN", "hanoi_vn")
        fly_to: Destination IATA code or city
        date_from: "DD/MM/YYYY" departure date range start
        date_to: "DD/MM/YYYY" departure date range end
        return_from: "DD/MM/YYYY" return date range start (omit for one-way)
        return_to: "DD/MM/YYYY" return date range end
        adults: Number of adults
        children: Number of children (2-11)
        infants: Number of infants (0-2)
        cabin_class: "M" (economy), "W" (premium eco), "C" (business), "F" (first)
        max_stopovers: Max number of stopovers (default: 2)
        curr: Currency code (default: USD)
        limit: Max results
        vehicle_type: "aircraft" to exclude buses/trains, or None for all

    Returns:
        dict with "data" (list of itineraries), "currency", "search_id"
    """
    params = {
        "fly_from": fly_from,
        "fly_to": fly_to,
        "date_from": date_from,
        "date_to": date_to,
        "adults": adults or DEFAULTS["adults"],
        "children": children,
        "infants_in_seat": infants,
        "selected_cabins": cabin_class or "M",
        "curr": curr or DEFAULTS["currency"],
        "limit": limit or DEFAULTS["max_results"],
        "max_stopovers": max_stopovers if max_stopovers is not None else DEFAULTS["max_stops"],
        "sort": "price",
        "asc": 1,
    }
    if return_from:
        params["return_from"] = return_from
    if return_to:
        params["return_to"] = return_to
    if vehicle_type:
        params["vehicle_type"] = vehicle_type

    return _request("/v2/search", params=params)


def check_flights(booking_token, adults=1, children=0, infants=0, curr=None):
    """
    Validate a specific itinerary and check current price/availability.

    Args:
        booking_token: Token from search results
        adults: Number of adults
        children: Number of children
        infants: Number of infants
        curr: Currency code

    Returns:
        dict with "flights_checked", "flights_invalid", price confirmation
    """
    params = {
        "booking_token": booking_token,
        "bnum": adults,
        "children": children,
        "infants": infants,
        "currency": curr or DEFAULTS["currency"],
    }
    return _request("/v2/booking/check_flights", params=params)


def search_locations(query, location_types=None, limit=5):
    """
    Search for airport/city location codes.

    Args:
        query: Search term (e.g., "hanoi", "SFO")
        location_types: "airport", "city", or "country"
        limit: Max results

    Returns:
        dict with "locations" list
    """
    params = {
        "term": query,
        "limit": limit,
        "active_only": "true",
    }
    if location_types:
        params["location_types"] = location_types

    return _request("/locations/query", params=params)


if __name__ == "__main__":
    from config import validate_keys
    validate_keys("kiwi")
    print("Kiwi client ready. Base URL:", KIWI_BASE_URL)
