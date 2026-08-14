import os
import requests
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from datetime import datetime, timezone

import sys
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import API_URL, CONTRIBUTOR_ID



# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CURRENT_FILE = DATA_DIR / "bounty_current.csv"
HISTORY_FILE = DATA_DIR / "bounty_history.csv"


DATABASE_URL = os.getenv("NEON_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_STRING is not configured.")

# ============================================================
# FIELDS
# ============================================================

# These fields describe the current state of each bounty.
CURRENT_FIELDS = [
    "task_id",
    "title",
    "category",
    "brief",
    "proof_required",
    "reward_xrp",
    "reward_xora",
    "reward_label",
    "status",
    "task_status",
    "max_claims",
    "claimed_count",
    "spots_left",
    "submitted_count",
    "approved_count",
    "paid_count",
    "difficulty",
    "quality_bar",
    "min_proof_chars",
    "proof_link_required",
    "x_post_required",
    "min_account_age_hours",
    "own_proof_link",
    "own_proof_text",
]


# These fields are important for detecting changes over time.
TRACKED_FIELDS = [
    "title",
    "category",
    "reward_xrp",
    "reward_xora",
    "reward_label",
    "status",
    "task_status",
    "max_claims",
    "claimed_count",
    "spots_left",
    "submitted_count",
    "approved_count",
    "paid_count",
    "difficulty",
    "min_proof_chars",
    "proof_link_required",
    "x_post_required",
    "min_account_age_hours",
]


# Numeric fields where we want to calculate changes.
NUMERIC_CHANGE_FIELDS = [
    "reward_xrp",
    "reward_xora",
    "max_claims",
    "claimed_count",
    "spots_left",
    "submitted_count",
    "approved_count",
    "paid_count",
]


# ============================================================
# FETCH API
# ============================================================

