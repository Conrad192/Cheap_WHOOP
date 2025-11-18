# ============================================================================
# CALIBRATION.PY - Calibrate wrist device against chest strap
# ============================================================================
# Wrist-based HR monitors are less accurate than chest straps.
# This module creates correction factors by comparing simultaneous readings.
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

def calibrate_wrist_to_chest(xiaomi_file, coospo_file, output_file="data/calibration.json"):
    """
    Compare simultaneous readings from wrist and chest to create correction factors.
    
    How to use:
    1. Wear BOTH Xiaomi band and Coospo chest strap during a workout
    2. Run this function with both data files
    3. Correction factors are saved and automatically applied to future data
    
    Args:
        xiaomi_file: Path to Xiaomi data CSV
        coospo_file: Path to Coospo data CSV
        output_file: Where to save calibration factors
    
    Returns:
        Dictionary with calibration factors and accuracy info
    """
    # ========================================================================
    # LOAD BOTH DATA FILES
    # ========================================================================
    xiaomi = pd.read_csv(xiaomi_file, parse_dates=["timestamp"])
    coospo = pd.read_csv(coospo_file, parse_dates=["timestamp"])
    
    # ========================================================================
    # MERGE ON TIMESTAMP (within 1 minute tolerance)
    # ========================================================================
    # This matches up readings that happened at the same time
    merged = pd.merge_asof(
        xiaomi.sort_values("timestamp"),
        coospo.sort_values("timestamp"),
        on="timestamp",
        tolerance=pd.Timedelta("1min"),  # Allow 1-minute difference
        suffixes=("_wrist", "_chest")
    ).dropna()
    
    # ========================================================================
    # VALIDATE SUFFICIENT DATA
    # ========================================================================
    # Need at least 30 matching data points for reliable calibration
    if len(merged) < 30:
        return {
            "error": "Not enough overlapping data. Wear both devices for at least 20 minutes.",
            "samples": len(merged)
        }
    
    # ========================================================================
    # CALCULATE CORRECTION FACTORS
    # ========================================================================
    # chest = true value (more accurate)
    # wrist = measured value (what we want to correct)
    # Formula: true_value = (measured_value * slope) + intercept
    
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
    
    # Calculate accuracy improvement
    bpm_error_before = abs(merged["bpm_wrist"] - merged["bpm_chest"]).mean()
    
    # ========================================================================
    # SAVE CALIBRATION DATA
    # ========================================================================
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
    
    Args:
        df: DataFrame with 'bpm' and 'rr_ms' columns
        calibration_file: Path to calibration JSON file
    
    Returns:
        DataFrame with corrected values
    """
    try:
        # Load calibration factors
        with open(calibration_file) as f:
            cal = json.load(f)
        
        # Apply correction formulas
        df["bpm"] = df["bpm"] * cal["bpm_slope"] + cal["bpm_intercept"]
        df["rr_ms"] = df["rr_ms"] * cal["rr_slope"] + cal["rr_intercept"]
        
        print("✅ Calibration applied to data")
    except FileNotFoundError:
        # No calibration file exists - use raw data
        print("ℹ️  No calibration file found - using raw data")
    
    return df


def get_calibration_status():
    """
    Check if calibration exists and when it was done.
    
    Returns:
        Dictionary with calibration info, or None if no calibration exists
    """
    calibration_file = "data/calibration.json"
    
    if not os.path.exists(calibration_file):
        return None
    
    try:
        with open(calibration_file) as f:
            cal = json.load(f)
        return cal
    except:
        return None