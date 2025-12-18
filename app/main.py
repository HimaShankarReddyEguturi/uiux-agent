# app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.services.parser import extract_text_from_bytes
from app.services.llm import UIAnalyzer
from app.services.figma_client import FigmaClient
from app.schemas import UIReport, UIReportResponse
import os
import json
import webbrowser
import threading

load_dotenv()

# Initialize LLM analyzer (supports both Groq and Gemini)
analyzer = UIAnalyzer()

# Initialize Figma client
figma_client = FigmaClient()

# --------------------------------------------
# LLM ANALYSIS → project name
# --------------------------------------------
def extract_project_name(text: str) -> str:
    try:
        import re
        import hashlib
        from datetime import datetime
        
        text_lower = text.lower()
        lines = [line.strip() for line in text.split('\n')[:50] if line.strip()]
        
        # Enhanced explicit project name patterns
        explicit_patterns = [
            r'(?:Product|Project|Application|App|System|Platform|Tool)\s*Name\s*:?\s*["\']?([A-Za-z][A-Za-z0-9\s&-]{2,35})["\']?',
            r'(?:Product|Project|Application|App|System|Platform|Tool)\s*:?\s*["\']?([A-Za-z][A-Za-z0-9\s&-]{2,35})["\']?',
            r'PRD\s*(?:for|of)?\s*:?\s*["\']?([A-Za-z][A-Za-z0-9\s&-]{2,35})["\']?',
            r'Title\s*:?\s*["\']?([A-Za-z][A-Za-z0-9\s&-]{2,35})["\']?',
            r'Name\s*:?\s*["\']?([A-Za-z][A-Za-z0-9\s&-]{2,35})["\']?',
            r'([A-Za-z][A-Za-z0-9\s&-]*(?:Calculator|App|Application|System|Platform|Tool|Manager|Portal|Dashboard))',
            r'"([A-Za-z][A-Za-z0-9\s&-]{3,35})"',
            r"'([A-Za-z][A-Za-z0-9\s&-]{3,35})'"
        ]
        
        # Search for explicit names in first 1000 characters
        for pattern in explicit_patterns:
            matches = re.findall(pattern, text[:1000], re.IGNORECASE)
            for match in matches:
                name = match.strip().title()
                name = re.sub(r'\s+', ' ', name).strip()
                # Filter out generic words and sentence fragments
                if (3 <= len(name) <= 35 and 
                    not any(skip in name.lower() for skip in ['document', 'page', 'section', 'prd', 'requirements', 'specification', 'the', 'and', 'for', 'is', 'to', 'provide', 'reliable', 'will', 'can', 'should', 'must'])):
                    return name
        
        # Look for titles in first lines (enhanced)
        for i, line in enumerate(lines[:15]):
            if 3 <= len(line) <= 50:
                # Skip metadata and common document words
                skip_words = ['http', 'www', '@', 'page', 'document', 'pdf', 'version', 'date', 'created', 'modified', 'author', 'subject']
                if any(skip in line.lower() for skip in skip_words):
                    continue
                
                # Check if line looks like a title (enhanced detection)
                if (line.istitle() or line.isupper() or 
                    re.match(r'^[A-Z][a-zA-Z0-9\s&-]+$', line) or
                    (i < 5 and len(line.split()) <= 6)):
                    
                    clean_title = re.sub(r'[^A-Za-z0-9\s&-]', ' ', line).strip()
                    clean_title = re.sub(r'\s+', ' ', clean_title)
                    
                    if (3 <= len(clean_title) <= 35 and 
                        not any(skip in clean_title.lower() for skip in ['document', 'page', 'section', 'requirements', 'is', 'to', 'provide', 'reliable', 'will', 'can', 'should', 'must'])):
                        return clean_title.title()
        
        # Extract domain-specific names with context
        domain_patterns = {
            'calculator': [
                r'([A-Za-z]+\s*Calculator)',
                r'([A-Za-z]+\s*Math\s*[A-Za-z]*)',
                r'(Scientific\s*[A-Za-z]*)',
                r'(Advanced\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Computation\s*[A-Za-z]*)'
            ],
            'chat': [
                r'([A-Za-z]+\s*(?:Chat|Messenger|Message))',
                r'([A-Za-z]+\s*Communication)',
                r'(Instant\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Talk\s*[A-Za-z]*)'
            ],
            'ecommerce': [
                r'([A-Za-z]+\s*(?:Shop|Store|Market))',
                r'([A-Za-z]+\s*Commerce)',
                r'([A-Za-z]+\s*Retail)',
                r'(Online\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Buy\s*[A-Za-z]*)'
            ],
            'banking': [
                r'([A-Za-z]+\s*(?:Bank|Finance|Pay))',
                r'([A-Za-z]+\s*Wallet)',
                r'([A-Za-z]+\s*Transaction)',
                r'(Digital\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Money\s*[A-Za-z]*)'
            ],
            'health': [
                r'([A-Za-z]+\s*(?:Health|Medical|Care))',
                r'([A-Za-z]+\s*Doctor)',
                r'([A-Za-z]+\s*Patient)',
                r'(Medical\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Clinic\s*[A-Za-z]*)'
            ],
            'food': [
                r'([A-Za-z]+\s*(?:Food|Restaurant|Recipe))',
                r'([A-Za-z]+\s*Kitchen)',
                r'([A-Za-z]+\s*Delivery)',
                r'(Fresh\s*[A-Za-z]*)',
                r'([A-Za-z]*\s*Meal\s*[A-Za-z]*)'
            ]
        }
        
        # Detect domain and extract specific names
        for domain, patterns in domain_patterns.items():
            if any(keyword in text_lower for keyword in [domain, domain.replace('ecommerce', 'shop')]):
                for pattern in patterns:
                    matches = re.findall(pattern, text[:800], re.IGNORECASE)
                    if matches:
                        name = matches[0].strip().title()
                        name = re.sub(r'\s+', ' ', name)
                        if 3 <= len(name) <= 30:
                            return name
        
        # Extract meaningful compound words and phrases
        compound_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b',  # CamelCase
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',  # Title Case phrases
            r'\b([A-Za-z]+[-_][A-Za-z]+)\b',  # Hyphenated/underscore
        ]
        
        for pattern in compound_patterns:
            matches = re.findall(pattern, text[:600])
            for match in matches:
                clean_match = re.sub(r'[-_]', ' ', match).title()
                if (3 <= len(clean_match) <= 30 and 
                    not any(skip in clean_match.lower() for skip in ['the', 'and', 'for', 'with', 'this', 'that'])):
                    return clean_match
        
        # Extract unique words and create meaningful combinations
        words = re.findall(r'\b[A-Z][a-z]{2,15}\b', text[:500])
        filtered_words = []
        
        # Enhanced word filtering
        skip_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'document', 'page', 'section', 
            'requirements', 'specification', 'description', 'overview', 'introduction',
            'chapter', 'part', 'appendix', 'figure', 'table', 'example', 'note'
        }
        
        for word in words:
            if (word.lower() not in skip_words and 
                len(word) >= 3 and 
                not word.lower().endswith('ing') and
                not word.lower().endswith('tion')):
                filtered_words.append(word)
        
        # Remove duplicates while preserving order
        unique_words = []
        seen = set()
        for word in filtered_words:
            if word.lower() not in seen:
                unique_words.append(word)
                seen.add(word.lower())
        
        # Create meaningful combinations
        if len(unique_words) >= 2:
            # Try different combinations
            combinations = [
                f"{unique_words[0]} {unique_words[1]}",
                f"{unique_words[0]} App",
                f"{unique_words[1]} System",
                f"{unique_words[0]} Platform"
            ]
            
            for combo in combinations:
                if len(combo) <= 30:
                    return combo
        
        elif len(unique_words) == 1:
            word = unique_words[0]
            # Add contextual suffix based on content
            if any(tech in text_lower for tech in ['api', 'service', 'backend']):
                return f"{word} Service"
            elif any(ui in text_lower for ui in ['ui', 'interface', 'frontend']):
                return f"{word} Interface"
            elif any(mobile in text_lower for mobile in ['mobile', 'app', 'android', 'ios']):
                return f"{word} App"
            else:
                return f"{word} System"
        
        # Content-based unique naming with timestamp
        content_words = re.findall(r'\b[a-zA-Z]{4,10}\b', text[:200])
        if content_words:
            # Use first meaningful word + timestamp for uniqueness
            base_word = content_words[0].title()
            timestamp = datetime.now().strftime("%m%d")
            return f"{base_word} App {timestamp}"
        
        # Final fallback with content hash for uniqueness
        content_hash = hashlib.md5(text[:200].encode()).hexdigest()[:6]
        return f"Project {content_hash.upper()}"
        
    except Exception as e:
        # Even fallback should be unique
        import time
        timestamp = str(int(time.time()))[-4:]
        return f"App {timestamp}"

