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


def detect_workouts(df, rhr):
    """
    Auto-detect workouts from elevated heart rate periods.

    A workout is defined as:
    - Heart rate elevated above (RHR + 30) BPM
    - Duration of at least 10 minutes
    - Returns list of workout dictionaries with start time, duration, intensity
    """
    workouts = []

    if df.empty:
        return workouts

    # Define workout threshold (RHR + 30 BPM)
    threshold = rhr + 30

    # Find periods where HR is elevated
    df = df.sort_values("timestamp").reset_index(drop=True)
    elevated = df[df["bpm"] > threshold].copy()

    if elevated.empty:
        return workouts

    # Group consecutive elevated periods
    elevated["time_diff"] = elevated["timestamp"].diff().dt.total_seconds()
    elevated["new_workout"] = elevated["time_diff"] > 300  # 5 min gap = new workout
    elevated["workout_id"] = elevated["new_workout"].cumsum()

    # Process each workout
    for workout_id in elevated["workout_id"].unique():
        workout_data = elevated[elevated["workout_id"] == workout_id]

        duration_minutes = len(workout_data)  # Data is per-minute

        # Only include if >= 10 minutes
        if duration_minutes >= 10:
            avg_hr = workout_data["bpm"].mean()
            max_hr = workout_data["bpm"].max()
            start_time = workout_data["timestamp"].iloc[0]

            # Determine intensity based on heart rate
            if avg_hr > rhr + 60:
                intensity = "High"
            elif avg_hr > rhr + 45:
                intensity = "Moderate"
            else:
                intensity = "Light"

            workouts.append({
                "start": start_time,
                "duration_min": duration_minutes,
                "avg_hr": int(avg_hr),
                "max_hr": int(max_hr),
                "intensity": intensity
            })

    return workouts


