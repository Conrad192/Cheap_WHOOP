import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

def calibrate_wrist_to_chest(xiaomi_file, coospo_file, output_file="data/calibration.json"):
    """
    Compare simultaneous readings from wrist and chest to create correction factors.
    Run this after wearing both devices during a workout.
    """
    # Load both data files
    xiaomi = pd.read_csv(xiaomi_file, parse_dates=["timestamp"])
    coospo = pd.read_csv(coospo_file, parse_dates=["timestamp"])
    
    # Merge on timestamp (within 1 minute tolerance)
    # This matches up readings that happened at the same time
    merged = pd.merge_asof(
        xiaomi.sort_values("timestamp"),
        coospo.sort_values("timestamp"),
        on="timestamp",
        tolerance=pd.Timedelta("1min"),
        suffixes=("_wrist", "_chest")
    ).dropna()
    
    # Need at least 30 matching data points
    if len(merged) < 30:
        return {
            "error": "Not enough overlapping data. Wear both devices for at least 20 minutes.",
            "samples": len(merged)
        }
    
    # Calculate correction factors using simple math
    # chest = true value, wrist = measured value
    # We want: true_value = (measured_value * slope) + intercept
    
    # BPM correction
    bpm_wrist_avg = merged["bpm_wrist"].mean()
    bpm_chest_avg = merged["bpm_chest"].mean()
    bpm_slope = bpm_chest_avg / bpm_wrist_avg
    bpm_intercept = bpm_chest_avg - (bpm_slope * bpm_wrist_avg)
    
    # RR interval correction
    rr_wrist_avg = merged["rr_ms_wrist"].mean()
    rr_chest_avg = merged["rr_ms_chest"].mean()
    rr_slope = rr_chest_avg / rr_wrist_avg
    rr_intercept = rr_chest_avg - (rr_slope * rr_wrist_avg)
    
    # Calculate how accurate the wrist was before calibration
    bpm_error_before = abs(merged["bpm_wrist"] - merged["bpm_chest"]).mean()
    
    # Save calibration data
    calibration = {
        "bpm_slope": float(bpm_slope),
        "bpm_intercept": float(bpm_intercept),
        "rr_slope": float(rr_slope),
        "rr_intercept": float(rr_intercept),
        "samples": len(merged),
        "date": datetime.now().isoformat(),
        "avg_error_before": float(bpm_error_before)
    }
    
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(calibration, f, indent=2)
    
    return calibration


def apply_calibration(df, calibration_file="data/calibration.json"):
    """
    Apply calibration correction to wrist data.
    This makes wrist readings more like chest strap readings.
    """
    try:
        with open(calibration_file) as f:
            cal = json.load(f)
        
        # Apply correction formulas
        df["bpm"] = df["bpm"] * cal["bpm_slope"] + cal["bpm_intercept"]
        df["rr_ms"] = df["rr_ms"] * cal["rr_slope"] + cal["rr_intercept"]
        
        print("✅ Calibration applied to data")
    except FileNotFoundError:
        print("ℹ️  No calibration file found - using raw data")
    
    return df


def get_calibration_status():
    """Check if calibration exists and when it was done"""
    calibration_file = "data/calibration.json"
    
    if not os.path.exists(calibration_file):
        return None
    
    try:
        with open(calibration_file) as f:
            cal = json.load(f)
        return cal
    except:
        return None