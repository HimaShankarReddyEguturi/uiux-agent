#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from app.services.llm import UIAnalyzer

# Load environment variables
load_dotenv()

def test_groq_api():
    print("🧪 Testing Groq API...")
    print(f"API Key: {os.getenv('GROQ_API_KEY')[:20]}..." if os.getenv('GROQ_API_KEY') else "❌ No API key")
    print(f"Model: {os.getenv('GROQ_MODEL')}")
    
    try:
        # Initialize analyzer
        analyzer = UIAnalyzer()
        print("✅ UIAnalyzer initialized successfully")
        
        # Test with simple input
        test_text = "Create a modern e-commerce mobile app with vibrant colors and gradient designs"
        
        print("\n🚀 Calling Groq API...")
        result = analyzer.generate_ui_spec(test_text)
        
        print("✅ LLM Response received!")
        print(f"Project Name: {result.get('project_name', 'N/A')}")
        print(f"Summary: {result.get('summary', 'N/A')}")
        print(f"Number of screens: {len(result.get('screens', []))}")
        print(f"Colors: {result.get('styles', {}).get('colors', {})}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = test_groq_api()
    if result:
        print("\n🎉 SUCCESS: Your Groq LLM is working correctly!")
        print("The JSON schema you saw earlier was NOT from your LLM.")
    else:
        print("\n💥 FAILED: Check your API key and connection.")