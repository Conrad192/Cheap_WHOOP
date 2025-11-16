import pandas as pd
import os
from calibration import apply_calibration

def merge_data():
    """Merge Xiaomi and Coospo data, applying calibration if available"""
    os.makedirs("data/merged", exist_ok=True)

    # Load Xiaomi data
    xiaomi = pd.read_csv("data/raw/xiaomi_today.csv", parse_dates=["timestamp"])
    
    # Apply calibration to make it more accurate
    xiaomi = apply_calibration(xiaomi)

    # Try to load Coospo workout data
    try:
        coospo = pd.read_csv("data/raw/coospo_workout.csv", parse_dates=["timestamp"])
        merged = pd.concat([xiaomi, coospo]).sort_values("timestamp").drop_duplicates("timestamp")
    except:
        merged = xiaomi

    merged.to_csv("data/merged/daily_merged.csv", index=False)
    print("✅ All data merged → data/merged/daily_merged.csv")

if __name__ == "__main__":
    merge_data()