# --------------------------------------------
# FIGMA API INTEGRATION
# --------------------------------------------
import requests
import datetime
import uuid
import time
import urllib.parse



def create_unique_filename(project_name: str, domain: str) -> str:
    """Create unique filename with domain prefix and timestamp"""
    # Generate prefix from domain dynamically
    prefix = domain[:4].upper() if len(domain) >= 4 else domain.upper()
    
    # Create timestamp
    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    
    # Create unique ID
    unique_id = str(uuid.uuid4())[:6]
    
    # Build unique name
    return f"[{prefix}] {project_name} - {timestamp} - {unique_id}"



# --------------------------------------------
# BUILD UI REPORT WITH LLM ANALYSIS (Groq/Gemini)
# --------------------------------------------
def detect_domain_from_text(text: str) -> str:
    """Dynamically detect domain from PDF content - extracts actual domain from text"""
    import re
    from collections import Counter
    
    text_lower = text.lower()
    
    # Extract domain-related nouns and phrases (what the app is ABOUT)
    domain_indicators = []
    
    # Pattern 1: "X app", "X application", "X platform", "X system"
    app_patterns = re.findall(r'\b([a-z]+)\s+(?:app|application|platform|system|service|tool|portal|software)\b', text_lower)
    domain_indicators.extend(app_patterns)
    
    # Pattern 2: "for X", "X management", "X solution"
    for_patterns = re.findall(r'\bfor\s+([a-z]+(?:\s+[a-z]+){0,2})\b', text_lower)
    domain_indicators.extend([p.strip() for p in for_patterns])
    
    management_patterns = re.findall(r'\b([a-z]+)\s+(?:management|solution|service)\b', text_lower)
    domain_indicators.extend(management_patterns)
    
    # Pattern 3: Common action verbs that indicate domain
    action_patterns = re.findall(r'\b(?:book|order|buy|sell|track|manage|schedule|reserve|deliver|browse|search|chat|message|pay|transfer|learn|teach|diagnose|treat)\s+([a-z]+)\b', text_lower)
    domain_indicators.extend(action_patterns)
    
    # Pattern 4: Industry-specific terms (first 500 chars for context)
    industry_terms = re.findall(r'\b([a-z]{5,15})\b', text_lower[:500])
    domain_indicators.extend(industry_terms)
    
    # Filter out common words
    stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'will', 'been', 'were', 
                  'their', 'there', 'would', 'could', 'should', 'about', 'which', 'these', 'those',
                  'document', 'requirements', 'specification', 'business', 'technical', 'user', 'system'}
    
    filtered_indicators = [word for word in domain_indicators if word not in stop_words and len(word) > 3]
    
    # Count frequency and get top domain indicators
    if filtered_indicators:
        word_counts = Counter(filtered_indicators)
        top_words = word_counts.most_common(3)
        
        # Use most frequent word as domain
        if top_words:
            domain = top_words[0][0]
            # Clean up domain name
            domain = domain.replace(' ', '_').strip()
            return domain
    
    # Fallback: Extract from title or first meaningful line
    lines = [line.strip() for line in text.split('\n')[:20] if line.strip()]
    for line in lines:
        # Look for "X App" or "X System" in titles
        title_match = re.search(r'\b([A-Za-z]+)\s+(?:App|Application|Platform|System)', line, re.IGNORECASE)
        if title_match:
            return title_match.group(1).lower()
    
    # Final fallback: Use most common meaningful noun
    nouns = re.findall(r'\b[a-z]{5,12}\b', text_lower[:1000])
    filtered_nouns = [n for n in nouns if n not in stop_words]
    if filtered_nouns:
        noun_counts = Counter(filtered_nouns)
        return noun_counts.most_common(1)[0][0]
    
    return 'application'

