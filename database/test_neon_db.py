from neon_db import get_connection


def main():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM bounty_current;")
        current_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bounty_history;")
        history_count = cursor.fetchone()[0]

        print(f"Neon current rows: {current_count}")
        print(f"Neon history rows: {history_count}")

        cursor.close()

    finally:
        conn.close()


if __name__ == "__main__":
    main()