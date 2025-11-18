# ============================================================================
# MERGE.PY - Combine data from multiple devices
# ============================================================================
# Merges Xiaomi (all-day tracking) with Coospo (workout) data.
# Applies calibration if available to improve accuracy.
# ============================================================================

import pandas as pd
import os
from calibration import apply_calibration

def merge_data():
    """
    Merge Xiaomi and Coospo data into a single daily dataset.
    
    Process:
    1. Load Xiaomi data (24-hour tracking)
    2. Apply calibration correction if available (makes wrist data more accurate)
    3. Load Coospo data (workout periods)
    4. Combine both datasets, removing duplicates
    5. Save merged data for analysis
    """
    # Create output directory
    os.makedirs("data/merged", exist_ok=True)

    # ========================================================================
    # LOAD XIAOMI DATA (All-day tracking from wrist device)
    # ========================================================================
    xiaomi = pd.read_csv("data/raw/xiaomi_today.csv", parse_dates=["timestamp"])
    
    # ========================================================================
    # APPLY CALIBRATION (if available)
    # ========================================================================
    # This corrects wrist measurements to match chest strap accuracy
    # See calibration.py for how this works
    xiaomi = apply_calibration(xiaomi)

    # ========================================================================
    # LOAD COOSPO DATA (Workout tracking from chest strap)
    # ========================================================================
    try:
        coospo = pd.read_csv("data/raw/coospo_workout.csv", parse_dates=["timestamp"])
        
        # Combine both datasets
        # Coospo data will override Xiaomi data for overlapping timestamps
        merged = pd.concat([xiaomi, coospo]).sort_values("timestamp").drop_duplicates("timestamp")
    except FileNotFoundError:
        # If no workout data exists, just use Xiaomi data
        merged = xiaomi

    # ========================================================================
    # SAVE MERGED DATA
    # ========================================================================
    merged.to_csv("data/merged/daily_merged.csv", index=False)
    print("✅ All data merged → data/merged/daily_merged.csv")


# For testing: run this file directly to merge existing data
if __name__ == "__main__":
    merge_data()