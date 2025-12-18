#!/usr/bin/env python3
"""
Test script to demonstrate dynamic color generation
Run this to see how colors change each time
"""

import sys
import os
import time

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.dynamic_ui_generator import DynamicUIGenerator

def test_dynamic_colors():
    generator = DynamicUIGenerator()
    
    print("Dynamic Color Generation Test")
    print("=" * 50)
    
    # Test with different project names
    test_projects = [
        "Calculator App",
        "E-commerce Platform", 
        "Healthcare Dashboard",
        "Financial Analytics",
        "Social Media App"
    ]
    
    for i, project in enumerate(test_projects, 1):
        print(f"\n{i}. Project: {project}")
        print("-" * 30)
        
        # Generate colors multiple times to show variation
        for attempt in range(3):
            colors = generator.generate_professional_color_palette(project)
            print(f"  Attempt {attempt + 1}:")
            print(f"    Primary:   {colors['primary']}")
            print(f"    Secondary: {colors['secondary']}")
            print(f"    Accent:    {colors['accent']}")
            
            # Small delay to ensure different timestamps
            time.sleep(0.1)
        
        print()
    
    print("Each run produces unique, professional color schemes!")
    print("Colors are generated based on content + timestamp for true dynamism")

if __name__ == "__main__":
    test_dynamic_colors()