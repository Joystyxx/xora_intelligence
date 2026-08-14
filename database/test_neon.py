import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_DATABASE_URL is not configured.")


def main():
    conn = psycopg2.connect(DATABASE_URL)

    cursor = conn.cursor()

    cursor.execute("SELECT NOW();")

    result = cursor.fetchone()

    print("Neon connection successful.")
    print(f"Database time: {result[0]}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()