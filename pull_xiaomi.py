# ============================================================================
# PULL_XIAOMI.PY - Generate mock Xiaomi Smart Band data
# ============================================================================
# Simulates data from Xiaomi Mi Band including:
# - Heart rate (BPM)
# - RR intervals (ms between beats)
# - SpO2 (blood oxygen)
# - Sleep stages
# - Step count (NEW)
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_xiaomi_data():
    """
    Generate realistic mock Xiaomi Smart Band data for one full day.
    
    Data includes:
    - 1440 data points (one per minute for 24 hours)
    - Realistic heart rate patterns (lower at night, higher during day)
    - Step accumulation throughout active hours
    - Sleep stage detection (10pm - 6am)
    """
    # Create data directory if it doesn't exist
    os.makedirs("data/raw", exist_ok=True)

    # ========================================================================
    # TIMESTAMPS - One per minute for full day
    # ========================================================================
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    times = [start + timedelta(minutes=i) for i in range(1440)]

    # ========================================================================
    # HEART RATE - Realistic daily pattern
    # ========================================================================
    # Average 70 BPM with variation
    # Lower during sleep, higher during activity
    bpm = np.random.normal(70, 10, 1440).astype(int)
    
    # Make sleep hours (10pm-6am) have lower heart rate
    sleep_indices = list(range(0, 360)) + list(range(1320, 1440))  # 12am-6am, 10pm-12am
    bpm[sleep_indices] = np.random.normal(60, 8, len(sleep_indices)).astype(int)

    # ========================================================================
    # RR INTERVALS - Time between heartbeats (milliseconds)
    # ========================================================================
    # Formula: 60,000 ms per minute / BPM = ms between beats
    # Add some natural variation
    rr = 60000 // bpm + np.random.normal(0, 20, 1440).astype(int)

    # ========================================================================
    # SPO2 - Blood oxygen saturation (%)
    # ========================================================================
    # Normal range: 95-100%
    spo2 = np.random.randint(95, 100, 1440)

    # ========================================================================
    # SLEEP STAGES
    # ========================================================================
    # 0 = awake, 1 = light sleep, 2 = deep sleep, 3 = REM sleep
    stages = np.zeros(1440, dtype=int)
    
    # Sleep period: 10pm - 6am (480 minutes of sleep)
    night_start = 1320  # 10pm = 22*60 = 1320 minutes from midnight
    
    # Sleep stages during night (mostly light sleep, some deep and REM)
    stages[night_start:] = np.random.choice(
        [1, 2, 3],  # Light, Deep, REM
        len(stages[night_start:]),
        p=[0.6, 0.2, 0.2]  # 60% light, 20% deep, 20% REM
    )

    # ========================================================================
    # STEP COUNT - Realistic accumulation throughout the day
    # ========================================================================
    # Most people sleep 10pm-6am, so no steps during that time
    # Peak activity at lunch (11am-2pm) and evening (5pm-7pm)
    
    steps_per_hour = np.zeros(24)
    
    # Active hours: 6am - 10pm (hours 6-22)
    active_hours = list(range(6, 22))
    
    for hour in active_hours:
        if 11 <= hour <= 14:  # Lunch time - more walking
            steps_per_hour[hour] = np.random.randint(500, 1000)
        elif 17 <= hour <= 19:  # Evening - commute/errands
            steps_per_hour[hour] = np.random.randint(400, 800)
        else:  # Normal activity
            steps_per_hour[hour] = np.random.randint(200, 600)
    
    # Create cumulative steps (running total throughout day)
    cumulative_steps = np.cumsum(steps_per_hour)
    
    # Repeat each hour's total for all 60 minutes in that hour
    # This creates a "staircase" pattern where steps increase each hour
    steps = np.repeat(cumulative_steps, 60)

    # ========================================================================
    # CREATE DATAFRAME
    # ========================================================================
    df = pd.DataFrame({
        "timestamp": times,
        "bpm": bpm,
        "rr_ms": rr,
        "spo2": spo2,
        "sleep_stage": stages,
        "steps": steps  # NEW: Step count column
    })

    # ========================================================================
    # SAVE TO FILE
    # ========================================================================
    df.to_csv("data/raw/xiaomi_today.csv", index=False)
    
    # Print confirmation with total steps
    total_steps = int(steps[-1])
    print(f"✅ Mock Xiaomi data saved with {total_steps:,} total steps")


# For testing: run this file directly to generate new data
if __name__ == "__main__":
    generate_xiaomi_data()