def extract_detailed_pdf_content(text: str) -> dict:
    """Extract comprehensive details from PDF content - focuses on app features, not document structure"""
    import re
    
    # Skip document metadata headings
    skip_headings = ['business requirements', 'user personas', 'technical specs', 'technical specifications', 
                     'security requirements', 'introduction', 'overview', 'conclusion', 'appendix']
    
    def is_document_heading(line: str) -> bool:
        """Check if line is a document heading (not app content)"""
        line_lower = line.lower().strip()
        return (line.isupper() or line.endswith(':') or 
                any(heading in line_lower for heading in skip_headings))
    
    # Extract bullet points and features (actual content)
    lines = text.split('\n')
    features = []
    workflows = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Skip document headings
        if is_document_heading(line):
            continue
        
        # Extract bullet points (actual features)
        if re.match(r'^[•\-\*]\s+(.+)', line):
            content = re.sub(r'^[•\-\*]\s+', '', line).strip()
            if len(content) > 10 and not is_document_heading(content):
                features.append(content)
        
        # Extract numbered items (workflows/steps)
        elif re.match(r'^\d+[\.\)]\s+(.+)', line):
            content = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
            if len(content) > 10 and not is_document_heading(content):
                workflows.append(content)
        
        # Extract action-oriented sentences (user can...)
        elif re.search(r'\b(can|will|should|able to|allows|enables)\b', line, re.IGNORECASE):
            if len(line) > 15 and not is_document_heading(line):
                features.append(line)
    
    # Extract user personas (actual roles, not headings)
    persona_patterns = [
        r'(?:as\s+a|as\s+an)\s+([a-z]+(?:\s+[a-z]+){0,2})',
        r'\b(customer|user|admin|manager|student|teacher|doctor|patient|buyer|seller|driver|rider)s?\b'
    ]
    personas = set()
    for pattern in persona_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        personas.update([m.strip().title() for m in matches if len(m.strip()) > 2])
    
    # Extract technical specs (actual technologies, not headings)
    tech_patterns = [
        r'\b(React|Angular|Vue|Python|Java|Node\.?js|MongoDB|PostgreSQL|MySQL|AWS|Azure|Docker|Kubernetes)\b',
        r'(?:using|built with|powered by|based on)\s+([A-Z][a-zA-Z\s]{3,25})'
    ]
    tech_specs = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        tech_specs.update([m.strip() for m in matches if len(m.strip()) > 2])
    
    # Extract data entities dynamically from PDF content
    entities = set()
    
    # Extract nouns after "the", "a", "an" (most reliable for concrete nouns)
    article_nouns = re.findall(r'\b(?:the|a|an)\s+([a-z]{4,15})\b', text.lower())
    entities.update([n.title() for n in article_nouns])
    
    # Extract common entity patterns (Class-like names)
    entity_patterns = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text)  # CamelCase
    entities.update(entity_patterns)
    
    # Filter out verbs, adjectives, months, and error terms
    verb_endings = {'ing', 'tion', 'ment', 'ance', 'ence', 'ness', 'ship', 'ity', 'age', 'ism', 'ed', 'ate'}
    months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'}
    error_terms = {'corrupted', 'malformed', 'invalid', 'error', 'warning', 'failed', 'missing'}
    ui_generic = {'widget', 'control', 'button', 'label', 'input', 'field', 'form', 'panel', 'dialog'}
    stop_words = {'user', 'users', 'system', 'application', 'feature', 'function', 'requirement', 'specification', 
                  'document', 'section', 'page', 'overview', 'summary', 'introduction', 'conclusion',
                  'maintain', 'maintains', 'reflect', 'reflects', 'working', 'adjustment', 'metric', 'metrics',
                  'process', 'method', 'approach', 'strategy', 'concept', 'principle', 'aspect', 'factor', 'load'}
    
    entities = {e for e in entities 
                if e.lower() not in stop_words 
                and e.lower() not in months
                and e.lower() not in error_terms
                and e.lower() not in ui_generic
                and len(e) >= 4 
                and not any(e.lower().endswith(ending) for ending in verb_endings)}
    
    # If no entities found, extract from features
    if not entities and features:
        # Extract key nouns from features
        for feature in features[:3]:
            words = re.findall(r'\b([A-Z][a-z]{4,12})\b', feature)
            entities.update(words[:2])
    
    return {
        'business_requirements': features[:8] if features else ['Core app functionality'],
        'user_personas': list(personas)[:6] if personas else ['User'],
        'technical_specs': list(tech_specs)[:8] if tech_specs else ['Modern web stack'],
        'workflows': workflows[:6] if workflows else ['User interaction flow'],
        'data_entities': list(entities)[:6] if entities else ['Data', 'Content'],
        'security_requirements': ['Authentication', 'Data protection']
    }

