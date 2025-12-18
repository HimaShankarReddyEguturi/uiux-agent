#!/usr/bin/env python3
"""
Demo script showing the complete dynamic UI transformation
"""

import sys
import os
import json
import time

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.dynamic_ui_generator import DynamicUIGenerator

def demo_complete_transformation():
    print("Dynamic UI Transformation Demo")
    print("=" * 50)
    
    generator = DynamicUIGenerator()
    
    # Sample content analysis (simulating PDF extraction)
    sample_content = {
        "project_name": "Advanced Calculator Pro",
        "app_type": "tech app",
        "features": ["Scientific Functions", "Unit Conversion", "History Tracking", "Graph Plotting"],
        "sections": ["Main Calculator", "Scientific Mode", "Settings Panel"],
        "keywords": ["calculation", "mathematics", "precision", "advanced"]
    }
    
    print(f"Sample Project: {sample_content['project_name']}")
    print(f"App Type: {sample_content['app_type']}")
    print(f"Features: {', '.join(sample_content['features'])}")
    print()
    
    # Generate 3 different designs to show variation
    for i in range(3):
        print(f"Design Variation {i + 1}:")
        print("-" * 30)
        
        # Generate enhanced UI report
        ui_report = generator.create_enhanced_ui_report(sample_content)
        
        # Show color scheme
        colors = ui_report.styles.colors
        print(f"  Colors:")
        print(f"    Primary:   {colors.get('primary', 'N/A')}")
        print(f"    Secondary: {colors.get('secondary', 'N/A')}")
        print(f"    Accent:    {colors.get('accent', 'N/A')}")
        
        # Show first screen components
        if ui_report.screens:
            first_screen = ui_report.screens[0]
            print(f"  Screen: {first_screen.name}")
            
            sections = first_screen.layout.get('sections', [])
            if sections:
                print(f"  Components:")
                for section in sections[:3]:  # Show first 3 components
                    component_type = section.get('component', 'unknown')
                    print(f"    - {component_type}")
                    
                    # Show special styling
                    if 'gradient' in section:
                        print(f"      Gradient: {section['gradient'][:50]}...")
                    if 'animation' in section:
                        print(f"      Animation: {section['animation']}")
        
        print()
        time.sleep(0.2)  # Small delay for different timestamps
    
    print("Key Features Demonstrated:")
    print("- Unique color schemes each time")
    print("- Professional component styling")
    print("- Dynamic gradients and effects")
    print("- Content-aware design adaptation")
    print("- Time-based variation system")

def demo_color_harmonies():
    print("\\nColor Harmony Demonstration")
    print("=" * 50)
    
    generator = DynamicUIGenerator()
    
    harmonies = ["Monochromatic", "Analogous", "Triadic", "Complementary", "Split-Complementary"]
    
    for harmony in harmonies:
        print(f"\\n{harmony} Harmony Example:")
        colors = generator.generate_professional_color_palette(f"test_{harmony}_{time.time()}")
        print(f"  Primary:   {colors['primary']}")
        print(f"  Secondary: {colors['secondary']}")
        print(f"  Accent:    {colors['accent']}")

if __name__ == "__main__":
    demo_complete_transformation()
    demo_color_harmonies()
    
    print("\\n" + "=" * 50)
    print("Dynamic UI System Ready!")
    print("Upload any PDF to see professional, unique designs every time.")