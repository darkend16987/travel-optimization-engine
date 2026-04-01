"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import { popularAirports } from "../lib/airports";

interface Flight {
  id: string;
  source: string;
  airlines: string[];
  flight_numbers: string[];
  origin: string;
  destination: string;
  departure: string;
  arrival: string;
  duration_minutes: number;
  stops: number;
  cabin_class: string;
  price_total: number;
  price_breakdown: { base: number; taxes: number; fees: number };
  virtual_interlining: boolean;
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [aiAdvisory, setAiAdvisory] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  
  const [origin, setOrigin] = useState("HAN");
  const [destination, setDestination] = useState("SFO");
  const [depart, setDepart] = useState("2026-06-15");
  const [returnDate, setReturnDate] = useState("");
  const [adults, setAdults] = useState(1);
  const [maxStops, setMaxStops] = useState<string>("any");

  // Autocomplete state
  const [originSearch, setOriginSearch] = useState("Hà Nội");
  const [destSearch, setDestSearch] = useState("San Francisco");
  const [showOriginDropdown, setShowOriginDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const res = await fetch(`${apiUrl}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin,
          destination,
          depart,
          return_date: returnDate || null,
          adults,
          max_stops: maxStops === "direct" ? 0 : null
        }),
      });

      if (!res.ok) throw new Error("API Connection Failed");

      const data = await res.json();
      setResults(data.flights || []);
    } catch (err: any) {
      setError(err.message || "Failed to search flights");
    } finally {
      setLoading(false);
    }
  };

  const getAiAdvisory = async (flight: Flight) => {
    setSelectedFlight(flight);
    setAiAdvisory(null);
    setAnalyzing(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const res = await fetch(`${apiUrl}/api/ai-analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Using fee-analysis as the primary advisory for now (can combine later)
        body: JSON.stringify({ flight_data: flight, skill_name: "fee-analysis" })
      });
      if (!res.ok) throw new Error("AI Advisor Failed");
      const data = await res.json();
      setAiAdvisory(data.advisory);
    } catch (err: any) {
      setAiAdvisory("⚠️ Error connecting to AI Advisor: " + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const formatDuration = (mins: number) => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m`;
  };

  return (
    <main className="min-h-screen bg-[#F9FAFB]">
      {/* Hero Section */}
      <div className="bg-[#171717] text-white py-20 px-4 text-center header-bg relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#171717] to-[#404040] opacity-80" />
        <div className="relative z-10 max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Travel <span className="text-[#D4AF37]">Optimization</span> Engine
          </h1>
          <p className="text-gray-300 mb-10 text-lg">
            Find the cheapest flights, avoid hidden fees, and optimize your routes intelligently.
          </p>

          {/* Search Box */}
          <form 
            onSubmit={handleSearch}
            className="bg-white p-6 rounded-2xl shadow-xl grid grid-cols-1 md:grid-cols-12 gap-4 text-left border border-gray-100 items-end"
          >
            {/* Origin Autocomplete */}
            <div className="md:col-span-3 relative">
              <label className="text-xs text-gray-500 font-semibold mb-1 block uppercase tracking-wider">From (City/Airport)</label>
              <input 
                type="text" 
                required
                value={originSearch}
                onChange={e => {
                  setOriginSearch(e.target.value);
                  setShowOriginDropdown(true);
                }}
                onFocus={() => setShowOriginDropdown(true)}
                onBlur={() => setTimeout(() => setShowOriginDropdown(false), 200)}
                className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-lg px-4 py-3 focus:ring-2 focus:ring-[#D4AF37] focus:outline-none transition-all placeholder-gray-400"
                placeholder="Hà Nội"
              />
              {showOriginDropdown && originSearch.length > 0 && (
                <ul className="absolute z-50 w-full bg-white border border-gray-200 rounded-lg mt-1 shadow-lg max-h-60 overflow-y-auto">
                  {popularAirports.filter(a => a.name.toLowerCase().includes(originSearch.toLowerCase()) || a.code.toLowerCase().includes(originSearch.toLowerCase())).map(airport => (
                    <li 
                      key={airport.code} 
                      className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
                      onClick={() => {
                        setOriginSearch(`${airport.name} (${airport.code})`);
                        setOrigin(airport.code);
                        setShowOriginDropdown(false);
                      }}
                    >
                      <div className="font-bold text-gray-900">{airport.name} <span className="text-gray-400 font-normal">({airport.code})</span></div>
                      <div className="text-xs text-gray-500">{airport.full}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Destination Autocomplete */}
            <div className="md:col-span-3 relative">
              <label className="text-xs text-gray-500 font-semibold mb-1 block uppercase tracking-wider">To (City/Airport)</label>
              <input 
                type="text" 
                required
                value={destSearch}
                onChange={e => {
                  setDestSearch(e.target.value);
                  setShowDestDropdown(true);
                }}
                onFocus={() => setShowDestDropdown(true)}
                onBlur={() => setTimeout(() => setShowDestDropdown(false), 200)}
                className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-lg px-4 py-3 focus:ring-2 focus:ring-[#D4AF37] focus:outline-none transition-all placeholder-gray-400"
                placeholder="San Francisco"
              />
              {showDestDropdown && destSearch.length > 0 && (
                <ul className="absolute z-50 w-full bg-white border border-gray-200 rounded-lg mt-1 shadow-lg max-h-60 overflow-y-auto">
                  {popularAirports.filter(a => a.name.toLowerCase().includes(destSearch.toLowerCase()) || a.code.toLowerCase().includes(destSearch.toLowerCase())).map(airport => (
                    <li 
                      key={airport.code} 
                      className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
                      onClick={() => {
                        setDestSearch(`${airport.name} (${airport.code})`);
                        setDestination(airport.code);
                        setShowDestDropdown(false);
                      }}
                    >
                      <div className="font-bold text-gray-900">{airport.name} <span className="text-gray-400 font-normal">({airport.code})</span></div>
                      <div className="text-xs text-gray-500">{airport.full}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="text-xs text-gray-500 font-semibold mb-1 block uppercase tracking-wider">Depart</label>
              <input 
                type="date"
                required
                value={depart}
                onChange={e => setDepart(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-lg px-4 py-3 focus:ring-2 focus:ring-[#D4AF37] focus:outline-none transition-all cursor-pointer"
              />
            </div>
            
            <div className="md:col-span-1">
              <label className="text-xs text-gray-500 font-semibold mb-1 block uppercase tracking-wider">Pax</label>
              <input 
                type="number"
                min="1"
                required
                value={adults}
                onChange={e => setAdults(Number(e.target.value))}
                className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-lg px-4 py-3 focus:ring-2 focus:ring-[#D4AF37] focus:outline-none transition-all"
              />
            </div>

            <div className="md:col-span-2">
              <label className="text-xs text-gray-500 font-semibold mb-1 block uppercase tracking-wider">Stops</label>
              <select 
                value={maxStops}
                onChange={e => setMaxStops(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 text-gray-900 rounded-lg px-4 py-3 focus:ring-2 focus:ring-[#D4AF37] focus:outline-none transition-all"
              >
                <option value="any">Any Routes</option>
                <option value="direct">Direct Only</option>
              </select>
            </div>

            <div className="md:col-span-1 mt-5 md:mt-0">
              <button 
                type="submit" 
                disabled={loading}
                className="w-full md:w-auto bg-[#D4AF37] hover:bg-[#b5952c] text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 mt-1 h-[50px]"
              >
                {loading ? "..." : "Search"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Results Section */}
      <div className="max-w-5xl mx-auto px-4 py-12">
        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center mb-8 border border-red-100">
            <svg className="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-20 text-gray-500">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4AF37] mx-auto mb-4"></div>
            <p>Scanning multiple sources and optimizing routes...</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6 text-[#171717] flex items-center gap-2">
              Optimization Results
              <span className="bg-gray-100 text-sm font-normal px-3 py-1 rounded-full text-gray-600">
                {results.length} found
              </span>
            </h2>
            
            <div className="grid gap-6">
              {results.slice(0, 15).map((flight, idx) => (
                <div key={flight.id} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow relative overflow-hidden group">
                  {/* Badge */}
                  {idx === 0 && (
                    <div className="absolute top-0 right-0 bg-[#D4AF37] text-white text-xs font-bold px-4 py-1 rounded-bl-xl tracking-wide">
                      CHEAPEST
                    </div>
                  )}

                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    {/* Airlines */}
                    <div className="flex-[2]">
                      <h3 className="font-bold text-lg">{flight.airlines.join(", ")}</h3>
                      <p className="text-sm text-gray-500 mt-1">{flight.flight_numbers.join(", ")}</p>
                      
                      {flight.virtual_interlining && (
                        <div className="mt-2 inline-flex items-center text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-md cursor-help relative group/tooltip">
                          <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                          Virtual Interlining
                          <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-[#171717] text-white rounded shadow-xl opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all pointer-events-none z-10 text-left">
                            <strong>Note:</strong> Self-connection required. You may need to transfer baggage manually and pass through immigration again. Use with caution.
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Route Timeline */}
                    <div className="flex-[3] w-full flex items-center justify-between text-center px-4">
                      <div className="text-right">
                        <p className="font-bold text-xl">{flight.departure.split("T")[1].substring(0,5)}</p>
                        <p className="text-sm font-medium text-gray-500">{flight.origin}</p>
                      </div>
                      
                      <div className="flex-1 px-4 relative">
                        <div className="h-[2px] bg-gray-200 w-full rounded relative mt-2">
                          {flight.stops > 0 && (
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-[#D4AF37] rounded-full border border-white"></div>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 mt-2 font-medium">
                          {flight.stops === 0 ? "Direct" : `${flight.stops} Stop${flight.stops > 1 ? 's' : ''}`} • {formatDuration(flight.duration_minutes)}
                        </p>
                      </div>

                      <div className="text-left">
                        <p className="font-bold text-xl">{flight.arrival ? flight.arrival.split("T")[1].substring(0,5) : "--:--" }</p>
                        <p className="text-sm font-medium text-gray-500">{flight.destination}</p>
                      </div>
                    </div>

                    {/* Price & Action */}
                    <div className="flex-[2] text-right flex flex-col md:items-end justify-center">
                      <p className="text-3xl font-bold text-[#171717]">${flight.price_total.toFixed(0)}</p>
                      <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider">{flight.source}</p>
                      <button 
                        onClick={() => getAiAdvisory(flight)}
                        className="mt-4 px-6 py-2 border-2 border-[#171717] text-[#171717] hover:bg-[#171717] hover:text-white rounded-lg font-semibold transition-colors duration-200 text-sm whitespace-nowrap"
                      >
                        AI Analysis
                      </button>
                    </div>

                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Selected Flight Modal / AI Insights */}
        {selectedFlight && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl w-full max-w-5xl max-h-[92vh] overflow-y-auto shadow-2xl">
              
              {/* Modal Header */}
              <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50 rounded-t-2xl">
                <div>
                  <h2 className="text-2xl font-bold text-[#171717]">Flight Details & Optimization</h2>
                  <p className="text-gray-500 mt-1">ID: {selectedFlight.id}</p>
                </div>
                <button 
                  onClick={() => setSelectedFlight(null)}
                  className="text-gray-400 hover:text-gray-800 bg-gray-200 hover:bg-gray-300 rounded-full p-2 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6">
                
                {/* Section 1: Itinerary */}
                <div className="mb-8">
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <span className="bg-gray-100 p-2 rounded-lg"><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></span>
                    Itinerary
                  </h3>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-xl text-[#171717]">{selectedFlight.origin}</span>
                      <span className="text-gray-400 text-sm">{formatDuration(selectedFlight.duration_minutes)}</span>
                      <span className="font-semibold text-xl text-[#171717]">{selectedFlight.destination}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm text-gray-500">
                      <span>{selectedFlight.departure.replace("T", " ")}</span>
                      <span>{selectedFlight.stops} Stops</span>
                      <span>{selectedFlight.arrival ? selectedFlight.arrival.replace("T", " ") : "N/A"}</span>
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium">Airlines: <span className="text-gray-600">{selectedFlight.airlines.join(", ")}</span></p>
                      <p className="text-sm font-medium">Flight Numbers: <span className="text-gray-600">{selectedFlight.flight_numbers.join(", ")}</span></p>
                    </div>
                  </div>
                </div>

                {/* Section 2: AI Optimization Modules */}
                <div className="mt-8 border-t border-gray-200 pt-6">
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-700">
                    <span className="bg-indigo-100 text-indigo-700 p-2 rounded-lg">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </span>
                    AI Optimization Advisor
                  </h3>
                  
                  {analyzing ? (
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-8 rounded-xl flex flex-col items-center justify-center border border-gray-200">
                      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4"></div>
                      <p className="text-gray-600 font-medium animate-pulse">Gemini 2.5 Flash is analyzing fees and route options...</p>
                    </div>
                  ) : aiAdvisory ? (
                    <div className="prose prose-lg prose-indigo max-w-none bg-blue-50/50 p-6 rounded-xl border border-blue-100 leading-relaxed text-gray-800">
                      <ReactMarkdown>{aiAdvisory}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="bg-red-50 text-red-600 p-4 rounded-lg">Failed to load AI advisory.</div>
                  )}
                </div>

                {/* Footer Action */}
                <div className="mt-8 flex justify-end gap-4 border-t border-gray-100 pt-6">
                  <a href={`https://www.google.com/travel/flights?q=Flights%20to%20${selectedFlight.destination}%20from%20${selectedFlight.origin}%20on%20${selectedFlight.departure.substring(0,10)}`} target="_blank" rel="noreferrer" className="bg-[#D4AF37] hover:bg-[#b5952c] text-white px-8 py-3 rounded-lg font-bold transition-colors">
                    Search on Google Flights
                  </a>
                </div>

              </div>
            </div>
          </div>
        )}

        {!loading && !error && results.length === 0 && (
          <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-300">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Enter trip details to begin</h3>
            <p className="text-gray-500">Search for flights to optimize your travel and save money.</p>
          </div>
        )}
      </div>
    </main>
  );
}
