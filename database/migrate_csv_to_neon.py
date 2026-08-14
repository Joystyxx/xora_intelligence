import os
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_STRING is not configured.")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

CURRENT_FILE = DATA_DIR / "bounty_current.csv"
HISTORY_FILE = DATA_DIR / "bounty_history.csv"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return None

    return value


# ============================================================
# MIGRATE CURRENT
# ============================================================

def migrate_current(conn, df):

    cursor = conn.cursor()

    for _, row in df.iterrows():

        cursor.execute(
            """
            INSERT INTO bounty_current (
                task_id,
                title,
                category,
                brief,
                proof_required,
                reward_xrp,
                reward_xora,
                reward_label,
                status,
                task_status,
                max_claims,
                claimed_count,
                spots_left,
                submitted_count,
                approved_count,
                paid_count,
                difficulty,
                quality_bar,
                min_proof_chars,
                proof_link_required,
                x_post_required,
                min_account_age_hours,
                own_proof_link,
                own_proof_text,
                last_seen_at
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (task_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                brief = EXCLUDED.brief,
                proof_required = EXCLUDED.proof_required,
                reward_xrp = EXCLUDED.reward_xrp,
                reward_xora = EXCLUDED.reward_xora,
                reward_label = EXCLUDED.reward_label,
                status = EXCLUDED.status,
                task_status = EXCLUDED.task_status,
                max_claims = EXCLUDED.max_claims,
                claimed_count = EXCLUDED.claimed_count,
                spots_left = EXCLUDED.spots_left,
                submitted_count = EXCLUDED.submitted_count,
                approved_count = EXCLUDED.approved_count,
                paid_count = EXCLUDED.paid_count,
                difficulty = EXCLUDED.difficulty,
                quality_bar = EXCLUDED.quality_bar,
                min_proof_chars = EXCLUDED.min_proof_chars,
                proof_link_required = EXCLUDED.proof_link_required,
                x_post_required = EXCLUDED.x_post_required,
                min_account_age_hours = EXCLUDED.min_account_age_hours,
                own_proof_link = EXCLUDED.own_proof_link,
                own_proof_text = EXCLUDED.own_proof_text,
                last_seen_at = EXCLUDED.last_seen_at
            """,
            (
                clean_value(row.get("task_id")),
                clean_value(row.get("title")),
                clean_value(row.get("category")),
                clean_value(row.get("brief")),
                clean_value(row.get("proof_required")),
                clean_value(row.get("reward_xrp")),
                clean_value(row.get("reward_xora")),
                clean_value(row.get("reward_label")),
                clean_value(row.get("status")),
                clean_value(row.get("task_status")),
                clean_value(row.get("max_claims")),
                clean_value(row.get("claimed_count")),
                clean_value(row.get("spots_left")),
                clean_value(row.get("submitted_count")),
                clean_value(row.get("approved_count")),
                clean_value(row.get("paid_count")),
                clean_value(row.get("difficulty")),
                clean_value(row.get("quality_bar")),
                clean_value(row.get("min_proof_chars")),
                clean_value(row.get("proof_link_required")),
                clean_value(row.get("x_post_required")),
                clean_value(row.get("min_account_age_hours")),
                clean_value(row.get("own_proof_link")),
                clean_value(row.get("own_proof_text")),
                clean_value(row.get("scraped_at")),
            )
        )
    cursor.close()


# ============================================================
# MIGRATE HISTORY
# ============================================================

