import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_STRING is not configured.")


def get_connection():
    return psycopg2.connect(DATABASE_URL)