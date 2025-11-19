# ============================================================================
# METRICS.PY - Calculate all fitness metrics from heart rate data
# ============================================================================
# Calculates: HRV, RHR, Strain (with steps), Recovery, Sleep metrics,
# Stress, Training Readiness, and Respiratory Rate
# ============================================================================

import pandas as pd
import numpy as np

def calculate_stress_score(df):
    """
    Calculate stress level (0-10 scale).
    Higher heart rate + lower HRV = more stress
    
    This measures nervous system tension, NOT physical workload.
    """
    # Group by hour to see stress patterns throughout the day
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
    
    This is the "Should I work out hard today?" score.
    """
    # Parse sleep efficiency (it's a string like "85%")
    try:
        sleep_score = float(sleep_efficiency_str.strip('%'))
    except:
        sleep_score = 70.0  # Default
    
    # Calculate component scores
    hrv_score = min(100, (hrv / 80) * 100)  # 80ms = good HRV
    rhr_score = max(0, 100 - (rhr - 50))    # 50 BPM = excellent RHR
    
    # Weighted average (recovery is most important factor)
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
    Breathing causes regular oscillations in heart rate (RSA - respiratory sinus arrhythmia).
    
    Returns breaths per minute, or None if insufficient data.
    """
    rr = df["rr_ms"].dropna()
    
    if len(rr) < 100:
        return None  # Not enough data for reliable estimate
    
    # Simple method: breathing affects HRV in 0.2-0.4 Hz range
    # We'll look for periodic patterns in RR intervals
    
    # Calculate differences between consecutive heartbeats
    rr_diff = np.diff(rr)
    
    # Count zero crossings (changes in trend) as rough breathing indicator
    # Typically 12-20 breaths per minute at rest
    zero_crossings = np.where(np.diff(np.sign(rr_diff)))[0]
    
    if len(zero_crossings) < 10:
        return 15.0  # Default to normal breathing
    
    # Estimate from rate of oscillations
    duration_minutes = len(rr) / 60  # Assuming 1 Hz sampling
    breaths_per_min = (len(zero_crossings) / 2) / duration_minutes
    
    # Clamp to reasonable physiological range
    return round(min(30, max(8, breaths_per_min)), 1)