def migrate_history(conn, df):

    cursor = conn.cursor()

    for _, row in df.iterrows():

        change_type = row.get("change_type")

        if change_type == "new_task":
            db_change_type = "new_task"
        else:
            changed_fields = str(
                row.get("changed_fields", "")
            )

            if (
                "status" in changed_fields
                or "task_status" in changed_fields
            ):
                db_change_type = "status_change"
            else:
                db_change_type = "metric_change"

        cursor.execute(
            """
            INSERT INTO bounty_history (
                task_id,
                snapshot_at,
                change_type,
                title,
                category,
                brief,
                proof_required,
                reward_xrp,
                reward_xora,
                reward_label,
                status,
                task_status,
                max_claims,
                claimed_count,
                spots_left,
                submitted_count,
                approved_count,
                paid_count,
                difficulty,
                quality_bar,
                min_proof_chars,
                proof_link_required,
                x_post_required,
                min_account_age_hours,
                own_proof_link,
                own_proof_text
            )
            SELECT
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1
                FROM bounty_history
                WHERE task_id = %s
                  AND snapshot_at = %s
            )
            """,
            (
                clean_value(row.get("task_id")),
                clean_value(row.get("snapshot_at")),
                db_change_type,
                clean_value(row.get("title")),
                clean_value(row.get("category")),
                clean_value(row.get("brief")),
                clean_value(row.get("proof_required")),
                clean_value(row.get("reward_xrp")),
                clean_value(row.get("reward_xora")),
                clean_value(row.get("reward_label")),
                clean_value(row.get("status")),
                clean_value(row.get("task_status")),
                clean_value(row.get("max_claims")),
                clean_value(row.get("claimed_count")),
                clean_value(row.get("spots_left")),
                clean_value(row.get("submitted_count")),
                clean_value(row.get("approved_count")),
                clean_value(row.get("paid_count")),
                clean_value(row.get("difficulty")),
                clean_value(row.get("quality_bar")),
                clean_value(row.get("min_proof_chars")),
                clean_value(row.get("proof_link_required")),
                clean_value(row.get("x_post_required")),
                clean_value(row.get("min_account_age_hours")),
                clean_value(row.get("own_proof_link")),
                clean_value(row.get("own_proof_text")),

                # Duplicate check
                clean_value(row.get("task_id")),
                clean_value(row.get("snapshot_at")),
            )
        )

    cursor.close()

# ============================================================
# VALIDATE MIGRATION
# ============================================================

def validate(conn, current_df, history_df):

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM bounty_current"
    )

    neon_current_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bounty_history"
    )

    neon_history_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT task_id) FROM bounty_current"
    )

    neon_current_unique = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT task_id) FROM bounty_history"
    )

    neon_history_unique = cursor.fetchone()[0]

    cursor.close()

    print()
    print("=" * 60)
    print("NEON MIGRATION VALIDATION")
    print("=" * 60)

    print("\nCURRENT STATE")
    print("-" * 60)
    print(f"CSV rows             : {len(current_df)}")
    print(f"Neon rows            : {neon_current_count}")
    print(f"CSV unique tasks     : {current_df['task_id'].nunique()}")
    print(f"Neon unique tasks    : {neon_current_unique}")

    print("\nHISTORY")
    print("-" * 60)
    print(f"CSV rows             : {len(history_df)}")
    print(f"Neon rows            : {neon_history_count}")
    print(f"CSV unique tasks     : {history_df['task_id'].nunique()}")
    print(f"Neon unique tasks    : {neon_history_unique}")

    valid = (
        len(current_df) == neon_current_count
        and current_df["task_id"].nunique() == neon_current_unique
        and len(history_df) == neon_history_count
        and history_df["task_id"].nunique() == neon_history_unique
    )

    print("\nRESULT")
    print("-" * 60)

    if valid:
        print("MIGRATION VALIDATED")
    else:
        print("MIGRATION FAILED")

    print("=" * 60)

    return valid


# ============================================================
# MAIN
# ============================================================

def main():

    if not CURRENT_FILE.exists():
        raise FileNotFoundError(
            "bounty_current.csv not found."
        )

    if not HISTORY_FILE.exists():
        raise FileNotFoundError(
            "bounty_history.csv not found."
        )

    current_df = pd.read_csv(CURRENT_FILE)
    history_df = pd.read_csv(HISTORY_FILE)

    print("=" * 60)
    print("XORA CSV → NEON MIGRATION")
    print("=" * 60)

    print(
        f"Current CSV records : {len(current_df)}"
    )

    print(
        f"History CSV records : {len(history_df)}"
    )

    conn = get_connection()

    try:

        migrate_current(conn, current_df)
        migrate_history(conn, history_df)

        conn.commit()

        print("\nMigration completed.")

        validate(
            conn,
            current_df,
            history_df
        )

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()