# Import tools
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_xiaomi_data():
    """Generate mock Xiaomi Smart Band data with steps"""
    # Create folder if needed
    os.makedirs("data/raw", exist_ok=True)

    # Start time = midnight today
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Make 1440 timestamps (1 per minute in a day)
    times = [start + timedelta(minutes=i) for i in range(1440)]

    # Fake heart rate: average 70 bpm, random variation
    bpm = np.random.normal(70, 10, 1440).astype(int)   # Normal = bell curve

    # RR interval = time between beats (ms). 60,000 / BPM
    rr = 60000 // bpm + np.random.normal(0, 20, 1440).astype(int)

    # Fake SpO2
    spo2 = np.random.randint(95, 100, 1440)

    # Add mock sleep stages (e.g., 0=awake, 1=light, 2=deep, 3=REM) for night hours
    stages = np.zeros(1440, dtype=int)
    night_start = 1320  # 10pm = 22*60 = 1320 min
    stages[night_start:] = np.random.choice([1,2,3], len(stages[night_start:]), p=[0.6,0.2,0.2])  # Mostly light

    # Generate realistic step data (accumulates through the day)
    # Most people sleep 10pm-6am (480 minutes), so no steps then
    steps_per_hour = np.zeros(24)
    
    # Active hours (6am - 10pm = hours 6-22)
    active_hours = list(range(6, 22))
    for hour in active_hours:
        # Random steps each hour (200-800 steps)
        # Peak activity usually midday
        if 11 <= hour <= 14:  # Lunch time - more activity
            steps_per_hour[hour] = np.random.randint(500, 1000)
        elif 17 <= hour <= 19:  # Evening - more activity
            steps_per_hour[hour] = np.random.randint(400, 800)
        else:
            steps_per_hour[hour] = np.random.randint(200, 600)
    
    # Create cumulative steps (running total throughout day)
    cumulative_steps = np.cumsum(steps_per_hour)
    
    # Repeat each hour's total for 60 minutes
    steps = np.repeat(cumulative_steps, 60)

    # Make table
    df = pd.DataFrame({
        "timestamp": times,
        "bpm": bpm,
        "rr_ms": rr,
        "spo2": spo2,
        "sleep_stage": stages,
        "steps": steps
    })

    # Save
    df.to_csv("data/raw/xiaomi_today.csv", index=False)
    print(f"✅ Mock Xiaomi data saved with {int(steps[-1])} total steps")

if __name__ == "__main__":
    generate_xiaomi_data()