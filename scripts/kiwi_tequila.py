"""
Kiwi Tequila API Client — Standalone CLI tool for flight search.

NOTE: This is a standalone CLI script. For library usage, prefer kiwi_client.py
which uses shared config, retry logic, and safe imports.

Usage:
    python kiwi_tequila.py --from HAN --to SFO --depart 2026-06-16 --return 2026-06-25 --adults 2
    
Environment:
    KIWI_API_KEY: Your Tequila API key (get from tequila.kiwi.com)
"""

import os
import sys
import json
import argparse
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' library required. Install with: pip install requests")
    sys.exit(1)

BASE_URL = "https://api.tequila.kiwi.com"

def get_api_key():
    """Get API key from environment variable."""
    key = os.environ.get("KIWI_API_KEY")
    if not key:
        print("Error: KIWI_API_KEY environment variable not set.")
        print("Get your free API key at: https://tequila.kiwi.com/")
        print("Then set: $env:KIWI_API_KEY='your_key_here' (PowerShell)")
        sys.exit(1)
    return key

def search_flights(fly_from, fly_to, date_from, date_to,
                   return_from=None, return_to=None,
                   adults=1, children=0, infants=0,
                   cabin="M", currency="USD", max_stopovers=2,
                   sort="price", limit=20):
    """
    Search flights using Kiwi Tequila API.
    
    Args:
        fly_from: Origin IATA code
        fly_to: Destination IATA code
        date_from: Departure start (dd/mm/yyyy)
        date_to: Departure end (dd/mm/yyyy)
        return_from: Return start (dd/mm/yyyy), optional
        return_to: Return end (dd/mm/yyyy), optional
        adults: Number of adult passengers
        children: Number of children (2-11)
        infants: Number of infants (<2)
        cabin: M=economy, W=premium_eco, C=business, F=first
        currency: Currency code
        max_stopovers: Maximum number of stops
        sort: price, duration, quality
        limit: Max results
    
    Returns:
        List of normalized flight options
    """
    api_key = get_api_key()
    
    params = {
        "fly_from": fly_from,
        "fly_to": fly_to,
        "date_from": date_from,
        "date_to": date_to,
        "adults": adults,
        "children": children,
        "infants": infants,
        "selected_cabins": cabin,
        "curr": currency,
        "max_stopovers": max_stopovers,
        "sort": sort,
        "limit": limit,
        "locale": "en",
    }
    
    if return_from:
        params["return_from"] = return_from
    if return_to:
        params["return_to"] = return_to
    
    headers = {
        "apikey": api_key,
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/v2/search",
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("Error: Invalid API key. Check your KIWI_API_KEY.")
        elif response.status_code == 429:
            print("Error: Rate limited. Wait 60 seconds and retry.")
        else:
            print(f"HTTP Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")
        return []
    
    return normalize_results(data.get("data", []))

def normalize_results(raw_results):
    """
    Normalize Kiwi API results into standard format.
    
    Returns list of dicts with consistent structure for skill consumption.
    """
    normalized = []
    
    for flight in raw_results:
        airlines = list(set(flight.get("airlines", [])))
        route_segments = []
        
        for segment in flight.get("route", []):
            route_segments.append({
                "from": segment.get("flyFrom"),
                "to": segment.get("flyTo"),
                "airline": segment.get("airline"),
                "flight_no": segment.get("flight_no"),
                "departure": segment.get("local_departure"),
                "arrival": segment.get("local_arrival"),
            })
        
        # Determine tags
        tags = []
        num_stops = len(route_segments) - 1
        if num_stops == 0:
            tags.append("DIRECT")
        elif num_stops == 1:
            tags.append("1-STOP")
        else:
            tags.append(f"{num_stops}-STOP")
        
        if flight.get("virtual_interlining"):
            tags.append("INTERLINING")
        
        if len(airlines) > 1:
            tags.append("MULTI-AIRLINE")
        
        # Get bag prices
        bags_price = flight.get("bags_price", {})
        
        option = {
            "id": flight.get("id"),
            "price": flight.get("price"),
            "airlines": airlines,
            "route": route_segments,
            "duration_hours": round(flight.get("duration", {}).get("total", 0) / 3600, 1),
            "stops": num_stops,
            "tags": tags,
            "virtual_interlining": flight.get("virtual_interlining", False),
            "bags_price": {
                "first_bag": bags_price.get("1", 0),
                "second_bag": bags_price.get("2", 0),
            },
            "availability": flight.get("availability", {}).get("seats"),
            "booking_link": flight.get("deep_link", ""),
            "source": "kiwi_tequila",
        }
        
        normalized.append(option)
    
    return normalized

def resolve_location(query):
    """Resolve city/airport name to IATA code using Kiwi Locations API."""
    api_key = get_api_key()
    
    params = {
        "term": query,
        "location_types": "airport",
        "limit": 5,
    }
    
    headers = {"apikey": api_key}
    
    try:
        response = requests.get(
            f"{BASE_URL}/locations/query",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        locations = data.get("locations", [])
        if locations:
            return [{
                "code": loc.get("code"),
                "name": loc.get("name"),
                "city": loc.get("city", {}).get("name", ""),
                "country": loc.get("city", {}).get("country", {}).get("name", ""),
            } for loc in locations]
    except Exception as e:
        print(f"Location search error: {e}")
    
    return []

def format_date(date_str):
    """Convert YYYY-MM-DD to DD/MM/YYYY format required by Kiwi API."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def main():
    parser = argparse.ArgumentParser(description="Search flights via Kiwi Tequila API")
    parser.add_argument("--from", dest="fly_from", required=True, help="Origin IATA code (e.g., HAN)")
    parser.add_argument("--to", dest="fly_to", required=True, help="Destination IATA code (e.g., SFO)")
    parser.add_argument("--depart", required=True, help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    parser.add_argument("--flex", type=int, default=0, help="Date flexibility in days (e.g., 7)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults")
    parser.add_argument("--children", type=int, default=0, help="Number of children")
    parser.add_argument("--infants", type=int, default=0, help="Number of infants")
    parser.add_argument("--cabin", default="M", choices=["M","W","C","F"], help="Cabin class")
    parser.add_argument("--currency", default="USD", help="Currency code")
    parser.add_argument("--limit", type=int, default=20, help="Max results")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Calculate date ranges with flexibility
    from datetime import timedelta
    depart_dt = datetime.strptime(args.depart, "%Y-%m-%d")
    date_from = (depart_dt - timedelta(days=args.flex)).strftime("%d/%m/%Y")
    date_to = (depart_dt + timedelta(days=args.flex)).strftime("%d/%m/%Y")
    
    return_from = None
    return_to = None
    if args.return_date:
        return_dt = datetime.strptime(args.return_date, "%Y-%m-%d")
        return_from = (return_dt - timedelta(days=args.flex)).strftime("%d/%m/%Y")
        return_to = (return_dt + timedelta(days=args.flex)).strftime("%d/%m/%Y")
    
    print(f"Searching: {args.fly_from} -> {args.fly_to}")
    print(f"Depart: {date_from} to {date_to}")
    if return_from:
        print(f"Return: {return_from} to {return_to}")
    print(f"Passengers: {args.adults}A {args.children}C {args.infants}I")
    print("---")
    
    results = search_flights(
        fly_from=args.fly_from,
        fly_to=args.fly_to,
        date_from=date_from,
        date_to=date_to,
        return_from=return_from,
        return_to=return_to,
        adults=args.adults,
        children=args.children,
        infants=args.infants,
        cabin=args.cabin,
        currency=args.currency,
        limit=args.limit,
    )
    
    print(f"Found {len(results)} options\n")
    
    for i, opt in enumerate(results, 1):
        tags = " ".join(f"[{t}]" for t in opt["tags"])
        airlines = "+".join(opt["airlines"])
        route_str = " -> ".join(s["from"] for s in opt["route"]) + f" -> {opt['route'][-1]['to']}"
        print(f"#{i:2d}  ${opt['price']:>7,.0f}  {route_str:<30s}  {airlines:<12s}  {opt['duration_hours']:.1f}h  {tags}")
    
    if args.output:
        # Validate output path to prevent directory traversal
        output_path = os.path.realpath(args.output)
        if ".." in os.path.relpath(output_path):
            print(f"Error: Output path '{args.output}' is not allowed (directory traversal detected).")
            sys.exit(1)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()
