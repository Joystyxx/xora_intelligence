from bounty_db import (
    get_current_bounties,
    get_history,
    get_task_history,
    upsert_current_bounties,
    insert_history_records,
)


def main():

    print("=" * 60)
    print("XORA DATABASE WRITE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. READ BASELINE
    # --------------------------------------------------------

    current_before = get_current_bounties()
    history_before = get_history()

    print("\nBASELINE")
    print("-" * 60)
    print(f"Current rows : {len(current_before)}")
    print(f"History rows : {len(history_before)}")

    # --------------------------------------------------------
    # 2. TEST CURRENT UPSERT
    # --------------------------------------------------------

    test_task = current_before[0].copy()

    print("\nCURRENT UPSERT TEST")
    print("-" * 60)
    print(f"Testing task : {test_task['task_id']}")

    upsert_current_bounties([test_task])

    current_after = get_current_bounties()

    print(f"Current rows after upsert : {len(current_after)}")

    task_ids = [
        row["task_id"]
        for row in current_after
    ]

    duplicate_count = (
        len(task_ids) - len(set(task_ids))
    )

    print(f"Duplicate task IDs        : {duplicate_count}")

    # --------------------------------------------------------
    # 3. TEST HISTORY INSERT
    # --------------------------------------------------------

    print("\nHISTORY INSERT TEST")
    print("-" * 60)

    history_before_count = len(history_before)

    test_history = test_task.copy()

    # Remove current-table-only field
    test_history.pop("last_seen_at", None)

    # Use a known-valid change type
    test_history["snapshot_at"] = (
        "2026-01-01T00:00:00+00:00"
    )

    test_history["change_type"] = "metric_change"

    insert_history_records([test_history])

    history_after = get_history()

    print(f"History rows before : {history_before_count}")
    print(f"History rows after  : {len(history_after)}")

    # --------------------------------------------------------
    # 4. VERIFY HISTORY RECORD
    # --------------------------------------------------------

    inserted_history = get_task_history(
        test_task["task_id"]
    )

    test_records = [
        row
        for row in inserted_history
        if (
            row["change_type"] == "metric_change"
            and str(row["snapshot_at"])
            == "2026-01-01 00:00:00+00:00"
        )
    ]

    print(
        f"Test history records found : "
        f"{len(test_records)}"
    )

    # --------------------------------------------------------
    # 5. FINAL VALIDATION
    # --------------------------------------------------------

    print("\nVALIDATION")
    print("-" * 60)

    valid = (
        len(current_after) == len(current_before)
        and duplicate_count == 0
        and len(history_after)
        == history_before_count + 1
        and len(test_records) >= 1
    )

    if valid:
        print("DATABASE WRITE TEST PASSED")
    else:
        print("DATABASE WRITE TEST FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()