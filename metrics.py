# Import tools
import pandas as pd
import numpy as np

def calculate_stress_score(df):
    """
    Calculate stress level (0-10 scale).
    Higher heart rate + lower HRV = more stress
    """
    # Group by hour to see stress patterns
    hourly = df.set_index("timestamp").resample("1H").agg({
        "bpm": "mean",
        "rr_ms": lambda x: np.std(np.diff(x.dropna())) if len(x) > 1 else 0
    })
    
    if hourly.empty:
        return 5.0  # Default moderate stress
    
    # Normalize: high HR + low HRV variation = high stress
    # Scale to 0-10 range
    hr_component = (hourly["bpm"] / 100)  # Higher HR = more stress
    hrv_component = (50 / (hourly["rr_ms"] + 1))  # Lower HRV = more stress
    
    stress = (hr_component * hrv_component).mean() * 10
    return min(10.0, max(0.0, stress))


def calculate_training_readiness(hrv, rhr, recovery, sleep_efficiency_str):
    """
    Calculate if you're ready for hard training (0-100 scale).
    Combines HRV, resting HR, recovery, and sleep quality.
    """
    # Parse sleep efficiency (it's a string like "85%")
    try:
        sleep_score = float(sleep_efficiency_str.strip('%'))
    except:
        sleep_score = 70.0
    
    # Calculate component scores
    hrv_score = min(100, (hrv / 80) * 100)  # 80ms = good HRV
    rhr_score = max(0, 100 - (rhr - 50))    # 50 BPM = excellent RHR
    
    # Weighted average (recovery is most important)
    readiness = (
        hrv_score * 0.25 +      # 25% weight
        rhr_score * 0.15 +      # 15% weight
        recovery * 0.40 +       # 40% weight (most important)
        sleep_score * 0.20      # 20% weight
    )
    
    return int(min(100, max(0, readiness)))


def estimate_respiratory_rate(df):
    """
    Estimate breathing rate from heart rate variability patterns.
    Breathing causes regular oscillations in heart rate (respiratory sinus arrhythmia).
    Returns breaths per minute.
    """
    rr = df["rr_ms"].dropna()
    
    if len(rr) < 100:
        return None  # Not enough data
    
    # Simple method: breathing affects HRV in 0.2-0.4 Hz range
    # We'll look for periodic patterns in RR intervals
    
    # Calculate differences between consecutive heartbeats
    rr_diff = np.diff(rr)
    
    # Count zero crossings (changes in trend) as rough breathing indicator
    # Typically 12-20 breaths per minute
    zero_crossings = np.where(np.diff(np.sign(rr_diff)))[0]
    
    if len(zero_crossings) < 10:
        return 15.0  # Default to normal breathing
    
    # Estimate from rate of oscillations
    duration_minutes = len(rr) / 60  # Assuming 1 Hz sampling
    breaths_per_min = (len(zero_crossings) / 2) / duration_minutes
    
    # Clamp to reasonable range
    return round(min(30, max(8, breaths_per_min)), 1)


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

    # Get total steps for the day
    total_steps = df["steps"].max() if "steps" in df.columns else 0
    
    # Improved strain calculation with steps
    # Base strain from HR
    excess = df["bpm"] - rhr
    hr_strain = min(21, np.sum(excess[excess > 0]) * 0.0001)
    
    # Step strain (10,000 steps ≈ 3 strain points)
    step_strain = (total_steps / 10000) * 3
    
    # Combined strain
    strain = min(21, hr_strain + step_strain)

    # Recovery = combo of HRV + resting HR
    recovery = min(100, max(33, (hrv / 80) * 100 * (60 / rhr)))

    # Sleep metrics (from Xiaomi stages)
    sleep_df = df[df["sleep_stage"] > 0]  # Only sleeping periods
    sleep_duration = len(sleep_df) / 60  # Hours
    deep = len(sleep_df[sleep_df["sleep_stage"] == 2]) / 60
    rem = len(sleep_df[sleep_df["sleep_stage"] == 3]) / 60
    light = len(sleep_df[sleep_df["sleep_stage"] == 1]) / 60
    efficiency = (sleep_duration / 8) * 100 if sleep_duration > 0 else 0  # Assume 8h ideal
    efficiency_str = f"{int(efficiency)}%"
    
    # NEW METRICS (now rhr is defined before we use it)
    stress = calculate_stress_score(df)
    readiness = calculate_training_readiness(hrv, rhr, recovery, efficiency_str)
    respiratory_rate = estimate_respiratory_rate(df)

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
        "efficiency": efficiency_str,
        # New metrics
        "stress": round(stress, 1),
        "readiness": readiness,
        "respiratory_rate": respiratory_rate,
        "steps": int(total_steps)  # Add steps to return
    }

if __name__ == "__main__":
    print(get_metrics())