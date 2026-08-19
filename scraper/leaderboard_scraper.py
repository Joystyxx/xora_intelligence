import os
import pandas as pd
import psycopg2

from datetime import datetime, timezone
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_STRING is not configured.")


# ============================================================
# EXTRACT LEADERBOARD
# ============================================================

def flatten_leaderboard(data):
    """
    Extract the latest Top-12 leaderboard.

    Full contributor_code is retained for backend use.
    pseudo_code contains ONLY the final 4 characters and
    is the identifier exposed to Power BI.
    """

    leaderboard = data.get("leaderboard")

    if not isinstance(leaderboard, list):
        raise ValueError(
            "API response does not contain a valid 'leaderboard' list."
        )

    snapshot_at = datetime.now(timezone.utc)

    rows = []

    for rank, contributor in enumerate(leaderboard, start=1):

        contributor_code = contributor.get("code")

        if not contributor_code:
            continue

        contributor_code = str(contributor_code).strip()

        # EXACTLY the final four characters
        pseudo_code = contributor_code[-4:]

        rows.append({
            "contributor_code": contributor_code,
            "pseudo_code": pseudo_code,
            "name": contributor.get("name"),
            "role": contributor.get("role"),
            "rank": rank,
            "approved_xrp": contributor.get("approvedXrp"),
            "approved_xora": contributor.get("approvedXora"),
            "paid_xrp": contributor.get("paidXrp"),
            "paid_xora": contributor.get("paidXora"),
            "total_xrp": contributor.get("totalXrp"),
            "total_xora": contributor.get("totalXora"),
            "approved_count": contributor.get("approvedCount"),
            "completed": contributor.get("completed"),
            "snapshot_at": snapshot_at,
        })

    df = pd.DataFrame(rows)

    if len(df) != 12:
        print(
            f"Warning: API returned {len(df)} leaderboard contributors, "
            f"not 12."
        )

    return df


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# ============================================================
# BACKEND TABLE
# ============================================================

def save_leaderboard_backend(df):
    """
    Store the full contributor code for backend use.

    This table must NOT be connected to Power BI.
    """

    if df.empty:
        print("Leaderboard backend: nothing to save.")
        return

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        for _, row in df.iterrows():

            cursor.execute(
                """
                INSERT INTO leaderboard_backend (
                    contributor_code,
                    pseudo_code,
                    name,
                    role,
                    rank,
                    approved_xrp,
                    approved_xora,
                    paid_xrp,
                    paid_xora,
                    total_xrp,
                    total_xora,
                    approved_count,
                    completed,
                    snapshot_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (contributor_code)
                DO UPDATE SET
                    pseudo_code = EXCLUDED.pseudo_code,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    rank = EXCLUDED.rank,
                    approved_xrp = EXCLUDED.approved_xrp,
                    approved_xora = EXCLUDED.approved_xora,
                    paid_xrp = EXCLUDED.paid_xrp,
                    paid_xora = EXCLUDED.paid_xora,
                    total_xrp = EXCLUDED.total_xrp,
                    total_xora = EXCLUDED.total_xora,
                    approved_count = EXCLUDED.approved_count,
                    completed = EXCLUDED.completed,
                    snapshot_at = EXCLUDED.snapshot_at
                """,
                (
                    row["contributor_code"],
                    row["pseudo_code"],
                    row["name"],
                    row["role"],
                    row["rank"],
                    row["approved_xrp"],
                    row["approved_xora"],
                    row["paid_xrp"],
                    row["paid_xora"],
                    row["total_xrp"],
                    row["total_xora"],
                    row["approved_count"],
                    row["completed"],
                    row["snapshot_at"],
                )
            )

        conn.commit()

        print(
            f"Leaderboard backend updated: {len(df)} contributors."
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# CURRENT LEADERBOARD
# ============================================================

def save_leaderboard_current(df):
    """
    Replace leaderboard_current with the latest Top-12.

    This is the Power BI-facing current leaderboard.
    """

    if df.empty:
        print("Leaderboard current: nothing to save.")
        return

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Remove the previous Top-12 completely.
        cursor.execute(
            "DELETE FROM leaderboard_current"
        )

        for _, row in df.iterrows():

            cursor.execute(
                """
                INSERT INTO leaderboard_current (
                    pseudo_code,
                    name,
                    role,
                    rank,
                    approved_xrp,
                    approved_xora,
                    paid_xrp,
                    paid_xora,
                    total_xrp,
                    total_xora,
                    approved_count,
                    completed,
                    snapshot_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    row["pseudo_code"],
                    row["name"],
                    row["role"],
                    row["rank"],
                    row["approved_xrp"],
                    row["approved_xora"],
                    row["paid_xrp"],
                    row["paid_xora"],
                    row["total_xrp"],
                    row["total_xora"],
                    row["approved_count"],
                    row["completed"],
                    row["snapshot_at"],
                )
            )

        conn.commit()

        print(
            f"Leaderboard current replaced: {len(df)} contributors."
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# LEADERBOARD HISTORY
# ============================================================

def save_leaderboard_history(df):
    """
    Append the latest Top-12 snapshot to leaderboard_history.

    The history table stores the pseudocode, never the full
    contributor code.
    """

    if df.empty:
        print("Leaderboard history: nothing to save.")
        return

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        for _, row in df.iterrows():

            cursor.execute(
                """
                INSERT INTO leaderboard_history (
                    pseudo_code,
                    name,
                    role,
                    rank,
                    approved_xrp,
                    approved_xora,
                    paid_xrp,
                    paid_xora,
                    total_xrp,
                    total_xora,
                    approved_count,
                    completed,
                    snapshot_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    row["pseudo_code"],
                    row["name"],
                    row["role"],
                    row["rank"],
                    row["approved_xrp"],
                    row["approved_xora"],
                    row["paid_xrp"],
                    row["paid_xora"],
                    row["total_xrp"],
                    row["total_xora"],
                    row["approved_count"],
                    row["completed"],
                    row["snapshot_at"],
                )
            )

        conn.commit()

        print(
            f"Leaderboard history updated: "
            f"{len(df)} snapshot records."
        )

    finally:
        cursor.close()
        conn.close()