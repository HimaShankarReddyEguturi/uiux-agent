#!/usr/bin/env python3
"""
Quick test for /latest-report endpoint
"""

import requests
import json

def test_latest_report():
    """Test the /latest-report endpoint"""
    url = "http://localhost:8000/latest-report"
    
    try:
        print("Testing /latest-report endpoint...")
        response = requests.get(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: {json.dumps(data, indent=2)}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection failed. Is the server running on localhost:8000?")
        print("Start server with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_latest_report()