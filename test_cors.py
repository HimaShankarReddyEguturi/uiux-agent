#!/usr/bin/env python3
"""
Test script to verify CORS configuration for PDF to JSON conversion
"""

import requests
import json

def test_cors_headers():
    """Test CORS headers on the latest-report endpoint"""
    url = "http://localhost:8000/latest-report"
    
    try:
        # Test OPTIONS request (preflight)
        print("Testing OPTIONS request...")
        options_response = requests.options(url)
        print(f"OPTIONS Status: {options_response.status_code}")
        print("CORS Headers:")
        for header, value in options_response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        # Test GET request
        print("\nTesting GET request...")
        get_response = requests.get(url)
        print(f"GET Status: {get_response.status_code}")
        print("CORS Headers:")
        for header, value in get_response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if get_response.status_code == 200:
            data = get_response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_upload_endpoint():
    """Test the upload endpoint"""
    url = "http://localhost:8000/health"
    
    try:
        response = requests.get(url)
        print(f"\nHealth check status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health data: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    print("🔍 Testing CORS Configuration for PDF to JSON API")
    print("=" * 50)
    test_cors_headers()
    test_upload_endpoint()
    print("\n✅ CORS test completed")