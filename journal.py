# ============================================================================
# JOURNAL - Daily notes and correlations with metrics
# ============================================================================
# Log how you feel and find patterns
# ============================================================================

import json
import os
from datetime import datetime

def load_journal():
    """
    Load journal entries from file.

    Returns:
        Dictionary with dates as keys
    """
    journal_file = "data/journal.json"

    if os.path.exists(journal_file):
        with open(journal_file, "r") as f:
            return json.load(f)
    return {}


def save_journal(journal):
    """
    Save journal entries to file.

    Args:
        journal: Dictionary with journal data
    """
    os.makedirs("data", exist_ok=True)
    with open("data/journal.json", "w") as f:
        json.dump(journal, f, indent=2)


def add_entry(text, tags=None, date=None):
    """
    Add a journal entry for a specific date.

    Args:
        text: Journal entry text
        tags: List of tags (e.g., ["tired", "stressed"])
        date: Date string "YYYY-MM-DD" (defaults to today)

    Returns:
        Success status
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    journal = load_journal()

    if date not in journal:
        journal[date] = {"entries": []}

    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "text": text,
        "tags": tags or []
    }

    journal[date]["entries"].append(entry)

    save_journal(journal)

    return True


def get_entries(date=None):
    """
    Get journal entries for a specific date.

    Args:
        date: Date string "YYYY-MM-DD" (defaults to today)

    Returns:
        List of journal entries
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    journal = load_journal()

    if date in journal:
        return journal[date]["entries"]

    return []


def get_all_entries():
    """
    Get all journal entries across all dates.

    Returns:
        Dictionary with dates and entries
    """
    return load_journal()


def find_correlations(history_df):
    """
    Find correlations between journal tags and metrics.

    For example: "tired" tag might correlate with low recovery

    Args:
        history_df: DataFrame with date, recovery, strain, etc.

    Returns:
        Dictionary with correlation insights
    """
    journal = load_journal()

    if not journal:
        return {
            "message": "No journal entries yet - start logging to find patterns!",
            "correlations": []
        }

    # Count tag frequencies
    tag_metrics = {}

    for date, data in journal.items():
        for entry in data.get("entries", []):
            for tag in entry.get("tags", []):
                if tag not in tag_metrics:
                    tag_metrics[tag] = {
                        "count": 0,
                        "recoveries": [],
                        "strains": []
                    }

                tag_metrics[tag]["count"] += 1

                # Find corresponding metrics for this date
                matching_day = history_df[history_df["date"].astype(str) == date]

                if not matching_day.empty:
                    tag_metrics[tag]["recoveries"].append(
                        matching_day.iloc[0]["recovery"]
                    )
                    tag_metrics[tag]["strains"].append(
                        matching_day.iloc[0]["strain"]
                    )

    # Calculate averages
    correlations = []
    for tag, data in tag_metrics.items():
        if data["recoveries"]:
            avg_recovery = sum(data["recoveries"]) / len(data["recoveries"])
            avg_strain = sum(data["strains"]) / len(data["strains"])

            correlations.append({
                "tag": tag,
                "count": data["count"],
                "avg_recovery": round(avg_recovery, 1),
                "avg_strain": round(avg_strain, 1)
            })

    # Sort by frequency
    correlations.sort(key=lambda x: x["count"], reverse=True)

    return {
        "message": f"Found {len(correlations)} tags across {len(journal)} days",
        "correlations": correlations
    }


# Predefined tags for quick selection
COMMON_TAGS = [
    "tired",
    "energized",
    "stressed",
    "relaxed",
    "sore",
    "great energy",
    "poor sleep",
    "good sleep",
    "sick",
    "recovered",
    "motivated",
    "unmotivated"
]