def extract_colors_from_pdf(text: str) -> str:
    """Extract colors from PDF, generate dynamic colors if none found"""
    import re
    import random
    
    color_patterns = {
        'primary': [r'primary\s*:?\s*(#[0-9A-Fa-f]{6})', r'Primary\s*:?\s*(#[0-9A-Fa-f]{6})', r'PRIMARY\s*:?\s*(#[0-9A-Fa-f]{6})', r'main\s*color\s*:?\s*(#[0-9A-Fa-f]{6})', r'brand\s*color\s*:?\s*(#[0-9A-Fa-f]{6})'],
        'secondary': [r'secondary\s*:?\s*(#[0-9A-Fa-f]{6})', r'Secondary\s*:?\s*(#[0-9A-Fa-f]{6})', r'SECONDARY\s*:?\s*(#[0-9A-Fa-f]{6})'],
        'accent': [r'accent\s*:?\s*(#[0-9A-Fa-f]{6})', r'Accent\s*:?\s*(#[0-9A-Fa-f]{6})', r'ACCENT\s*:?\s*(#[0-9A-Fa-f]{6})', r'highlight\s*:?\s*(#[0-9A-Fa-f]{6})'],
        'background': [r'background\s*:?\s*(#[0-9A-Fa-f]{6})', r'Background\s*:?\s*(#[0-9A-Fa-f]{6})', r'BACKGROUND\s*:?\s*(#[0-9A-Fa-f]{6})']
    }
    
    extracted_colors = {}
    for color_type, patterns in color_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                extracted_colors[color_type] = matches[0]
                break
    
    all_hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', text)
    if all_hex_colors and len(extracted_colors) < 3:
        if 'primary' not in extracted_colors and len(all_hex_colors) > 0:
            extracted_colors['primary'] = all_hex_colors[0]
        if 'secondary' not in extracted_colors and len(all_hex_colors) > 1:
            extracted_colors['secondary'] = all_hex_colors[1]
        if 'accent' not in extracted_colors and len(all_hex_colors) > 2:
            extracted_colors['accent'] = all_hex_colors[2]
    
    if extracted_colors:
        color_parts = [f"{k}: {v}" for k, v in extracted_colors.items()]
        return f"PDF-specified colors - {', '.join(color_parts)}"
    
    # Generate dynamic random colors
    def generate_color():
        return f"#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}"
    
    primary = generate_color()
    secondary = generate_color()
    accent = generate_color()
    
    return f"Dynamic colors - primary: {primary}, secondary: {secondary}, accent: {accent}"

