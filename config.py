import os
from dotenv import load_dotenv

load_dotenv()

# --- DO NOT MODIFY THE BELOW SECTION ---

# =================================================================
# 1. CORE SYSTEM CONFIGURATION (Do Not Modify)
# =================================================================
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_TABLE_NAME: str = "jobs"
SUPABASE_CUSTOMIZED_RESUMES_TABLE_NAME = "customized_resumes"
SUPABASE_STORAGE_BUCKET="personalized_resumes"
SUPABASE_RESUME_STORAGE_BUCKET="resumes"
SUPABASE_BASE_RESUME_TABLE_NAME = "base_resume"
BASE_RESUME_PATH = "resume.json"

# API keys — set only the key(s) needed for your chosen provider.
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_FIRST_API_KEY")

# =================================================================
# 2. USER PREFERENCES (Editable)
# =================================================================

# --- LLM Settings ---
# Use any model supported by LiteLLM (gemini, openai/gpt-4o-mini, groq/llama-3.3-70b-versatile)
# Full list of supported models & naming: https://docs.litellm.ai/docs/providers
LLM_MODEL = "openai/gpt-oss-20b"
LLM_API_BASE = os.environ.get("LLM_API_BASE") or "http://localhost:1234/v1"

# --- Search Configuration ---
LINKEDIN_SEARCH_QUERIES = ["Softwareentwickler", "Data Scientist", "Python Developer", "Machine Learning Engineer", "Robotics Software Engineer", "Software Architect", "Computer Vision Engineer", "Oracle APEX Developer", "Low Code"]
LINKEDIN_LOCATION = "Germany"
LINKEDIN_GEO_ID = 101282230      # Germany: 101282230
LINKEDIN_JOB_TYPE = "F" # F=Full-time, C=Contract, P=Part-time, T=Temporary, I=Internship
LINKEDIN_JOB_POSTING_DATE = "r604800" # r86400=Past 24h, r604800=Past week
LINKEDIN_F_WT = 2 # 1=Onsite, 2=Remote, 3=Hybrid

CAREERS_FUTURE_SEARCH_QUERIES = ["Python Developer", "Machine Learning Engineer", "Data Scientist", "Software Architect"]
CAREERS_FUTURE_SEARCH_CATEGORIES = ["Information Technology"]
CAREERS_FUTURE_SEARCH_EMPLOYMENT_TYPES = ["Full Time"]

# --- New Portals Configuration ---
ARBEITSAGENTUR_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Softwareentwickler Python", "Machine Learning Ingenieur", "Robotics Engineer", "Oracle APEX Entwickler", "Low Code"]
INDEED_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Python Developer", "Machine Learning Engineer", "Robotics Engineer", "Software Architect", "Computer Vision", "Low Code"]
STEPSTONE_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Python Softwareentwickler", "Data Scientist", "Machine Learning", "Oracle APEX", "Low Code"]
MEINESTADT_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Python", "IT Projektleiter", "Low Code"]
JOOBLE_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Python Developer", "Robotics", "Machine Learning", "Autonomous Systems", "Low Code"]

WORKWISE_SEARCH_QUERIES = ["KI", "C#", "Softwareentwickler", "Python", "Data", "IT", "Low Code"]

# Generic Location setting
GERMANY_LOCATION = "Heidelberg"
SEARCH_RADIUS_KM = 10  # Radius in km around GERMANY_LOCATION

# --- Output Settings ---
OUTPUT_LANGUAGE = "german"      # "german" or "english" — affects resume & Anschreiben text
GENERATE_ANSCHREIBEN = True     # Whether to generate a cover letter alongside the resume

# Full sender address for the Anschreiben header (street, city, postal code)
SENDER_ADDRESS = os.environ.get("SENDER_ADDRESS") or "Musterstraße 1, 69117 Heidelberg"

# --- Processing Limits ---
SCRAPING_SOURCES = ["arbeitsagentur", "indeed", "stepstone", "meinestadt", "jooble", "workwise"] # Also available: "linkedin", "careers_future"
JOBS_TO_SCORE_PER_RUN = 200
JOBS_TO_CUSTOMIZE_PER_RUN = 10
MAX_JOBS_PER_SEARCH = {
    "linkedin": 2,
    "careers_future": 10,
    "arbeitsagentur": 20,
    "indeed": 20,
    "stepstone": 20,
    "meinestadt": 20,
    "jooble": 20,
    "workwise": 20,
}

# =================================================================
# 3. ADVANCED SYSTEM SETTINGS (Modify with Caution)
# =================================================================
LLM_MAX_RPM = 10
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 10
LLM_DAILY_REQUEST_BUDGET = 0
LLM_REQUEST_DELAY_SECONDS = 8

LINKEDIN_MAX_START = 1 
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 15

JOB_EXPIRY_DAYS = 30
JOB_CHECK_DAYS = 3
JOB_DELETION_DAYS = 60
JOB_CHECK_LIMIT = 50
ACTIVE_CHECK_TIMEOUT = 20
ACTIVE_CHECK_MAX_RETRIES = 2
ACTIVE_CHECK_RETRY_DELAY = 10