def calculate_sleep_performance_score(df, sleep_duration, deep, rem, light, sleep_efficiency_pct):
    """
    Calculate comprehensive Sleep Performance Score (0-100%) similar to WHOOP.

    Components:
    1. Sleep Sufficiency (40%): Did you get enough sleep based on your needs?
    2. Sleep Efficiency (30%): Quality - % of time in bed actually asleep
    3. Sleep Consistency (20%): Regularity of sleep/wake times over last 4 days
    4. Sleep Stress (10%): Physiological stress during sleep (inverted)

    Returns dict with:
    - sleep_score: Overall performance (0-100%)
    - sufficiency, efficiency, consistency, stress_score: Individual components
    - sleep_debt: Accumulated deficit in minutes
    - restorative_sleep: % of sleep in deep + REM stages
    """

    # ========================================================================
    # 1. SLEEP SUFFICIENCY (0-100%)
    # ========================================================================
    # Calculate sleep need based on baseline + strain from previous day
    # Baseline: 8 hours (can be personalized)
    # Additional need: +15 min per 5 points of strain

    baseline_need = 8.0  # hours

    # Try to get previous day's strain from history
    try:
        history = pd.read_csv("data/history.csv")
        if not history.empty and len(history) >= 2:
            prev_strain = history.iloc[-2]["strain"]  # Yesterday's strain
            additional_need = (prev_strain / 5) * 0.25  # +15min per 5 strain points
        else:
            additional_need = 0
    except:
        additional_need = 0

    sleep_need = baseline_need + additional_need
    sufficiency = min(100, (sleep_duration / sleep_need) * 100)

    # Calculate sleep debt (accumulated deficit)
    sleep_debt_hours = max(0, sleep_need - sleep_duration)
    sleep_debt_minutes = int(sleep_debt_hours * 60)

    # ========================================================================
    # 2. SLEEP EFFICIENCY (0-100%)
    # ========================================================================
    # We already have this from the caller
    efficiency = sleep_efficiency_pct

    # ========================================================================
    # 3. SLEEP CONSISTENCY (0-100%)
    # ========================================================================
    # Calculate regularity of sleep/wake times over last 4 days
    # Compare bedtime and wake time variance

    try:
        # Get sleep times from last 4 days
        history = pd.read_csv("data/history.csv")

        if len(history) >= 4:
            # We need to detect sleep windows from daily data
            # For now, use a simplified approach based on sleep duration variance
            recent_sleep = history.tail(4)

            if "sleep_duration_hours" in recent_sleep.columns:
                sleep_durations = recent_sleep["sleep_duration_hours"].values
                # Calculate variance in sleep duration as proxy for consistency
                if len(sleep_durations) > 1:
                    std_dev = np.std(sleep_durations)
                    # Lower variance = higher consistency
                    # 0 hours std dev = 100%, 2 hours std dev = 0%
                    consistency = max(0, 100 - (std_dev / 2) * 100)
                else:
                    consistency = 75  # Default
            else:
                # First time tracking - analyze current day's sleep timing
                sleep_data = df[df["sleep_stage"] > 0]
                if not sleep_data.empty:
                    # Check if sleep is concentrated in expected window (10pm-6am)
                    night_sleep = sleep_data[sleep_data["timestamp"].dt.hour.between(22, 23) |
                                            sleep_data["timestamp"].dt.hour.between(0, 6)]
                    consistency = min(100, (len(night_sleep) / len(sleep_data)) * 100)
                else:
                    consistency = 75  # Default
        else:
            # Not enough history - use default moderate consistency
            consistency = 75
    except:
        consistency = 75  # Default if calculation fails

    # ========================================================================
    # 4. SLEEP STRESS (0-100%, inverted)
    # ========================================================================
    # Measure physiological stress during sleep
    # High HR + Low HRV during sleep = high stress = lower score

    sleep_periods = df[df["sleep_stage"] > 0]

    if not sleep_periods.empty and len(sleep_periods) > 10:
        # Calculate average HR and HRV during sleep
        sleep_hr = sleep_periods["bpm"].mean()
        sleep_rr = sleep_periods["rr_ms"].dropna()

        if len(sleep_rr) > 1:
            sleep_hrv = np.sqrt(np.mean(np.diff(sleep_rr)**2))  # RMSSD

            # Lower HR and higher HRV during sleep = less stress
            # Typical good sleep: HR 50-60, HRV 50-100ms
            hr_stress = max(0, (sleep_hr - 50) / 30)  # 0 if HR=50, 1 if HR=80+
            hrv_stress = max(0, (60 - sleep_hrv) / 60)  # 0 if HRV=60+, 1 if HRV=0

            stress_level = (hr_stress + hrv_stress) / 2  # 0-1 scale
            stress_score = (1 - stress_level) * 100  # Invert: lower stress = higher score
        else:
            stress_score = 75  # Default
    else:
        stress_score = 75  # Default if insufficient data

    # ========================================================================
    # 5. RESTORATIVE SLEEP (%)
    # ========================================================================
    # % of sleep time spent in Deep + REM stages
    # Target: ~50% (half of sleep should be restorative)

    restorative_hours = deep + rem
    restorative_pct = (restorative_hours / sleep_duration * 100) if sleep_duration > 0 else 0

    # ========================================================================
    # 6. COMBINED SLEEP PERFORMANCE SCORE
    # ========================================================================
    # Weighted average of all components

    sleep_score = (
        sufficiency * 0.40 +    # 40% - Most important: did you get enough?
        efficiency * 0.30 +     # 30% - Quality of sleep
        consistency * 0.20 +    # 20% - Circadian rhythm alignment
        stress_score * 0.10     # 10% - Physiological stress
    )

    return {
        "sleep_score": int(min(100, max(0, sleep_score))),
        "sufficiency": int(sufficiency),
        "efficiency": int(efficiency),
        "consistency": int(consistency),
        "stress_score": int(stress_score),
        "sleep_debt_minutes": sleep_debt_minutes,
        "restorative_sleep_pct": int(restorative_pct),
        "sleep_need_hours": round(sleep_need, 1)
    }


