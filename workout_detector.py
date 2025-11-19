# ============================================================================
# WORKOUT AUTO-DETECTION - Automatically detect and log workouts
# ============================================================================
# Detects when HR is elevated for 10+ minutes
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def detect_workouts(df, rhr):
    """
    Automatically detect workout sessions from heart rate data.

    Criteria:
    - Heart rate elevated > 20 BPM above resting for 10+ consecutive minutes
    - Minimum workout duration: 10 minutes

    Args:
        df: DataFrame with columns [timestamp, bpm]
        rhr: Resting heart rate

    Returns:
        List of detected workout dictionaries
    """
    workouts = []

    # Calculate elevated HR threshold (resting + 20 BPM)
    threshold = rhr + 20

    # Mark elevated periods
    df = df.copy()
    df["elevated"] = df["bpm"] > threshold

    # Find continuous elevated periods
    df["block"] = (df["elevated"] != df["elevated"].shift()).cumsum()

    # Group by block and filter for elevated periods
    for block_id, block in df[df["elevated"]].groupby("block"):
        duration_min = len(block)

        # Only count as workout if 10+ minutes
        if duration_min >= 10:
            start_time = block["timestamp"].min()
            end_time = block["timestamp"].max()
            avg_hr = block["bpm"].mean()
            max_hr = block["bpm"].max()

            # Estimate strain for this workout
            # Strain = elevated HR above resting * duration * scaling factor
            strain = min(10, (avg_hr - rhr) * duration_min * 0.001)

            workouts.append({
                "date": start_time.strftime("%Y-%m-%d"),
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "duration_min": duration_min,
                "avg_hr": int(avg_hr),
                "max_hr": int(max_hr),
                "strain": round(strain, 1),
                "auto_detected": True
            })

    return workouts


def save_workout(workout_data):
    """
    Save a workout to the workouts log file.

    Args:
        workout_data: Dictionary with workout details
    """
    workouts_file = "data/workouts.json"

    # Load existing workouts
    if os.path.exists(workouts_file):
        with open(workouts_file, "r") as f:
            workouts = json.load(f)
    else:
        workouts = []

    # Add new workout
    workouts.append(workout_data)

    # Save back
    os.makedirs("data", exist_ok=True)
    with open(workouts_file, "w") as f:
        json.dump(workouts, f, indent=2)


def load_workouts():
    """
    Load all workouts from the log file.

    Returns:
        List of workout dictionaries
    """
    workouts_file = "data/workouts.json"

    if os.path.exists(workouts_file):
        with open(workouts_file, "r") as f:
            return json.load(f)
    return []


def get_workout_summary(date=None):
    """
    Get workout summary for a specific date or all time.

    Args:
        date: Date string "YYYY-MM-DD" or None for all time

    Returns:
        Dictionary with summary stats
    """
    workouts = load_workouts()

    if date:
        workouts = [w for w in workouts if w["date"] == date]

    if not workouts:
        return {
            "count": 0,
            "total_duration_min": 0,
            "total_strain": 0,
            "avg_hr": 0
        }

    return {
        "count": len(workouts),
        "total_duration_min": sum(w["duration_min"] for w in workouts),
        "total_strain": sum(w["strain"] for w in workouts),
        "avg_hr": int(np.mean([w["avg_hr"] for w in workouts]))
    }


def calculate_hr_zones(hr, age=30):
    """
    Calculate which HR zone you're in (1-5).

    Zones based on % of max heart rate (220 - age):
    - Zone 1 (Recovery): 50-60% of max HR
    - Zone 2 (Endurance): 60-70%
    - Zone 3 (Tempo): 70-80%
    - Zone 4 (Threshold): 80-90%
    - Zone 5 (Max): 90-100%

    Args:
        hr: Current heart rate
        age: User's age

    Returns:
        Zone number (1-5) and zone name
    """
    max_hr = 220 - age

    percent = (hr / max_hr) * 100

    if percent < 60:
        return 1, "Recovery"
    elif percent < 70:
        return 2, "Endurance"
    elif percent < 80:
        return 3, "Tempo"
    elif percent < 90:
        return 4, "Threshold"
    else:
        return 5, "Maximum"


def get_zone_distribution(workout_hr_data, age=30):
    """
    Calculate time spent in each HR zone during a workout.

    Args:
        workout_hr_data: List of heart rate readings during workout
        age: User's age

    Returns:
        Dictionary with minutes in each zone
    """
    zones = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for hr in workout_hr_data:
        zone_num, _ = calculate_hr_zones(hr, age)
        zones[zone_num] += 1

    return zones
