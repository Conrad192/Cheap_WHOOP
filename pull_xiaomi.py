# Import tools
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

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

# Make table
df = pd.DataFrame({
    "timestamp": times,
    "bpm": bpm,
    "rr_ms": rr,
    "spo2": spo2,
    "sleep_stage": stages
})

# Save
df.to_csv("data/raw/xiaomi_today.csv", index=False)

print("✅ Mock Xiaomi data saved to data/raw/xiaomi_today.csv (with sleep stages)")