# Import same tools
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

os.makedirs("data/raw", exist_ok=True)

start = datetime.now().replace(hour=7, minute=0)
times = [start + timedelta(seconds=i) for i in range(1800)]  # 30 min
bpm = np.clip(np.random.normal(140, 20, 1800), 60, 190).astype(int)
rr = 60000 // bpm + np.random.normal(0, 10, 1800).astype(int)
df = pd.DataFrame({"timestamp": times, "bpm": bpm, "rr_ms": rr})
df.to_csv("data/raw/coospo_workout.csv", index=False)
print("✅ Mock Coospo workout saved to data/raw/coospo_workout.csv")

def generate_coospo_data():
    os.makedirs("data/raw", exist_ok=True)
    start = datetime.now().replace(hour=7, minute=0)
    times = [start + timedelta(seconds=i) for i in range(1800)]
    bpm = np.clip(np.random.normal(140, 20, 1800), 60, 190).astype(int)
    rr = 60000 // bpm + np.random.normal(0, 10, 1800).astype(int)
    df = pd.DataFrame({"timestamp": times, "bpm": bpm, "rr_ms": rr})
    df.to_csv("data/raw/coospo_workout.csv", index=False)

if __name__ == "__main__":
    generate_coospo_data()