def get_metrics():
    """
    Main function: Calculate and return all fitness metrics.

    Returns dictionary with:
    - HRV, RHR, Strain (with steps), Recovery
    - Sleep duration, stages, efficiency
    - Sleep Performance Score (WHOOP-style)
    - Stress, Readiness, Respiratory rate
    - Steps
    """
    # Load merged data from Xiaomi + Coospo
    df = pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])
    
    # ========================================================================
    # HRV (Heart Rate Variability) - RMSSD method
    # ========================================================================
    # Higher HRV = better recovery and fitness
    # Typical ranges: 20-80ms (varies by person)
    rr = df["rr_ms"].dropna()  # Remove missing values
    hrv = np.sqrt(np.mean(np.diff(rr)**2)) if len(rr) > 1 else 50  # RMSSD formula

    # ========================================================================
    # RHR (Resting Heart Rate)
    # ========================================================================
    # Lowest 5% of heart rate during night (12am–6am)
    # Lower RHR = better cardiovascular fitness
    # Typical ranges: 40-100 BPM (athletes: 40-60)
    night = df[df["timestamp"].dt.hour.between(0, 6)]
    rhr = night["bpm"].quantile(0.05) if not night.empty else 60

    # ========================================================================
    # STEPS - Get total steps for the day
    # ========================================================================
    total_steps = df["steps"].max() if "steps" in df.columns else 0
    
    # ========================================================================
    # STRAIN - Cardiovascular load (0-21 scale, WHOOP-style)
    # ========================================================================
    # Combines heart rate elevation + step count
    # 0-7: Light day
    # 7-14: Moderate activity
    # 14-21: Hard training
    
    # Part 1: Heart rate-based strain
    excess = df["bpm"] - rhr  # How much above resting
    hr_strain = min(21, np.sum(excess[excess > 0]) * 0.0001)  # Scale to 0–21
    
    # Part 2: Step-based strain (10,000 steps ≈ 3 strain points)
    step_strain = (total_steps / 10000) * 3
    
    # Combined strain
    strain = min(21, hr_strain + step_strain)

    # ========================================================================
    # RECOVERY - How well you recovered overnight (0-100%)
    # ========================================================================
    # Based on HRV and RHR
    # 67-100: Great recovery, ready to train
    # 34-66: Moderate recovery, light workout
    # 0-33: Poor recovery, rest day
    recovery = min(100, max(33, (hrv / 80) * 100 * (60 / rhr)))

    # ========================================================================
    # SLEEP METRICS
    # ========================================================================
    # Extract sleep stages from Xiaomi data
    # 0 = awake, 1 = light, 2 = deep, 3 = REM
    sleep_df = df[df["sleep_stage"] > 0]  # Only sleeping periods

    # Calculate durations (data is per-minute, convert to hours)
    sleep_duration = len(sleep_df) / 60  # Total sleep in hours
    deep = len(sleep_df[sleep_df["sleep_stage"] == 2]) / 60  # Deep sleep hours
    rem = len(sleep_df[sleep_df["sleep_stage"] == 3]) / 60   # REM sleep hours
    light = len(sleep_df[sleep_df["sleep_stage"] == 1]) / 60  # Light sleep hours

    # Sleep efficiency (% of 8-hour ideal)
    efficiency = (sleep_duration / 8) * 100 if sleep_duration > 0 else 0
    efficiency_str = f"{int(efficiency)}%"

    # Calculate comprehensive sleep performance score (WHOOP-style)
    sleep_perf = calculate_sleep_performance_score(
        df, sleep_duration, deep, rem, light, efficiency
    )
    
    # ========================================================================
    # ADVANCED METRICS
    # ========================================================================
    # Calculate stress, readiness, and respiratory rate
    # Note: rhr must be calculated BEFORE calling these functions
    stress = calculate_stress_score(df)
    readiness = calculate_training_readiness(hrv, rhr, recovery, efficiency_str)
    respiratory_rate = estimate_respiratory_rate(df)

    # ========================================================================
    # RETURN ALL METRICS
    # ========================================================================
    return {
        # Core metrics
        "hrv": round(hrv, 1),
        "rhr": int(rhr),
        "strain": round(strain, 1),
        "recovery": int(recovery),

        # Sleep metrics (formatted as strings)
        "sleep_duration": f"{int(sleep_duration)}h {int((sleep_duration % 1)*60)}m",
        "deep": f"{int(deep)}h {int((deep % 1)*60)}m",
        "rem": f"{int(rem)}h {int((rem % 1)*60)}m",
        "light": f"{int(light)}h {int((light % 1)*60)}m",
        "efficiency": efficiency_str,

        # Sleep Performance Score (WHOOP-style)
        "sleep_score": sleep_perf["sleep_score"],
        "sleep_sufficiency": sleep_perf["sufficiency"],
        "sleep_consistency": sleep_perf["consistency"],
        "sleep_stress_score": sleep_perf["stress_score"],
        "sleep_debt_minutes": sleep_perf["sleep_debt_minutes"],
        "restorative_sleep_pct": sleep_perf["restorative_sleep_pct"],
        "sleep_need_hours": sleep_perf["sleep_need_hours"],

        # Sleep metrics as numbers (for history storage)
        "sleep_duration_hours": round(sleep_duration, 2),
        "deep_hours": round(deep, 2),
        "rem_hours": round(rem, 2),
        "light_hours": round(light, 2),
        "sleep_efficiency_pct": int(efficiency),

        # Advanced metrics
        "stress": round(stress, 1),
        "readiness": readiness,
        "respiratory_rate": respiratory_rate,

        # Activity
        "steps": int(total_steps)
    }


# For testing: run this file directly to see current metrics
if __name__ == "__main__":
    print(get_metrics())