def fetch_bounties():
    print("Fetching XORA bounty data...")

    response = requests.get(
        API_URL,
        params={"id": CONTRIBUTOR_ID},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Unexpected API response format.")

    if not isinstance(data.get("tasks"), list):
        raise ValueError("API response does not contain a valid 'tasks' list.")

    print(f"API returned {len(data['tasks'])} tasks.")

    return data


# ============================================================
# FLATTEN TASKS
# ============================================================

def flatten_tasks(data):
    scraped_at = datetime.now(timezone.utc).isoformat()

    rows = []

    for task in data["tasks"]:

        reward = task.get("reward") or {}
        requirements = task.get("requirements") or {}
        own_claim = task.get("ownClaim") or {}

        row = {
            "scraped_at": scraped_at,

            "task_id": task.get("id"),
            "title": task.get("title"),
            "category": task.get("category"),

            "brief": task.get("brief"),
            "proof_required": task.get("proofRequired"),

            "reward_xrp": reward.get("xrp"),
            "reward_xora": reward.get("xora"),
            "reward_label": task.get("rewardLabel"),

            "status": task.get("status"),
            "task_status": task.get("taskStatus"),

            "max_claims": task.get("maxClaims"),
            "claimed_count": task.get("claimedCount"),
            "spots_left": task.get("spotsLeft"),
            "submitted_count": task.get("submittedCount"),
            "approved_count": task.get("approvedCount"),
            "paid_count": task.get("paidCount"),

            "difficulty": requirements.get("difficulty"),
            "quality_bar": requirements.get("qualityBar"),
            "min_proof_chars": requirements.get("minProofChars"),
            "proof_link_required": requirements.get("proofLinkRequired"),
            "x_post_required": requirements.get("xPostRequired"),
            "min_account_age_hours": requirements.get("minAccountAgeHours"),

            "own_proof_link": own_claim.get("proofLink"),
            "own_proof_text": own_claim.get("proofText"),
        }

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# NORMALIZE VALUES
# ============================================================

def normalize_value(value):
    """
    Makes comparisons reliable when comparing current API data
    against previously saved CSV data.
    """

    if pd.isna(value):
        return None

    if isinstance(value, str):
        return value.strip()

    return value


# ============================================================
# DETECT CHANGES
# ============================================================

def find_changes(old_row, new_row):
    """
    Returns the fields that changed between the previous
    snapshot and the new API response.
    """

    changes = {}

    for field in TRACKED_FIELDS:

        old_value = normalize_value(old_row.get(field))
        new_value = normalize_value(new_row.get(field))

        if old_value != new_value:

            change = {
                "old_value": old_value,
                "new_value": new_value
            }

            # Calculate numeric difference where appropriate.
            if field in NUMERIC_CHANGE_FIELDS:

                try:
                    if old_value is None:
                        difference = new_value
                    elif new_value is None:
                        difference = None
                    else:
                        difference = float(new_value) - float(old_value)

                    change["difference"] = difference

                except (ValueError, TypeError):
                    change["difference"] = None

            changes[field] = change

    return changes


# ============================================================
# LOAD CURRENT DATA
# ============================================================

def load_current():

    if not CURRENT_FILE.exists():
        return pd.DataFrame(columns=CURRENT_FIELDS + ["scraped_at"])

    df = pd.read_csv(CURRENT_FILE)

    if "task_id" not in df.columns:
        raise ValueError("Existing current dataset has no task_id column.")

    return df


# ============================================================
# UPDATE CURRENT + HISTORY
# ============================================================

def process_data(new_df, old_df):

    now = datetime.now(timezone.utc).isoformat()

    history_rows = []

    # --------------------------------------------------------
    # Build lookup of previous tasks
    # --------------------------------------------------------

    old_lookup = {}

    if not old_df.empty:

        for _, row in old_df.iterrows():
            task_id = row.get("task_id")

            if pd.notna(task_id):
                old_lookup[str(task_id)] = row.to_dict()

    # --------------------------------------------------------
    # Process every task returned by API
    # --------------------------------------------------------

    for _, new_row_series in new_df.iterrows():

        new_row = new_row_series.to_dict()

        task_id = new_row.get("task_id")

        if not task_id:
            continue

        task_id = str(task_id)

        # ----------------------------------------------------
        # NEW TASK
        # ----------------------------------------------------

        if task_id not in old_lookup:

            history_row = new_row.copy()

            history_row["snapshot_at"] = now
            history_row["change_type"] = "new_task"
            history_row["changed_fields"] = "NEW_TASK"

            for field in NUMERIC_CHANGE_FIELDS:
                value = new_row.get(field)

                try:
                    history_row[f"{field}_change"] = (
                        float(value) if value is not None else None
                    )
                except (ValueError, TypeError):
                    history_row[f"{field}_change"] = None

            history_rows.append(history_row)

            continue

        # ----------------------------------------------------
        # EXISTING TASK
        # ----------------------------------------------------

        old_row = old_lookup[task_id]

        changes = find_changes(old_row, new_row)

        # Nothing changed -> DO NOT add history row.
        if not changes:
            continue

        # ----------------------------------------------------
        # CHANGED TASK
        # ----------------------------------------------------

        history_row = new_row.copy()

        history_row["snapshot_at"] = now
        history_row["change_type"] = "update"

        history_row["changed_fields"] = ",".join(changes.keys())

        # Add metric differences.
        for field in NUMERIC_CHANGE_FIELDS:

            if field in changes:
                history_row[f"{field}_change"] = changes[field]["difference"]
            else:
                history_row[f"{field}_change"] = 0

        # Add previous values for important tracked metrics.
        for field in TRACKED_FIELDS:

            if field in changes:
                history_row[f"{field}_previous"] = changes[field]["old_value"]

        history_rows.append(history_row)

    return history_rows


# ============================================================
# SAVE CURRENT STATE
# ============================================================

def save_current(new_df):

    # Keep only one row per task.
    new_df = new_df.drop_duplicates(
        subset=["task_id"],
        keep="last"
    )

    new_df.to_csv(
        CURRENT_FILE,
        index=False
    )

    print(
        f"Current state saved: "
        f"{len(new_df)} unique bounty tasks."
    )


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(history_rows):

    if not history_rows:

        print("No bounty changes detected.")
        return

    new_history = pd.DataFrame(history_rows)

    if HISTORY_FILE.exists():

        old_history = pd.read_csv(HISTORY_FILE)

        history = pd.concat(
            [old_history, new_history],
            ignore_index=True
        )

    else:

        history = new_history

    history.to_csv(
        HISTORY_FILE,
        index=False
    )

    print(
        f"History updated: "
        f"{len(new_history)} new change records."
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(new_df, old_df, history_rows):

    old_ids = set()

    if not old_df.empty:
        old_ids = set(
            old_df["task_id"]
            .dropna()
            .astype(str)
        )

    new_ids = set(
        new_df["task_id"]
        .dropna()
        .astype(str)
    )

    new_tasks = new_ids - old_ids

    print()
    print("=" * 60)
    print("XORA BOUNTY SCRAPER SUMMARY")
    print("=" * 60)

    print(f"Current API tasks:     {len(new_df)}")
    print(f"Previous tasks:        {len(old_ids)}")
    print(f"New tasks detected:    {len(new_tasks)}")
    print(f"Changed tasks:         {len(history_rows) - len(new_tasks)}")
    print(f"History records added: {len(history_rows)}")

    print()
    print(f"Current file:  {CURRENT_FILE}")
    print(f"History file:  {HISTORY_FILE}")

    print("=" * 60)



# ============================================================
# NEON DATABASE
# ============================================================

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def save_current_to_neon(new_df):
    """
    Replace the Neon current-state table with the latest
    state returned by the API.
    """

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Upsert every current bounty.
        for _, row in new_df.iterrows():

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
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
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
                    datetime.now(timezone.utc)
                )
            )

        conn.commit()

        print(
            f"Neon current state updated: "
            f"{len(new_df)} tasks."
        )

    finally:
        cursor.close()
        conn.close()


