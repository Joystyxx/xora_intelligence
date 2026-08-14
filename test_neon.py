import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("XORA_API_URL")
CONTRIBUTOR_ID = os.getenv("XORA_CONTRIBUTOR_ID")

if not API_URL:
    raise ValueError("XORA_API_URL is not configured.")

if not CONTRIBUTOR_ID:
    raise ValueError("XORA_CONTRIBUTOR_ID is not configured.")