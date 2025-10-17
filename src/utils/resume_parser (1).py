# src/utils/resume_parser.py
import spacy
from spacy.pipeline import EntityRuler
import json
import os
import re
import logging
from collections import defaultdict

# --- Setup a dedicated logger for this module ---
logger = logging.getLogger(__name__)

# --- CRITICAL OPTIMIZATION: Load the model only ONCE when the app starts ---
NLP_MODEL = None
try:
    NLP_MODEL = spacy.load("en_core_web_sm")
    logger.info("✅ spaCy NLP model ('en_core_web_sm') loaded successfully.")
except OSError:
    logger.warning("⚠️ spaCy model 'en_core_web_sm' not found. The app will run with limited resume parsing capabilities.")
    # Create a dummy model to prevent crashes
    try:
        NLP_MODEL = spacy.blank("en")
        logger.info("✅ Created blank English model as fallback.")
    except Exception as e:
        logger.error(f"❌ Could not create fallback model: {e}")
        NLP_MODEL = None

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_TAXONOMY_PATH = os.path.join(_CURRENT_DIR, "skill_taxonomy.json")

def load_skill_patterns(job_category: str) -> list:
    """Loads skill patterns from the JSON taxonomy for a specific job category."""
    try:
        with open(_TAXONOMY_PATH, 'r') as f:
            taxonomy = json.load(f)
    except FileNotFoundError:
        logger.error(f"Skill taxonomy file not found at {_TAXONOMY_PATH}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from skill taxonomy file at {_TAXONOMY_PATH}")
        return []

    # Get skills for the category, default to an empty list
    skills_for_category = taxonomy.get(job_category, [])
    
    # Create spaCy pattern dictionaries
    patterns = [{"label": "SKILL", "pattern": skill} for skill in skills_for_category]
    return patterns

def redact_pii(text: str) -> str:
    """Finds and redacts common PII patterns like emails and phone numbers."""
    # Regex for most common email formats
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Regex for common phone number formats (more comprehensive)
    phone_regex = r'(\+?\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}'
    
    text = re.sub(email_regex, '[REDACTED_EMAIL]', text)
    text = re.sub(phone_regex, '[REDACTED_PHONE]', text)
    return text

def parse_resume_text(text: str, job_category: str) -> str:
    """
    Parses raw resume text using spaCy NER after redacting PII.
    It efficiently adds and removes a custom entity ruler for skill detection.
    """
    if NLP_MODEL is None:
        logger.warning("NLP model is not available. Returning basic resume analysis.")
        # Return a basic structure without NLP parsing
        basic_analysis = {
            "SKILLS": ["NLP model not available"],
            "ORG": ["Enable spaCy for full analysis"],
            "LOCATIONS": ["Install en_core_web_sm"],
            "NOTE": "spaCy model not installed. Please install en_core_web_sm for full resume parsing."
        }
        return json.dumps(basic_analysis, indent=2)

    # 1. Redact PII as the very first step
    clean_text = redact_pii(text)
    
    # 2. Dynamically add and manage the EntityRuler pipeline component
    skill_patterns = load_skill_patterns(job_category)
    ruler_name = "skill_ruler"
    
    if ruler_name in NLP_MODEL.pipe_names:
        # If the ruler exists from a previous run, remove it to start fresh
        NLP_MODEL.remove_pipe(ruler_name)
        
    ruler = NLP_MODEL.add_pipe("entity_ruler", name=ruler_name, before="ner")
    ruler.add_patterns(skill_patterns)

    # 3. Process the text with the configured pipeline
    doc = NLP_MODEL(clean_text)
    
    # 4. Cleanly extract entities using defaultdict
    entities = defaultdict(set)
    for ent in doc.ents:
        # Map spaCy's GPE label to a more intuitive "LOCATIONS" key
        label = "LOCATIONS" if ent.label_ == "GPE" else ent.label_
        if label in ["SKILL", "ORG", "DATE", "LOCATIONS"]:
            entities[label].add(ent.text.strip())
            
    # Convert sets to sorted lists for consistent JSON output
    output_entities = {label: sorted(list(values)) for label, values in entities.items()}

    # 5. Remove the custom ruler after processing to keep the model clean
    NLP_MODEL.remove_pipe(ruler_name)
    
    return json.dumps(output_entities, indent=2)