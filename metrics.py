# Import tools
import pandas as pd
import numpy as np

# Main function: returns all scores
def get_metrics():
    # Load merged data
    df = pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])
    
    # HRV = how steady your heartbeat is (higher = better recovery)
    rr = df["rr_ms"].dropna()  # Remove missing
    hrv = np.sqrt(np.mean(np.diff(rr)**2)) if len(rr) > 1 else 50  # RMSSD formula

    # Resting HR = lowest 5% during night (12am–6am)
    night = df[df["timestamp"].dt.hour.between(0, 6)]
    rhr = night["bpm"].quantile(0.05) if not night.empty else 60

    # Strain = how hard your day was (WHOOP style)
    excess = df["bpm"] - rhr
    strain = min(21, np.sum(excess[excess > 0]) * 0.0001)  # Scale to 0–21

    # Recovery = combo of HRV + resting HR
    recovery = min(100, max(33, (hrv / 80) * 100 * (60 / rhr)))

    # Sleep metrics (from Xiaomi stages)
    sleep_df = df[df["sleep_stage"] > 0]  # Only sleeping periods
    sleep_duration = len(sleep_df) / 60  # Hours
    deep = len(sleep_df[sleep_df["sleep_stage"] == 2]) / 60
    rem = len(sleep_df[sleep_df["sleep_stage"] == 3]) / 60
    light = len(sleep_df[sleep_df["sleep_stage"] == 1]) / 60
    efficiency = (sleep_duration / 8) * 100 if sleep_duration > 0 else 0  # Assume 8h ideal

    # Return rounded values
    return {
        "hrv": round(hrv, 1),
        "rhr": int(rhr),
        "strain": round(strain, 1),
        "recovery": int(recovery),
        "sleep_duration": f"{int(sleep_duration)}h {int((sleep_duration % 1)*60)}m",
        "deep": f"{int(deep)}h {int((deep % 1)*60)}m",
        "rem": f"{int(rem)}h {int((rem % 1)*60)}m",
        "light": f"{int(light)}h {int((light % 1)*60)}m",
        "efficiency": f"{int(efficiency)}%"
    }

if __name__ == "__main__":
    print(get_metrics())