def save_history_to_neon(history_rows):
    """
    Insert only newly detected bounty changes into Neon history.
    """

    if not history_rows:
        print("Neon history: no new change records.")
        return

    conn = get_db_connection()

    inserted = 0

    try:
        cursor = conn.cursor()

        for row in history_rows:

            change_type = row.get("change_type")

            # Match the database constraint.
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

            snapshot_at = row.get("snapshot_at")

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
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (task_id, snapshot_at)
                DO NOTHING
                """,
                (
                    row.get("task_id"),
                    snapshot_at,
                    db_change_type,
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
                    row.get("own_proof_text")
                )
            )

            inserted += cursor.rowcount

        conn.commit()

        print(
            f"Neon history updated: "
            f"{inserted} new change records."
        )

    finally:
        cursor.close()
        conn.close()

        
# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # 1. Fetch API
        data = fetch_bounties()

        # 2. Convert API tasks into dataframe
        new_df = flatten_tasks(data)

        if new_df.empty:
            print("No bounty tasks returned by API.")
            return

        # 3. Load previous current state
        old_df = load_current()

        # 4. Detect new tasks and metric/state changes
        history_rows = process_data(
            new_df,
            old_df
        )

        # 5. Replace current CSV with latest state
        save_current(new_df)
        
        # 6. Append ONLY meaningful changes to CSV history
        save_history(history_rows)
        
        # 7. Write latest state to Neon
        save_current_to_neon(new_df)
        
        # 8. Write ONLY meaningful changes to Neon history
        save_history_to_neon(history_rows)
        
        # 9. Print result
        print_summary(
            new_df,
            old_df,
            history_rows
        )
        
        print()
        print("Scraping completed successfully.")

    except requests.RequestException as error:

        print(f"API request failed: {error}")

    except Exception as error:

        print(f"Scraper failed: {error}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()