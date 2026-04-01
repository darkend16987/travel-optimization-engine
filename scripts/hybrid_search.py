#!/usr/bin/env python3
"""Hybrid Search Aggregator for Travel Optimization Engine."""

import argparse
import concurrent.futures
import time

import amadeus_client
import serpapi_client
import normalize

def normalize_serpapi_offer(flight, origin, destination, departure_date):
    """Convert SerpApi Google Flights offer to unified format."""
    flights = flight.get("flights", [])
    airlines = set()
    flight_numbers = []
    stop_airports = []

    for idx, f in enumerate(flights):
        carrier = f.get("airline", "Unknown")
        airlines.add(carrier)
        f_num = f.get("flight_number", "")
        # SerpApi sometimes provides full flight number or just number
        if f_num:
            flight_numbers.append(f"{carrier} {f_num}")
        else:
            flight_numbers.append(carrier)
        
        # Collect stops (arrival airport of all but last leg)
        if idx < len(flights) - 1:
            arrival_airport = f.get("arrival_airport", {})
            stop_airports.append(arrival_airport.get("id", ""))

    first_flight = flights[0] if flights else {}
    last_flight = flights[-1] if flights else {}

    # Extract departure and arrival datetime (SerpApi provides strings like '2026-06-15 08:00')
    departure = first_flight.get("departure_airport", {}).get("time", f"{departure_date} 00:00")
    arrival = last_flight.get("arrival_airport", {}).get("time", "")

    duration_minutes = flight.get("total_duration", 0)
    
    # SerpApi provides price directly
    price_total = float(flight.get("price", 0))

    flight_token = flight.get("flight_token", "")
    if not flight_token:
        # Fallback to hash of flight numbers if no token
        flight_token = str(abs(hash("".join(flight_numbers))))

    return {
        "id": f"serpapi_{flight_token[:15]}",
        "source": "serpapi",
        "airlines": sorted(airlines),
        "flight_numbers": flight_numbers,
        "origin": origin,
        "destination": destination,
        "departure": departure.replace(" ", "T"), # Make it pseudo ISO
        "arrival": arrival.replace(" ", "T"),
        "duration_minutes": duration_minutes,
        "stops": len(flights) - 1 if flights else 0,
        "stop_airports": stop_airports,
        "cabin_class": "ECONOMY", # Assuming economy for now
        "price_total": price_total,
        "price_currency": "USD",
        "price_breakdown": {"base": price_total, "taxes": 0, "fees": 0},
        "segments": flights,
        "booking_url": None,
        "booking_token": flight.get("booking_token", None),
        "virtual_interlining": len(airlines) > 1,
        "baggage_included": None,
        "raw": flight,
    }

def run_amadeus(origin, destination, depart, return_date=None, adults=1):
    print("  [Hybrid] Fetching Amadeus...")
    try:
        res = amadeus_client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=depart,
            return_date=return_date,
            adults=adults
        )
        offers = res.get("data", [])
        return [normalize.normalize_amadeus_offer(offer) for offer in offers]
    except Exception as e:
        print(f"  [Hybrid] Amadeus Error: {e}")
        return []

def run_serpapi(origin, destination, depart, return_date=None, adults=1):
    print("  [Hybrid] Fetching SerpApi...")
    try:
        res = serpapi_client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=depart,
            return_date=return_date,
            adults=adults
        )
        best = res.get("best_flights", [])
        other = res.get("other_flights", [])
        all_flights = best + other
        return [normalize_serpapi_offer(f, origin, destination, depart) for f in all_flights]
    except Exception as e:
        print(f"  [Hybrid] SerpApi Error: {e}")
        return []


def hybrid_search(origin, destination, departure_date, return_date=None, adults=1):
    """Run search commands concurrently."""
    print(f"Starting Hybrid Search: {origin} -> {destination} on {departure_date}")
    start_time = time.time()
    
    combined_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_amad = executor.submit(run_amadeus, origin, destination, departure_date, return_date, adults)
        f_serp = executor.submit(run_serpapi, origin, destination, departure_date, return_date, adults)
        
        amadeus_flights = f_amad.result()
        serpapi_flights = f_serp.result()
        
    combined_results.extend(amadeus_flights)
    combined_results.extend(serpapi_flights)
    
    # Process results
    combined_results = normalize.deduplicate_flights(combined_results)
    combined_results = normalize.sort_by_price(combined_results)
    
    end_time = time.time()
    print(f"\nHybrid Search completed in {end_time - start_time:.2f}s")
    print(f"Total unique flights found: {len(combined_results)}")
    print(f"  - From Amadeus: {len(amadeus_flights)}")
    print(f"  - From SerpApi: {len(serpapi_flights)}")
    print("-" * 60)
    
    return combined_results


if __name__ == "__main__":
    from config import validate_keys
    
    # Only strictly require amadeus, but try to fetch serpapi. 
    # Actually we can just let it fail gracefully in the thread if key is missing.
    try:
        validate_keys("serpapi") # At least one source should be strictly validated for the test
    except SystemExit:
        print("Continuing without SerpApi key...")
    
    parser = argparse.ArgumentParser(description="Hybrid Flight Search")
    parser.add_argument("--from", dest="origin", required=True, help="Origin IATA code")
    parser.add_argument("--to", dest="destination", required=True, help="Destination IATA code")
    parser.add_argument("--depart", required=True, help="Departure Date YYYY-MM-DD")
    parser.add_argument("--return-date", help="Return Date YYYY-MM-DD")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults")
    args = parser.parse_args()

    results = hybrid_search(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.depart,
        return_date=args.return_date,
        adults=args.adults
    )
    
    if results:
        print("\nTop 15 Cheapest Options:\n")
        print(normalize.format_results_table(results, top_n=15))
    else:
        print("\nNo flights found.")