# Enhanced dynamic prompt generation
def generate_dynamic_prompt(text: str, project_name: str, domain: str) -> str:
    """Generate detailed context-aware prompt with comprehensive PDF analysis"""
    # Extract detailed content
    detailed_content = extract_detailed_pdf_content(text)
    
    # Original screen and feature detection
    screen_keywords = ["login", "signup", "home", "dashboard", "profile", "cart", "checkout", "menu", "search", "settings", "booking", "payment"]
    screens = [s for s in screen_keywords if s in text.lower()][:5]
    
    feature_keywords = ["search", "filter", "payment", "notification", "chat", "map", "calendar", "upload", "analytics"]
    features = [f for f in feature_keywords if f in text.lower()][:6]
    
    # Extract PDF colors first - now always returns colors
    pdf_colors = extract_colors_from_pdf(text)
    
    # Domain-specific colors and styles - PDF colors will always be used now
    domain_configs = {
        "security": {
            "colors": pdf_colors,
            "style": "secure, alert-focused, vulnerability-oriented with clear status indicators",
            "screens": screens if screens else ["scan", "vulnerabilities", "reports", "settings"]
        },
        "development": {
            "colors": pdf_colors,
            "style": "code-focused, analytical, developer-friendly with syntax highlighting",
            "screens": screens if screens else ["analysis", "code", "reports", "settings"]
        },
        "calculator": {
            "colors": pdf_colors,
            "style": "clean, functional, number-focused with clear operation buttons",
            "screens": screens if screens else ["calculator", "operations", "history", "settings"]
        },
        "chat": {
            "colors": pdf_colors,
            "style": "friendly, conversational, message-focused",
            "screens": screens if screens else ["chats", "contacts", "profile", "settings"]
        },
        "productivity": {
            "colors": pdf_colors,
            "style": "organized, efficient, task-focused",
            "screens": screens if screens else ["tasks", "calendar", "projects", "settings"]
        },
        "food": {
            "colors": pdf_colors,
            "style": "appetizing, warm, inviting with food imagery",
            "screens": screens if screens else ["browse", "restaurant", "cart", "checkout", "tracking"]
        },
        "healthcare": {
            "colors": pdf_colors,
            "style": "clean, trustworthy, accessible with health icons",
            "screens": screens if screens else ["booking", "dashboard", "records", "consultation"]
        },
        "fintech": {
            "colors": pdf_colors,
            "style": "secure, professional, data-focused with charts",
            "screens": screens if screens else ["dashboard", "transactions", "transfer", "analytics"]
        },
        "ecommerce": {
            "colors": pdf_colors,
            "style": "attractive, product-focused, easy navigation",
            "screens": screens if screens else ["home", "products", "cart", "checkout"]
        },
        "education": {
            "colors": pdf_colors,
            "style": "engaging, clear, progress-oriented",
            "screens": screens if screens else ["courses", "dashboard", "lessons", "profile"]
        }
    }
    
    config = domain_configs.get(domain, {
        "colors": pdf_colors,
        "style": "clean, modern, user-friendly",
        "screens": screens if screens else ["home", "dashboard", "profile"]
    })
    
    # Build navigation flow
    screen_list = config["screens"]
    navigation_instructions = "\n".join([
        f"- Screen {i+1} ({screen.upper()}): Add buttons/cards that navigate to Screen {i+2 if i+1 < len(screen_list) else 1} on click"
        for i, screen in enumerate(screen_list)
    ])
    
    # Extract detailed content for enhanced prompting
    detailed_content = extract_detailed_pdf_content(text)
    
    prompt = f"""Design UI for '{project_name}'.

=== EXTRACTED PDF CONTENT ===
BUSINESS REQUIREMENTS:
{chr(10).join([f'• {req}' for req in detailed_content['business_requirements'][:5]]) if detailed_content['business_requirements'] else '• Core business functionality'}

USER PERSONAS/ROLES:
{', '.join(detailed_content['user_personas'][:4]) if detailed_content['user_personas'] else 'General Users'}

TECHNICAL SPECIFICATIONS:
{chr(10).join([f'• {spec}' for spec in detailed_content['technical_specs'][:4]]) if detailed_content['technical_specs'] else '• Standard web technologies'}

WORKFLOWS/PROCESSES:
{chr(10).join([f'• {flow}' for flow in detailed_content['workflows'][:4]]) if detailed_content['workflows'] else '• Standard user workflows'}

DATA ENTITIES:
{', '.join(detailed_content['data_entities'][:6]) if detailed_content['data_entities'] else 'User, Content, Settings'}

SECURITY REQUIREMENTS:
{chr(10).join([f'• {sec}' for sec in detailed_content['security_requirements'][:3]]) if detailed_content['security_requirements'] else '• Standard authentication'}

=== UI DESIGN SPECIFICATIONS ===
COLOR SCHEME (APPLY TO ALL COMPONENTS):
{config['colors']}

DESIGN STYLE:
{config['style']}

SCREENS: {', '.join(screen_list)}
FEATURES: {', '.join(features) if features else 'core functionality'}

NAVIGATION:
{navigation_instructions}

COLOR APPLICATION (CRITICAL):
1. gradient_banner: gradient primary→secondary, WHITE text, text_shadow
2. filter_chips: accent color background, WHITE text
3. event_cards: gradient secondary→accent, WHITE text on gradient
4. section_heading: primary color background, WHITE text
5. elevated_container: gradient accent→primary, WHITE text
6. floating_action_button: gradient primary→secondary, WHITE icon
7. All buttons: primary color, WHITE text
8. All cards: box_shadow with primary color

TEXT RULES:
- ALL text on colored backgrounds MUST be WHITE
- Headings on gradients: WHITE with shadow
- Never dark text on dark backgrounds

INTERACTIONS:
- onClick navigation between screens
- Gradient backgrounds on ALL components
- Hover states (lighten 10%)
- 300ms transitions

=== CONTENT INTEGRATION ===
Incorporate the extracted business requirements, user personas, and workflows into the UI design.
Create screens that reflect the actual processes and data entities found in the PDF.
Ensure the design supports the identified technical specifications and security requirements.

Document Content: {text[:1000]}

REQUIRED: Create a UI that reflects the ACTUAL PDF content, not generic templates."""
    
    return prompt

