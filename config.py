import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load .env from current directory
load_dotenv()



class Config:
    # Airtable
    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Google Gemini (Fallback)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower() # 'openai', 'gemini', or 'openrouter'
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # AWS Lambda Endpoints (from n8n json)
    IMAGE_METADATA_API = os.getenv("IMAGE_METADATA_API")
    VIDEO_METADATA_API = os.getenv("VIDEO_METADATA_API")
    
    # Cloudinary (from n8n json)
    CLOUDINARY_API_URL = os.getenv("CLOUDINARY_API_URL")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET")

    # Make Webhooks (Add your 10 webhooks here)
    MAKE_API_KEY = os.getenv("MAKE_API_KEY")
    MAKE_WEBHOOKS = {
        "Profile1": os.getenv("MAKE_WEBHOOK_1", "URL_HERE"),
        "Profile2": os.getenv("MAKE_WEBHOOK_2", "URL_HERE"),
        "Profile3": os.getenv("MAKE_WEBHOOK_3", "URL_HERE"),
        "Profile4": os.getenv("MAKE_WEBHOOK_4", "URL_HERE"),
        "Profile5": os.getenv("MAKE_WEBHOOK_5", "URL_HERE"),
        "Profile6": os.getenv("MAKE_WEBHOOK_6", "URL_HERE"),
        "Profile7": os.getenv("MAKE_WEBHOOK_7", "URL_HERE"),
        "Profile8": os.getenv("MAKE_WEBHOOK_8", "URL_HERE"),
        "Profile9": os.getenv("MAKE_WEBHOOK_9", "URL_HERE"),
        "Profile10": os.getenv("MAKE_WEBHOOK_10", "URL_HERE"),
    }

    # Posting Times (24h format e.g., "09:00")
    POSTING_TIMES = {
        "Profile1": os.getenv("TIME_1", "09:00"),
        "Profile2": os.getenv("TIME_2", "10:00"),
        "Profile3": os.getenv("TIME_3", "11:00"),
        "Profile4": os.getenv("TIME_4", "12:00"),
        "Profile5": os.getenv("TIME_5", "13:00"),
        "Profile6": os.getenv("TIME_6", "14:00"),
        "Profile7": os.getenv("TIME_7", "15:00"),
        "Profile8": os.getenv("TIME_8", "16:00"),
        "Profile9": os.getenv("TIME_9", "17:00"),
        "Profile10": os.getenv("TIME_10", "18:00"),
    }

    # Scheduling
    SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "60"))
