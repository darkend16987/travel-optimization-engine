#!/usr/bin/env python3
"""AI Advisor Module connecting to Google Gemini API."""

import os
import json
from pathlib import Path
import google.generativeai as genai
import importlib.util

# --- Safe import config ---
_config_path = Path(__file__).parent / "config.py"
_spec = importlib.util.spec_from_file_location("_travel_config", _config_path)
_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config)

get_gemini_key = _config.get_gemini_key
APIKeyMissingError = _config.APIKeyMissingError

def generate_advisory(flight_data: dict, skill_name: str) -> str:
    """Read skill instructions and call Gemini to generate advisory."""
    api_key = get_gemini_key()
    if not api_key:
        raise APIKeyMissingError("GEMINI_API_KEY is not set.")

    genai.configure(api_key=api_key)
    
    # Using Gemini 2.5 Flash as fallback for availability
    model_name = 'gemini-2.5-flash'
    model = genai.GenerativeModel(model_name)

    # Load context files
    base_dir = Path(__file__).parent.parent
    skill_path = base_dir / "skills" / skill_name / "SKILL.md"
    
    if not skill_path.exists():
        return f"Error: Skill definition {skill_name} not found."

    with open(skill_path, "r", encoding="utf-8") as f:
        skill_prompt = f.read()

    # Create the final prompt
    prompt = f"""
You are the AI Travel Optimization Engine Advisor.
Below are your core instructions (Skill Logic):
---
{skill_prompt}
---

Here is the selected flight data from the user:
```json
{json.dumps(flight_data, indent=2)}
```

Based ONLY on your skill logic and the given flight data, please generate a concise, markdown-formatted advisory report. Address the user directly. 
Make sure your answer is clean, professional, and directly analyzes this specific flight segment. Use bullet points and bold text for readability.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini AI: {str(e)}"

if __name__ == "__main__":
    # Test script
    mock_flight = {
        "airlines": ["VietJet Air"],
        "price_total": 96,
        "origin": "SGN",
        "destination": "HAN",
        "cabin_class": "ECONOMY",
        "duration_minutes": 130
    }
    print("Testing fee-analysis advisory...")
    res = generate_advisory(mock_flight, "fee-analysis")
    print(res)