def build_ui_report(project_name: str, text: str, domain: str = "ecommerce") -> tuple:
    try:
        # Extract detailed content for enhanced reporting
        detailed_content = extract_detailed_pdf_content(text)
        
        # Generate enhanced prompt
        dynamic_prompt = generate_dynamic_prompt(text, project_name, domain)
        ui_data = analyzer.generate_ui_spec(dynamic_prompt)
        
        if not ui_data or not ui_data.get("screens"):
            raise ValueError("LLM returned empty or invalid response")
        
        # FORCE correct screen names from extracted features
        features = detailed_content['business_requirements']
        if features and len(features) > 0:
            # Override LLM-generated screen names with actual features
            for i, screen in enumerate(ui_data.get("screens", [])[:5]):
                if i < len(features):
                    # Replace screen name with actual feature
                    screen['name'] = f"{features[i][:50]} Screen"
                    screen['description'] = f"{features[i]} for {project_name}"
        
        # Generate dynamic summary from extracted features
        features_summary = ', '.join(detailed_content['business_requirements'][:3]) if detailed_content['business_requirements'] else 'core functionality'
        enhanced_summary = f"""{domain.title()} app with {features_summary}
        
📋 BUSINESS REQUIREMENTS: {len(detailed_content['business_requirements'])} identified
👥 USER PERSONAS: {', '.join(detailed_content['user_personas'][:3]) if detailed_content['user_personas'] else 'General Users'}
⚙️ TECHNICAL SPECS: {len(detailed_content['technical_specs'])} specifications
🔄 WORKFLOWS: {len(detailed_content['workflows'])} processes identified
🗃️ DATA ENTITIES: {', '.join(detailed_content['data_entities'][:4]) if detailed_content['data_entities'] else 'Standard entities'}
🔒 SECURITY: {len(detailed_content['security_requirements'])} requirements"""
            
        report = UIReport(
            project_name=ui_data.get("project_name", project_name),
            summary=enhanced_summary,
            screens=ui_data.get("screens", []),
            styles=ui_data.get("styles", {}),
            navigation_flow=ui_data.get("navigation_flow", []),
            prototype_settings=ui_data.get("prototype_settings", {})
        )
        return report, dynamic_prompt
    except Exception as e:
        print(f"LLM Error: {e}")
        retry_prompt = f"Create a UI for: {project_name}. Context: {text[:1000]}"
        ui_data = analyzer.generate_ui_spec(retry_prompt)
        report = UIReport(
            project_name=ui_data.get("project_name", project_name),
            summary=ui_data.get("summary", "AI-generated UI specification"),
            screens=ui_data.get("screens", []),
            styles=ui_data.get("styles", {}),
            navigation_flow=ui_data.get("navigation_flow", []),
            prototype_settings=ui_data.get("prototype_settings", {})
        )
        return report, retry_prompt

# --------------------------------------------
# FASTAPI APP
# --------------------------------------------
app = FastAPI()

# Add CORS middleware with specific configuration for Figma plugin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://www.figma.com",
        "https://figma.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "*",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin"
    ],
)

# --------------------------------------------
# Chrome DevTools endpoint (silences 404 errors)
# --------------------------------------------
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def devtools():
    return {}