def get_metrics():
    """
    Main function: Calculate and return all fitness metrics.

    Returns dictionary with:
    - HRV, RHR, Strain (with steps), Recovery
    - Sleep duration, stages, efficiency
    - Stress, Readiness, Respiratory rate
    - Steps
    - Workouts (auto-detected from elevated HR)
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
    
    # ========================================================================
    # ADVANCED METRICS
    # ========================================================================
    # Calculate stress, readiness, and respiratory rate
    # Note: rhr must be calculated BEFORE calling these functions
    stress = calculate_stress_score(df)
    readiness = calculate_training_readiness(hrv, rhr, recovery, efficiency_str)
    respiratory_rate = estimate_respiratory_rate(df)

    # ========================================================================
    # WORKOUT DETECTION
    # ========================================================================
    # Auto-detect workouts from elevated heart rate periods
    workouts = detect_workouts(df, rhr)

    # ========================================================================
    # SLEEP PERFORMANCE SCORE
    # ========================================================================
    # Calculate comprehensive sleep score (0-100)
    sleep_score = 0
    if sleep_duration > 0:
        duration_score = min(100, (sleep_duration / 8) * 100)
        deep_score = min(100, (deep / 2) * 100) if deep > 0 else 0
        rem_score = min(100, (rem / 2) * 100) if rem > 0 else 0
        sleep_score = int((duration_score * 0.4) + (deep_score * 0.3) + (rem_score * 0.3))

    # ========================================================================
    # VO2 MAX ESTIMATION
    # ========================================================================
    # Simple estimation based on RHR and age (assuming age 30)
    vo2_max = max(35, min(80, 15.3 * (220 - 30) / rhr))

    # ========================================================================
    # SPO2 DATA
    # ========================================================================
    spo2_data = None
    if "spo2" in df.columns:
        spo2_readings = df["spo2"].dropna()
        if len(spo2_readings) > 0:
            excellent = len(spo2_readings[spo2_readings >= 98])
            good = len(spo2_readings[(spo2_readings >= 95) & (spo2_readings < 98)])
            low = len(spo2_readings[spo2_readings < 95])
            total = len(spo2_readings)

            spo2_data = {
                "avg": int(spo2_readings.mean()),
                "min": int(spo2_readings.min()),
                "max": int(spo2_readings.max()),
                "excellent_pct": int((excellent / total) * 100),
                "good_pct": int((good / total) * 100),
                "low_pct": int((low / total) * 100),
                "alerts": ["Low oxygen detected" if spo2_readings.min() < 90 else ""]
            }

    # ========================================================================
    # HEART RATE ZONES
    # ========================================================================
    max_hr = 220 - 30  # Assuming age 30
    zones = {
        "Zone 1 (50-60%)": len(df[(df["bpm"] >= max_hr * 0.5) & (df["bpm"] < max_hr * 0.6)]),
        "Zone 2 (60-70%)": len(df[(df["bpm"] >= max_hr * 0.6) & (df["bpm"] < max_hr * 0.7)]),
        "Zone 3 (70-80%)": len(df[(df["bpm"] >= max_hr * 0.7) & (df["bpm"] < max_hr * 0.8)]),
        "Zone 4 (80-90%)": len(df[(df["bpm"] >= max_hr * 0.8) & (df["bpm"] < max_hr * 0.9)]),
        "Zone 5 (90-100%)": len(df[df["bpm"] >= max_hr * 0.9])
    }

    # ========================================================================
    # HOURLY STRAIN
    # ========================================================================
    hourly_strain = df.set_index("timestamp").resample("1H")["bpm"].apply(
        lambda x: min(21, np.sum((x - rhr)[x > rhr]) * 0.0001) if len(x) > 0 else 0
    )

    # ========================================================================
    # STRAIN GOAL & COACH
    # ========================================================================
    if recovery >= 67:
        strain_goal = {"min": 10, "max": 18, "label": "High Intensity"}
        strain_coach = "Your recovery is strong. You can push hard today."
    elif recovery >= 34:
        strain_goal = {"min": 6, "max": 12, "label": "Moderate Intensity"}
        strain_coach = "Moderate recovery. Focus on quality over quantity."
    else:
        strain_goal = {"min": 0, "max": 6, "label": "Light Activity"}
        strain_coach = "Prioritize rest and recovery today."

    # ========================================================================
    # OVERTRAINING & REST DAY DETECTION
    # ========================================================================
    overtraining = {
        "risk": "low",
        "alerts": [],
        "recommendation": "Keep training as planned"
    }
    if strain > 18 and recovery < 50:
        overtraining["risk"] = "high"
        overtraining["alerts"].append("High strain with low recovery")
        overtraining["recommendation"] = "Take a rest day"
    elif strain > 15 and recovery < 60:
        overtraining["risk"] = "moderate"
        overtraining["alerts"].append("Elevated strain with moderate recovery")
        overtraining["recommendation"] = "Light activity only"

    rest_day = None
    if recovery < 34:
        rest_day = {
            "rest_recommended": True,
            "reasons": ["Recovery below 34%", "Body needs rest"]
        }

    # ========================================================================
    # RECOVERY PREDICTION
    # ========================================================================
    recovery_prediction = None
    if strain < 10:
        predicted = min(100, recovery + 10)
        confidence = "high"
    elif strain < 15:
        predicted = recovery
        confidence = "medium"
    else:
        predicted = max(33, recovery - 10)
        confidence = "low"

    recovery_prediction = {
        "predicted_recovery": predicted,
        "confidence": confidence,
        "factors": {
            "hrv_trend": "stable",
            "rhr_trend": "stable",
            "strain_level": "high" if strain > 15 else "moderate" if strain > 10 else "low"
        }
    }

    # ========================================================================
    # TRAINING LOAD (7-day total strain)
    # ========================================================================
    training_load = strain * 7  # Simplified - would need history for real calculation

    # ========================================================================
    # ACHIEVEMENTS & RECORDS
    # ========================================================================
    achievements = []
    if recovery >= 90:
        achievements.append({"icon": "⭐", "name": "Peak Recovery", "description": "Recovery above 90%"})
    if strain >= 18:
        achievements.append({"icon": "🔥", "name": "Beast Mode", "description": "Strain above 18"})

    personal_records = {
        "best_recovery": recovery,
        "best_recovery_date": "Today",
        "highest_hrv": int(hrv),
        "highest_hrv_date": "Today",
        "lowest_rhr": int(rhr),
        "lowest_rhr_date": "Today",
        "max_strain": round(strain, 1),
        "max_strain_date": "Today",
        "max_steps": int(total_steps),
        "max_steps_date": "Today"
    }

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
        "sleep_duration_hours": sleep_duration,
        "deep": f"{int(deep)}h {int((deep % 1)*60)}m",
        "deep_hours": deep,
        "rem": f"{int(rem)}h {int((rem % 1)*60)}m",
        "rem_hours": rem,
        "light": f"{int(light)}h {int((light % 1)*60)}m",
        "light_hours": light,
        "efficiency": efficiency_str,
        "sleep_score": sleep_score,

        # Advanced metrics
        "stress": round(stress, 1),
        "readiness": readiness,
        "respiratory_rate": respiratory_rate,
        "vo2_max": round(vo2_max, 1),
        "spo2_data": spo2_data,
        "hr_zones": zones,
        "hourly_strain": hourly_strain,

        # Training guidance
        "strain_goal": strain_goal,
        "strain_coach": strain_coach,
        "overtraining": overtraining,
        "rest_day": rest_day,
        "recovery_prediction": recovery_prediction,
        "training_load": training_load,

        # Activity
        "steps": int(total_steps),

        # Workouts (auto-detected)
        "workouts": workouts,

        # Achievements
        "achievements": achievements,
        "personal_records": personal_records
    }


# For testing: run this file directly to see current metrics
if __name__ == "__main__":
    print(get_metrics())