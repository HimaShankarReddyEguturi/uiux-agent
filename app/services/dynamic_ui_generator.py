from typing import Any, Dict, List
import time
import random
import hashlib
from app.schemas import UIReport, UIScreen, UIStyles

class DynamicUIGenerator:
    """Enhanced UI generator with professional dynamic designs"""
    
    def __init__(self):
        self.animation_types = [
            "fade-in-up", "slide-in-left", "slide-in-right", "zoom-in", 
            "bounce-in", "rotate-in", "flip-in-x", "elastic-in"
        ]
        
        self.glassmorphism_styles = [
            {"blur": 20, "opacity": 0.15, "border": "rgba(255,255,255,0.2)"},
            {"blur": 15, "opacity": 0.2, "border": "rgba(255,255,255,0.3)"},
            {"blur": 25, "opacity": 0.1, "border": "rgba(255,255,255,0.15)"},
        ]
        
        self.shadow_presets = [
            "0 10px 40px rgba(0,0,0,0.15)",
            "0 15px 50px rgba(0,0,0,0.2)",
            "0 20px 60px rgba(0,0,0,0.25)",
            "0 8px 32px rgba(0,0,0,0.12)",
        ]
    
    def generate_professional_color_palette(self, content_hash: str) -> Dict[str, str]:
        """Generate professional color palette with time-based variations"""
        # Create unique seed from content + current time
        seed = int(hashlib.sha256(f"{content_hash}{time.time()}".encode()).hexdigest()[:16], 16)
        random.seed(seed)
        
        # Professional color harmonies
        color_harmonies = [
            # Monochromatic with variations
            {"base": random.randint(200, 240), "type": "monochromatic"},
            # Analogous colors
            {"base": random.randint(0, 360), "type": "analogous"},
            # Triadic harmony
            {"base": random.randint(0, 360), "type": "triadic"},
            # Complementary
            {"base": random.randint(0, 360), "type": "complementary"},
            # Split complementary
            {"base": random.randint(0, 360), "type": "split_complementary"},
        ]
        
        harmony = random.choice(color_harmonies)
        base_hue = harmony["base"]
        
        if harmony["type"] == "monochromatic":
            colors = self._generate_monochromatic(base_hue)
        elif harmony["type"] == "analogous":
            colors = self._generate_analogous(base_hue)
        elif harmony["type"] == "triadic":
            colors = self._generate_triadic(base_hue)
        elif harmony["type"] == "complementary":
            colors = self._generate_complementary(base_hue)
        else:
            colors = self._generate_split_complementary(base_hue)
        
        return colors
    
    def _generate_monochromatic(self, base_hue: int) -> Dict[str, str]:
        """Generate monochromatic color scheme"""
        return {
            "primary": self._hsl_to_hex(base_hue, 70, 50),
            "secondary": self._hsl_to_hex(base_hue, 60, 65),
            "accent": self._hsl_to_hex(base_hue, 80, 40),
            "surface": self._hsl_to_hex(base_hue, 20, 95),
            "background": "#F8F9FA"
        }
    
    def _generate_analogous(self, base_hue: int) -> Dict[str, str]:
        """Generate analogous color scheme"""
        return {
            "primary": self._hsl_to_hex(base_hue, 75, 50),
            "secondary": self._hsl_to_hex((base_hue + 30) % 360, 70, 55),
            "accent": self._hsl_to_hex((base_hue - 30) % 360, 80, 45),
            "surface": "#FFFFFF",
            "background": "#F8F9FA"
        }
    
    def _generate_triadic(self, base_hue: int) -> Dict[str, str]:
        """Generate triadic color scheme"""
        return {
            "primary": self._hsl_to_hex(base_hue, 75, 50),
            "secondary": self._hsl_to_hex((base_hue + 120) % 360, 70, 55),
            "accent": self._hsl_to_hex((base_hue + 240) % 360, 80, 45),
            "surface": "#FFFFFF",
            "background": "#F8F9FA"
        }
    
    def _generate_complementary(self, base_hue: int) -> Dict[str, str]:
        """Generate complementary color scheme"""
        return {
            "primary": self._hsl_to_hex(base_hue, 75, 50),
            "secondary": self._hsl_to_hex((base_hue + 180) % 360, 70, 55),
            "accent": self._hsl_to_hex((base_hue + 60) % 360, 80, 45),
            "surface": "#FFFFFF",
            "background": "#F8F9FA"
        }
    
    def _generate_split_complementary(self, base_hue: int) -> Dict[str, str]:
        """Generate split complementary color scheme"""
        return {
            "primary": self._hsl_to_hex(base_hue, 75, 50),
            "secondary": self._hsl_to_hex((base_hue + 150) % 360, 70, 55),
            "accent": self._hsl_to_hex((base_hue + 210) % 360, 80, 45),
            "surface": "#FFFFFF",
            "background": "#F8F9FA"
        }
    
    def _hsl_to_hex(self, h: int, s: int, l: int) -> str:
        """Convert HSL to HEX color"""
        h = h / 360
        s = s / 100
        l = l / 100
        
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def generate_dynamic_gradients(self, colors: Dict[str, str]) -> List[str]:
        """Generate multiple gradient combinations"""
        gradients = [
            f"linear-gradient(135deg, {colors['primary']}, {colors['secondary']})",
            f"linear-gradient(45deg, {colors['secondary']}, {colors['accent']})",
            f"linear-gradient(-45deg, {colors['accent']}, {colors['primary']})",
            f"radial-gradient(circle, {colors['primary']}, {colors['secondary']})",
            f"conic-gradient(from 0deg, {colors['primary']}, {colors['secondary']}, {colors['accent']}, {colors['primary']})",
        ]
        return gradients
    
    def create_enhanced_component(self, component_type: str, colors: Dict[str, str], content: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced component with dynamic styling"""
        base_component = {
            "component": component_type,
            "animation": random.choice(self.animation_types),
            "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        }
        
        if component_type == "gradient_banner":
            gradients = self.generate_dynamic_gradients(colors)
            base_component.update({
                "gradient": random.choice(gradients),
                "height": random.randint(260, 320),
                "title": content.get("title", "Dynamic Title"),
                "subtitle": content.get("subtitle", "Professional subtitle"),
                "overlay": f"rgba(0,0,0,{random.uniform(0.1, 0.3):.2f})",
                "blur_effect": True,
                "text_shadow": "0 2px 4px rgba(0,0,0,0.3)",
                "border_radius": random.randint(20, 32)
            })
        
        elif component_type == "filter_chips":
            glass_style = random.choice(self.glassmorphism_styles)
            base_component.update({
                "items": content.get("items", ["Dynamic", "Professional", "Modern", "Elegant"]),
                "chip_style": {
                    "background": f"rgba(255,255,255,{glass_style['opacity']})",
                    "backdrop_filter": f"blur({glass_style['blur']}px)",
                    "border": f"1px solid {glass_style['border']}",
                    "border_radius": random.randint(20, 30),
                    "padding": "12px 24px",
                    "shadow": random.choice(self.shadow_presets),
                    "hover_transform": "translateY(-2px) scale(1.05)",
                    "active_gradient": random.choice(self.generate_dynamic_gradients(colors))
                }
            })
        
        elif component_type == "event_cards":
            base_component.update({
                "grid_columns": random.choice([2, 3]),
                "cardTitle": content.get("cardTitle", "Dynamic Cards"),
                "card_style": {
                    "background": random.choice(self.generate_dynamic_gradients(colors)),
                    "border_radius": random.randint(20, 32),
                    "shadow": random.choice(self.shadow_presets),
                    "hover_transform": "translateY(-8px) scale(1.02)",
                    "transition": "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                    "overlay": "rgba(255,255,255,0.1)",
                    "text_color": "#FFFFFF"
                }
            })
        
        elif component_type == "elevated_container":
            base_component.update({
                "title": content.get("title", "Enhanced Container"),
                "background": random.choice(self.generate_dynamic_gradients(colors)),
                "border_radius": random.randint(24, 36),
                "shadow": random.choice(self.shadow_presets),
                "padding": random.randint(28, 40),
                "elevation": random.randint(6, 12),
                "backdrop_filter": "blur(10px)"
            })
        
        elif component_type == "section_heading":
            base_component.update({
                "title": content.get("title", "Dynamic Section"),
                "background": colors["primary"],
                "text_color": "#FFFFFF",
                "icon": random.choice(["sparkles", "star", "zap", "trending-up", "award"]),
                "padding": "20px 32px",
                "border_radius": random.randint(16, 24),
                "shadow": random.choice(self.shadow_presets),
                "text_shadow": "0 1px 2px rgba(0,0,0,0.2)"
            })
        
        return base_component
    
    def generate_professional_screens(self, content_analysis: Dict[str, Any]) -> List[UIScreen]:
        """Generate multiple professional screens with dynamic styling"""
        colors = self.generate_professional_color_palette(content_analysis.get("project_name", ""))
        screens = []
        
        # Main Dashboard Screen
        main_screen = UIScreen(
            name=content_analysis.get("sections", ["Main Dashboard"])[0],
            layout={
                "sections": [
                    self.create_enhanced_component("gradient_banner", colors, {
                        "title": content_analysis["project_name"],
                        "subtitle": f"Professional {content_analysis['app_type']} Solution"
                    }),
                    self.create_enhanced_component("filter_chips", colors, {
                        "items": content_analysis["features"][:4]
                    }),
                    self.create_enhanced_component("section_heading", colors, {
                        "title": content_analysis.get("sections", ["Features"])[0] if content_analysis.get("sections") else "Core Features"
                    }),
                    self.create_enhanced_component("event_cards", colors, {
                        "cardTitle": f"{content_analysis['features'][0]} Overview" if content_analysis['features'] else "Feature Overview"
                    }),
                    self.create_enhanced_component("elevated_container", colors, {
                        "title": content_analysis.get("sections", ["Details"])[1] if len(content_analysis.get("sections", [])) > 1 else "Advanced Features"
                    })
                ]
            },
            description=f"Professional {content_analysis['app_type']} dashboard with dynamic UI components"
        )
        screens.append(main_screen)
        
        # Secondary Screens
        for i, feature in enumerate(content_analysis["features"][:3], 1):
            if i >= len(content_analysis.get("sections", [])):
                section_name = f"{feature} Management"
            else:
                section_name = content_analysis["sections"][i]
            
            screen = UIScreen(
                name=section_name,
                layout={
                    "sections": [
                        self.create_enhanced_component("section_heading", colors, {
                            "title": section_name
                        }),
                        self.create_enhanced_component("event_cards", colors, {
                            "cardTitle": f"{feature} Details"
                        }),
                        self.create_enhanced_component("elevated_container", colors, {
                            "title": f"{feature} Configuration"
                        })
                    ]
                },
                description=f"Detailed {feature} management interface"
            )
            screens.append(screen)
        
        return screens
    
    def create_enhanced_ui_report(self, content_analysis: Dict[str, Any]) -> UIReport:
        """Create enhanced UI report with professional dynamic design"""
        colors = self.generate_professional_color_palette(content_analysis.get("project_name", ""))
        screens = self.generate_professional_screens(content_analysis)
        
        styles = UIStyles(
            colors=colors,
            typography={
                "display": "Poppins 800",
                "heading": "Poppins 700", 
                "subheading": "Poppins 600",
                "body": "Inter 500",
                "caption": "Inter 400"
            },
            components=[
                "gradient_banner", "filter_chips", "event_cards", 
                "elevated_container", "section_heading", "rounded_card",
                "bottom_sheet", "floating_action_button"
            ]
        )
        
        return UIReport(
            project_name=content_analysis["project_name"],
            screens=screens,
            styles=styles,
            summary=f"Professional {content_analysis['app_type']} with dynamic UI featuring {', '.join(content_analysis['features'][:3])}"
        )