import pandas as pd
from pathlib import Path


# =========================
# CONFIGURATION
# =========================

DATA_DIR = Path("data")

CURRENT_FILE = DATA_DIR / "bounty_current.csv"
HISTORY_FILE = DATA_DIR / "bounty_history.csv"


# =========================
# VALIDATION
# =========================

def main():

    print("=" * 60)
    print("XORA BOUNTY DATA VALIDATION")
    print("=" * 60)

    # -------------------------
    # LOAD FILES
    # -------------------------

    if not CURRENT_FILE.exists():
        print("\nERROR: bounty_current.csv not found.")
        raise SystemExit(1)

    if not HISTORY_FILE.exists():
        print("\nERROR: bounty_history.csv not found.")
        raise SystemExit(1)

    current = pd.read_csv(CURRENT_FILE)
    history = pd.read_csv(HISTORY_FILE)

    # -------------------------
    # CURRENT STATE INTEGRITY
    # -------------------------

    current_task_count = current["task_id"].nunique()

    current_duplicates = current["task_id"].duplicated().sum()

    print("\nDATASETS")
    print("-" * 60)
    print(f"Current state : {len(current)} rows")
    print(f"Full history  : {len(history)} rows")

    print("\nCURRENT STATE INTEGRITY")
    print("-" * 60)
    print(f"Current unique tasks : {current_task_count}")
    print(f"Current duplicate IDs: {current_duplicates}")

    # -------------------------
    # HISTORY INTEGRITY
    # -------------------------

    history["scraped_at"] = history["scraped_at"].astype(str)

    history_task_count = history["task_id"].nunique()

    history_duplicate_records = history.duplicated(
        subset=["task_id", "scraped_at"]
    ).sum()

    snapshot_times = sorted(
        history["scraped_at"].dropna().unique()
    )

    snapshot_count = len(snapshot_times)

    print("\nHISTORY")
    print("-" * 60)
    print(f"Unique tasks in history : {history_task_count}")
    print(f"Historical snapshots    : {snapshot_count}")
    print(f"Duplicate history rows  : {history_duplicate_records}")

    if snapshot_times:
        print(f"First snapshot          : {snapshot_times[0]}")
        print(f"Latest snapshot         : {snapshot_times[-1]}")

    # -------------------------
    # LATEST HISTORY CHANGE
    # -------------------------

    latest_change_count = 0
    latest_changed_tasks = 0
    latest_new_tasks = 0

    if snapshot_times:

        latest_time = snapshot_times[-1]

        latest_changes = history[
            history["scraped_at"] == latest_time
        ].copy()

        latest_change_count = len(latest_changes)

        # A task appearing in history for the first time is a new task.
        task_first_seen = (
            history.groupby("task_id")["scraped_at"]
            .min()
        )

        latest_new_tasks = sum(
            task_first_seen.loc[task_id] == latest_time
            for task_id in latest_changes["task_id"]
        )

        latest_new_tasks = int(latest_new_tasks)

        latest_changed_tasks = (
            latest_change_count - latest_new_tasks
        )

    print("\nLATEST UPDATE")
    print("-" * 60)
    print(f"History records added   : {latest_change_count}")
    print(f"New tasks added         : {latest_new_tasks}")
    print(f"Changed existing tasks  : {latest_changed_tasks}")

    # -------------------------
    # CURRENT BUSINESS STATUS
    # -------------------------

    open_tasks = (
        current["status"] == "open"
    ).sum()

    claimed_tasks = (
        current["status"] == "claimed"
    ).sum()

    paid_tasks = (
        current["status"] == "paid"
    ).sum()

    total_spots_left = current["spots_left"].sum()

    print("\nCURRENT METRICS")
    print("-" * 60)
    print(f"Open tasks             : {open_tasks}")
    print(f"Claimed tasks          : {claimed_tasks}")
    print(f"Paid tasks             : {paid_tasks}")
    print(f"Total spots left       : {total_spots_left}")

    # -------------------------
    # HISTORY GROWTH
    # -------------------------

    print("\nHISTORY GROWTH")
    print("-" * 60)
    print(f"Current state rows      : {len(current)}")
    print(f"Total history rows      : {len(history)}")
    print(f"Historical snapshots    : {snapshot_count}")

    # -------------------------
    # VALIDATION RULES
    # -------------------------

    valid = True

    # Current state must contain one row per task.
    if len(current) != current_task_count:
        valid = False

    # No duplicate current task IDs.
    if current_duplicates != 0:
        valid = False

    # No duplicate task + timestamp records in history.
    if history_duplicate_records != 0:
        valid = False

    # History must contain at least the tasks currently known.
    if history_task_count < current_task_count:
        valid = False

    # History cannot be empty.
    if history.empty:
        valid = False

    # -------------------------
    # RESULT
    # -------------------------

    print("\nRESULT")
    print("-" * 60)

    if valid:
        print("VALIDATION PASSED")
    else:
        print("VALIDATION FAILED")
        raise SystemExit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()