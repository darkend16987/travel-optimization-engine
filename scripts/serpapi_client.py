#!/usr/bin/env python3
"""SerpApi Google Flights API client for Travel Optimization Engine."""

import time
import requests
import importlib.util
from pathlib import Path

# --- Safe import: load config from the same directory using importlib ---
_config_path = Path(__file__).parent / "config.py"
_spec = importlib.util.spec_from_file_location("_travel_config", _config_path)
_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config)

get_serpapi_key = _config.get_serpapi_key
DEFAULTS = _config.DEFAULTS
APIRequestError = _config.APIRequestError

SERPAPI_URL = "https://serpapi.com/search"

# Map standard classes to SerpApi travel_class
# 1: Economy, 2: Premium Economy, 3: Business, 4: First
_CLASS_MAP = {
    "ECONOMY": 1,
    "PREMIUM_ECONOMY": 2,
    "BUSINESS": 3,
    "FIRST": 4
}


def _request(params, retries=None):
    """Make request to SerpApi with retry mechanism."""
    if retries is None:
        retries = DEFAULTS["max_retries"]

    api_key = get_serpapi_key()
    if not api_key:
        raise ValueError("SERPAPI_KEY is missing")

    params["api_key"] = api_key
    params["engine"] = "google_flights"

    for attempt in range(retries + 1):
        try:
            resp = requests.get(
                SERPAPI_URL,
                params=params,
                timeout=DEFAULTS["request_timeout"]
            )
        except requests.Timeout:
            if attempt < retries:
                time.sleep(min(2 ** attempt, DEFAULTS["max_retry_after"]))
                continue
            raise

        if resp.status_code == 429: # Rate limit
            if attempt < retries:
                time.sleep(min(2 ** attempt, DEFAULTS["max_retry_after"]))
                continue

        resp.raise_for_status()
        return resp.json()

    raise APIRequestError(f"SerpApi request failed after {retries + 1} attempts")


def search_flights(origin, destination, departure_date, return_date=None, adults=None, cabin_class=None):
    """
    Search flights using Google Flights engine via SerpApi.

    Args:
        origin: IATA airport code (e.g., "HAN")
        destination: IATA airport code (e.g., "SFO")
        departure_date: "YYYY-MM-DD"
        return_date: "YYYY-MM-DD" for round trip, None for one-way
        adults: Number of adult travelers (default from config)
        cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST

    Returns:
        dict with SerpApi response containing best_flights, other_flights, etc.
    """
    params = {
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "currency": DEFAULTS["currency"],
        "hl": "en",
        "adults": adults or DEFAULTS["adults"],
        "type": 1 if return_date else 2, # 1 for round-trip, 2 for one-way
    }

    if return_date:
        params["return_date"] = return_date

    c_class = cabin_class or DEFAULTS["cabin_class"]
    params["travel_class"] = _CLASS_MAP.get(c_class, 1)

    return _request(params)


if __name__ == "__main__":
    from config import validate_keys
    import argparse
    import json

    validate_keys("serpapi")
    
    parser = argparse.ArgumentParser(description="Test SerpApi Google Flights Search")
    parser.add_argument("--from", dest="origin", required=True, help="Origin IATA code")
    parser.add_argument("--to", dest="destination", required=True, help="Destination IATA code")
    parser.add_argument("--depart", required=True, help="Departure Date YYYY-MM-DD")
    parser.add_argument("--return-date", help="Return Date YYYY-MM-DD")
    args = parser.parse_args()

    print(f"Searching google flights via SerpApi: {args.origin} to {args.destination} on {args.depart}...")
    try:
        results = search_flights(
            origin=args.origin,
            destination=args.destination,
            departure_date=args.depart,
            return_date=args.return_date
        )
        
        best = results.get("best_flights", [])
        if best:
            for flight in best[:3]:
                price = flight.get("price", "N/A")
                airlines = ", ".join([l.get("airline", "") for l in flight.get("flights", [])])
                duration = flight.get("total_duration", 0)
                print(f"- {airlines}: {price}$ | {duration} mins")
        else:
            print("No 'best_flights' found in response.")
    except Exception as e:
        print(f"Error: {e}")