@app.get("/upload-and-report", response_class=HTMLResponse)
async def upload_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF to Figma Generator</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c, #4facfe, #00f2fe);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 32px;
                padding: 48px;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.3);
                max-width: 520px;
                width: 100%;
                text-align: center;
                animation: fadeInUp 0.8s ease;
            }
            
            .logo { 
                font-size: 56px; 
                margin-bottom: 16px;
                animation: pulse 2s ease-in-out infinite;
                filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
            }
            
            h1 { 
                color: #ffffff; 
                font-size: 32px; 
                font-weight: 800; 
                margin-bottom: 12px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                background: linear-gradient(135deg, #ffffff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .subtitle { 
                color: rgba(255, 255, 255, 0.9); 
                font-size: 18px; 
                margin-bottom: 40px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .upload-area {
                border: 2px dashed rgba(255, 255, 255, 0.4);
                border-radius: 24px;
                padding: 48px 24px;
                margin-bottom: 32px;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
            }
            
            .upload-area::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }
            
            .upload-area:hover {
                border-color: rgba(255, 255, 255, 0.8);
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-4px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            }
            
            .upload-area:hover::before {
                left: 100%;
            }
            
            .upload-icon { 
                font-size: 56px; 
                color: rgba(255, 255, 255, 0.8); 
                margin-bottom: 20px;
                filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
            }
            
            .upload-text { 
                color: rgba(255, 255, 255, 0.95); 
                font-size: 18px; 
                font-weight: 600;
                margin-bottom: 8px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .upload-hint { 
                color: rgba(255, 255, 255, 0.7); 
                font-size: 14px;
            }
            
            #file-input { display: none; }
            
            .file-info {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                padding: 20px;
                margin-bottom: 32px;
                display: none;
                backdrop-filter: blur(10px);
                animation: fadeInUp 0.5s ease;
            }
            
            .file-name { 
                color: #ffffff; 
                font-weight: 700; 
                margin-bottom: 6px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .file-size { 
                color: rgba(255, 255, 255, 0.8); 
                font-size: 14px;
            }
            
            .generate-btn {
                background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
                background-size: 300% 300%;
                animation: gradientShift 3s ease infinite;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                width: 100%;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
                position: relative;
                overflow: hidden;
            }
            
            .generate-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                transition: left 0.5s;
            }
            
            .generate-btn:hover {
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
            }
            
            .generate-btn:hover::before {
                left: 100%;
            }
            
            .generate-btn:active {
                transform: translateY(-1px) scale(0.98);
            }
            
            .generate-btn:disabled { 
                opacity: 0.6; 
                cursor: not-allowed;
                transform: none;
            }
            
            .loading { 
                display: none; 
                color: rgba(255, 255, 255, 0.9); 
                font-size: 16px; 
                margin-top: 20px;
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            .result {
                display: none;
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                padding: 24px;
                margin-top: 32px;
                backdrop-filter: blur(10px);
                animation: fadeInUp 0.6s ease;
            }
            
            .result h3 {
                color: #ffffff;
                margin-bottom: 12px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .result p {
                color: rgba(255, 255, 255, 0.9);
                margin-bottom: 16px;
            }
            
            .figma-link { 
                color: #ffffff; 
                text-decoration: none; 
                font-weight: 700;
                word-break: break-all;
                background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
                padding: 12px 24px;
                border-radius: 12px;
                display: inline-block;
                transition: all 0.3s ease;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .figma-link:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🎨</div>
            <h1>UI/UX Agent</h1>
            <p class="subtitle">Transform documents into stunning, dynamic UI designs with professional color schemes</p>
            
            <form id="upload-form" action="/upload-and-report" method="post" enctype="multipart/form-data">
                <div class="upload-area" onclick="document.getElementById('file-input').click()">
                    <div class="upload-icon">📄</div>
                    <div class="upload-text">Click to upload or drag and drop</div>
                    <div class="upload-hint">PDF, DOCX files supported</div>
                    <input type="file" id="file-input" name="file" accept=".pdf,.docx,.doc" required>
                </div>
                
                <div class="file-info" id="file-info">
                    <div class="file-name" id="file-name"></div>
                    <div class="file-size" id="file-size"></div>
                </div>
                
                <button type="submit" class="generate-btn" id="generate-btn" disabled>
                    🚀 Generate Figma Design
                </button>
                
                <div class="loading" id="loading">⏳ Analyzing document and generating design...</div>
                <div class="result" id="result">
                    <h3>✅ Design Generated Successfully!</h3>
                    <p>Your Figma design is ready:</p>
                    <a href="#" id="figma-link" class="figma-link" target="_blank">Open Figma Design</a>
                </div>
            </form>
        </div>
        
        <script>
            const fileInput = document.getElementById('file-input');
            const fileInfo = document.getElementById('file-info');
            const fileName = document.getElementById('file-name');
            const fileSize = document.getElementById('file-size');
            const generateBtn = document.getElementById('generate-btn');
            
            fileInput.addEventListener('change', function() {
                const file = this.files[0];
                if (file) {
                    fileName.textContent = file.name;
                    fileSize.textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
                    fileInfo.style.display = 'block';
                    generateBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """

# --------------------------------------------
# POST Endpoint (Generate Figma Link + Report)
# --------------------------------------------
@app.post("/upload-and-report")
async def create_upload_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    text = extract_text_from_bytes(file_bytes, file.content_type)
    
    if not text.strip():
        text = "Create a modern mobile application"

    # Use uploaded filename as project name
    import os
    import html
    project_name = os.path.splitext(file.filename)[0].replace('_', ' ').replace('-', ' ').title()
    domain = detect_domain_from_text(text)
    
    report, prompt_used = build_ui_report(project_name, text, domain)
    
    # Create unique filename for Figma
    unique_project_name = create_unique_filename(project_name, domain)
    
    # Create Figma file with error handling
    try:
        figma_url = figma_client.create_figma_file(unique_project_name)
    except Exception as e:
        print(f"Figma API error: {e}")
        figma_url = None
    
    global latest_report_data, latest_prompt_used
    latest_report_data = report.dict()
    latest_prompt_used = prompt_used
    
    # Generate HTML response with styled UI Report and Prompt
    report_dict = report.dict()
    screens_html = ''.join([
        f'''<div class="screen-card">
            <div class="screen-icon">🎨</div>
            <h3>{screen.get("name", "Screen")}</h3>
            <p>{screen.get("description", "No description")[:150]}...</p>
        </div>'''
        for screen in report_dict.get('screens', [])[:6]
    ])
    
    colors = report_dict.get('styles', {}).get('colors', {})
    primary = colors.get('primary', '#667eea')
    secondary = colors.get('secondary', '#764ba2')
    escaped_prompt = html.escape(prompt_used)
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UI Report - {report_dict.get('project_name', 'Project')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', -apple-system, sans-serif;
                background: linear-gradient(135deg, {primary}, {secondary});
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            
            .section {{
                background: rgba(255, 255, 255, 0.95);
                border-radius: 24px;
                padding: 40px;
                margin-bottom: 32px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            }}
            
            .section-title {{
                font-size: 32px;
                font-weight: 800;
                color: {primary};
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .project-title {{
                font-size: 42px;
                font-weight: 800;
                color: {primary};
                margin-bottom: 16px;
            }}
            
            .summary {{
                font-size: 16px;
                color: #666;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            
            .badge {{
                display: inline-block;
                background: linear-gradient(135deg, {primary}, {secondary});
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin-right: 12px;
            }}
            
            .figma-btn {{
                display: inline-block;
                background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
                color: white;
                padding: 12px 32px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 700;
                margin-top: 16px;
                transition: transform 0.3s ease;
            }}
            
            .figma-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }}
            
            .screens-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 24px;
                margin-top: 32px;
            }}
            
            .screen-card {{
                background: white;
                border: 2px solid #f0f0f0;
                border-radius: 16px;
                padding: 24px;
                transition: all 0.3s ease;
            }}
            
            .screen-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.1);
                border-color: {primary};
            }}
            
            .screen-icon {{
                font-size: 40px;
                margin-bottom: 12px;
            }}
            
            .screen-card h3 {{
                font-size: 20px;
                font-weight: 700;
                color: #333;
                margin-bottom: 8px;
            }}
            
            .screen-card p {{
                color: #666;
                font-size: 14px;
                line-height: 1.5;
            }}
            
            .prompt-section {{
                background: #1e1e1e;
                border-radius: 24px;
                padding: 0;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            }}
            
            .prompt-header {{
                background: #2d2d2d;
                padding: 20px 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #3e3e3e;
            }}
            
            .prompt-title {{
                color: #58a6ff;
                font-size: 24px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .copy-btn {{
                background: #238636;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-family: inherit;
                font-size: 14px;
                font-weight: 600;
                transition: background 0.2s;
            }}
            
            .copy-btn:hover {{
                background: #2ea043;
            }}
            
            .copy-btn:active {{
                transform: scale(0.95);
            }}
            
            .prompt-content {{
                padding: 32px;
                color: #c9d1d9;
                font-family: 'Fira Code', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.8;
                overflow-x: auto;
                max-height: 600px;
                overflow-y: auto;
            }}
            
            .prompt-content pre {{
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            
            .stats {{
                display: flex;
                gap: 16px;
                margin-top: 16px;
            }}
            
            .stat {{
                background: #f8f9fa;
                padding: 12px 20px;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 12px;
                margin-bottom: 4px;
            }}
            
            .stat-value {{
                color: {primary};
                font-size: 18px;
                font-weight: 700;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- UI Report Section -->
            <div class="section">
                <div class="project-title">🎨 {report_dict.get('project_name', 'UI Report')}</div>
                <div class="summary">{report_dict.get('summary', 'No summary available')[:400]}</div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Screens</div>
                        <div class="stat-value">{len(report_dict.get('screens', []))}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Domain</div>
                        <div class="stat-value">{domain.title()}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Colors</div>
                        <div class="stat-value">{len(colors)}</div>
                    </div>
                </div>
                
                {f'<a href="{figma_url}" class="figma-btn" target="_blank">🚀 Open in Figma</a>' if figma_url else ''}
                
                <div class="section-title" style="margin-top: 40px;">
                    <span>📊</span>
                    <span>Generated Screens</span>
                </div>
                <div class="screens-grid">
                    {screens_html}
                </div>
            </div>
            
            <!-- Prompt Used Section -->
            <div class="prompt-section">
                <div class="prompt-header">
                    <div class="prompt-title">
                        <span>💻</span>
                        <span>Prompt Used</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt()">📋 Copy Prompt</button>
                </div>
                <div class="prompt-content">
                    <pre id="prompt-text">{escaped_prompt}</pre>
                </div>
            </div>
        </div>
        
        <script>
            function copyPrompt() {{
                const text = document.getElementById('prompt-text').textContent;
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = document.querySelector('.copy-btn');
                    const originalText = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    btn.style.background = '#2ea043';
                    setTimeout(() => {{
                        btn.textContent = originalText;
                        btn.style.background = '#238636';
                    }}, 2000);
                }}).catch(err => {{
                    alert('Failed to copy: ' + err);
                }});
            }}
        </script>
    </body>
    </html>
    """)

# --------------------------------------------
# Upload endpoint for Figma plugin (JSON response)
# --------------------------------------------
@app.post("/upload", response_model=UIReportResponse)
async def upload_for_plugin(file: UploadFile = File(...)):
    file_bytes = await file.read()
    text = extract_text_from_bytes(file_bytes, file.content_type)
    
    if not text.strip():
        text = "Create a modern mobile application"

    import os
    project_name = os.path.splitext(file.filename)[0].replace('_', ' ').replace('-', ' ').title()
    domain = detect_domain_from_text(text)
    
    report, prompt_used = build_ui_report(project_name, text, domain)
    
    unique_project_name = create_unique_filename(project_name, domain)
    
    try:
        figma_url = figma_client.create_figma_file(unique_project_name)
    except Exception as e:
        print(f"Figma API error: {e}")
        figma_url = None
    
    global latest_report_data, latest_prompt_used
    latest_report_data = report.dict()
    latest_prompt_used = prompt_used
    
    return UIReportResponse(
        figma_url=figma_url,
        report=report,
        prompt_used=prompt_used
    )

@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon"}

# --------------------------------------------
# Sample report endpoint
# --------------------------------------------
@app.post("/sample-report")
def sample_report():
    """Generate report from sample document and auto-open Figma"""
    sample_path = os.getenv("SAMPLE_DOCUMENT_PATH", "./sample-data/ecommerce_uiux_report.pdf")
    
    try:
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
        
        text = extract_text_from_bytes(file_bytes, "application/pdf")
        project_name = extract_project_name(text) if text.strip() else "Sample-Project"
        domain = detect_domain_from_text(text)
        
        report, prompt_used = build_ui_report(project_name, text, domain)
        
        # Create unique filename for Figma
        unique_project_name = create_unique_filename(project_name, domain)
        
        # Create Figma file with error handling
        try:
            figma_url = figma_client.create_figma_file(unique_project_name)
        except Exception as e:
            print(f"Figma API error: {e}")
            figma_url = None
        
        return UIReportResponse(
            figma_url=figma_url,
            report=report,
            prompt_used=prompt_used
        )
    except Exception as e:
        return {"error": f"Could not process sample document: {e}"}

# Store latest report and prompt globally for auto-fetch
latest_report_data = None
latest_prompt_used = None

@app.get("/latest-report")
def get_latest_report():
    """Get the most recent report for auto-plugin fetching"""
    if latest_report_data:
        return {
            "status": "success",
            "report": latest_report_data
        }
    else:
        return {
            "status": "no_data",
            "message": "No recent reports available"
        }

@app.get("/latest-prompt")
def get_latest_prompt():
    """Get the most recent prompt used for generation"""
    if latest_prompt_used:
        return {
            "status": "success",
            "prompt": latest_prompt_used
        }
    else:
        return {
            "status": "no_data",
            "message": "No recent prompt available. Upload a PDF first."
        }

@app.options("/latest-report")
def options_latest_report():
    """Handle CORS preflight for latest-report endpoint"""
    from fastapi import Response
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

@app.get("/")
def root():
    return {"message": "Server is running"}