import pandas as pd
import os

os.makedirs("data/merged", exist_ok=True)

xiaomi = pd.read_csv("data/raw/xiaomi_today.csv", parse_dates=["timestamp"])

try:
    coospo = pd.read_csv("data/raw/coospo_workout.csv", parse_dates=["timestamp"])
    merged = pd.concat([xiaomi, coospo]).sort_values("timestamp").drop_duplicates("timestamp")
except:
    merged = xiaomi

merged.to_csv("data/merged/daily_merged.csv", index=False)

print("✅ All data merged → data/merged/daily_merged.csv")