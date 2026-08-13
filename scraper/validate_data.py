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
        return

    if not HISTORY_FILE.exists():
        print("\nERROR: bounty_history.csv not found.")
        return

    current = pd.read_csv(CURRENT_FILE)
    history = pd.read_csv(HISTORY_FILE)

    # -------------------------
    # BASIC COUNTS
    # -------------------------

    current_task_count = current["task_id"].nunique()
    history_task_count = history["task_id"].nunique()

    print("\nDATASETS")
    print("-" * 60)
    print(f"Current state : {len(current)} rows")
    print(f"Full history  : {len(history)} rows")

    # -------------------------
    # CURRENT DUPLICATES
    # -------------------------

    current_duplicates = current["task_id"].duplicated().sum()

    print("\nCURRENT STATE INTEGRITY")
    print("-" * 60)
    print(f"Current unique tasks : {current_task_count}")
    print(f"Current duplicate IDs: {current_duplicates}")

    # -------------------------
    # HISTORY SNAPSHOT CHECK
    # -------------------------

    history["scraped_at"] = history["scraped_at"].astype(str)

    history_duplicate_snapshots = history.duplicated(
        subset=["task_id", "scraped_at"]
    ).sum()

    snapshot_times = sorted(
        history["scraped_at"].unique()
    )

    snapshot_count = len(snapshot_times)

    print("\nHISTORY")
    print("-" * 60)
    print(f"Unique tasks in history : {history_task_count}")
    print(f"Historical snapshots    : {snapshot_count}")
    print(f"Duplicate snapshots     : {history_duplicate_snapshots}")

    if snapshot_times:
        print(f"First snapshot          : {snapshot_times[0]}")
        print(f"Latest snapshot         : {snapshot_times[-1]}")

    # -------------------------
    # COMPARE CURRENT STATE
    # -------------------------

    new_tasks = 0
    changed_tasks = 0
    unchanged_tasks = 0

    history_records_added = 0

    if len(snapshot_times) >= 2:

        previous_time = snapshot_times[-2]
        latest_time = snapshot_times[-1]

        previous_snapshot = history[
            history["scraped_at"] == previous_time
        ].copy()

        latest_snapshot = history[
            history["scraped_at"] == latest_time
        ].copy()

        # Tasks represented in each historical snapshot
        previous_ids = set(previous_snapshot["task_id"])
        latest_ids = set(latest_snapshot["task_id"])

        # New tasks
        new_tasks = len(latest_ids - previous_ids)

        # Changed tasks are represented by the latest history batch.
        changed_tasks = len(latest_ids - (latest_ids - previous_ids))

        # However, a latest snapshot may contain both:
        # new tasks and changed existing tasks.
        existing_changed_tasks = latest_ids & previous_ids

        changed_tasks = len(existing_changed_tasks)

        unchanged_tasks = current_task_count - new_tasks - changed_tasks

        history_records_added = len(latest_snapshot)

        print("\nLATEST UPDATE")
        print("-" * 60)
        print(f"Current tasks           : {current_task_count}")
        print(f"Previous current tasks  : {len(previous_ids)}")
        print(f"New tasks added         : {new_tasks}")
        print(f"Changed existing tasks  : {changed_tasks}")
        print(f"Unchanged tasks         : {unchanged_tasks}")
        print(f"History records added   : {history_records_added}")

    else:

        print("\nLATEST UPDATE")
        print("-" * 60)
        print("Initial snapshot only.")
        print(f"Current tasks           : {current_task_count}")
        print("New tasks added         : 0")
        print("Changed existing tasks  : 0")
        print(f"History records         : {len(history)}")

    # -------------------------
    # CURRENT BUSINESS STATUS
    # -------------------------

    print("\nCURRENT METRICS")
    print("-" * 60)

    print(
        f"Open tasks             : "
        f"{(current['status'] == 'open').sum()}"
    )

    print(
        f"Claimed tasks          : "
        f"{(current['status'] == 'claimed').sum()}"
    )

    print(
        f"Paid tasks             : "
        f"{(current['status'] == 'paid').sum()}"
    )

    print(
        f"Total spots left       : "
        f"{current['spots_left'].sum()}"
    )

    # -------------------------
    # HISTORY GROWTH
    # -------------------------

    print("\nHISTORY GROWTH")
    print("-" * 60)
    print(f"Current state rows      : {len(current)}")
    print(f"Total history rows      : {len(history)}")
    print(f"Historical snapshots    : {snapshot_count}")

    # -------------------------
    # FINAL VALIDATION
    # -------------------------

    valid = (
        len(current) == current_task_count
        and current_duplicates == 0
        and history_duplicate_snapshots == 0
        and history_task_count >= current_task_count
    )

    print("\nRESULT")
    print("-" * 60)

    if valid:
        print("VALIDATION PASSED")
    else:
        print("VALIDATION FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()