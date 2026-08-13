import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("XORA_API_URL")
CONTRIBUTOR_ID = os.getenv("XORA_CONTRIBUTOR_ID")