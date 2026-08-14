import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_STRING is not configured.")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_current_bounties():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM bounty_current
            ORDER BY task_id;
        """)

        columns = [description[0] for description in cursor.description]

        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:
        conn.close()


def get_history():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM bounty_history
            ORDER BY snapshot_at, history_id;
        """)

        columns = [description[0] for description in cursor.description]

        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:
        conn.close()


def get_task_history(task_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM bounty_history
            WHERE task_id = %s
            ORDER BY snapshot_at, history_id;
        """, (task_id,))

        columns = [description[0] for description in cursor.description]

        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:
        conn.close()


def upsert_current_bounties(rows):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        for row in rows:
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
                    row.get("task_id"),
                    row.get("title"),
                    row.get("category"),
                    row.get("brief"),
                    row.get("proof_required"),
                    row.get("reward_xrp"),
                    row.get("reward_xora"),
                    row.get("reward_label"),
                    row.get("status"),
                    row.get("task_status"),
                    row.get("max_claims"),
                    row.get("claimed_count"),
                    row.get("spots_left"),
                    row.get("submitted_count"),
                    row.get("approved_count"),
                    row.get("paid_count"),
                    row.get("difficulty"),
                    row.get("quality_bar"),
                    row.get("min_proof_chars"),
                    row.get("proof_link_required"),
                    row.get("x_post_required"),
                    row.get("min_account_age_hours"),
                    row.get("own_proof_link"),
                    row.get("own_proof_text"),
                    row.get("last_seen_at") or row.get("scraped_at"),
                )
            )

        conn.commit()

    finally:
        conn.close()


def insert_history_records(rows):
    if not rows:
        return

    conn = get_connection()

    try:
        cursor = conn.cursor()

        for row in rows:
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
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s
                )
                """,
                (
                    row.get("task_id"),
                    row.get("snapshot_at"),
                    row.get("change_type"),
                    row.get("title"),
                    row.get("category"),
                    row.get("brief"),
                    row.get("proof_required"),
                    row.get("reward_xrp"),
                    row.get("reward_xora"),
                    row.get("reward_label"),
                    row.get("status"),
                    row.get("task_status"),
                    row.get("max_claims"),
                    row.get("claimed_count"),
                    row.get("spots_left"),
                    row.get("submitted_count"),
                    row.get("approved_count"),
                    row.get("paid_count"),
                    row.get("difficulty"),
                    row.get("quality_bar"),
                    row.get("min_proof_chars"),
                    row.get("proof_link_required"),
                    row.get("x_post_required"),
                    row.get("min_account_age_hours"),
                    row.get("own_proof_link"),
                    row.get("own_proof_text"),
                )
            )

        conn.commit()

    finally:
        conn.close()        