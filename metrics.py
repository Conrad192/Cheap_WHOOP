# ============================================================================
# METRICS.PY - Calculate all fitness metrics from heart rate data
# ============================================================================
# Calculates: HRV, RHR, Strain (with steps), Recovery, Sleep metrics,
# Stress, Training Readiness, Respiratory Rate, and many more advanced metrics
# ============================================================================

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

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


def calculate_sleep_performance_score(sleep_duration_hours, deep_hours, rem_hours, efficiency_pct, hrv, spo2_avg=None):
    """
    Calculate comprehensive sleep performance score (0-100).

    Factors:
    - Duration (target: 7-9 hours)
    - Deep sleep (target: 1.5-2 hours)
    - REM sleep (target: 1.5-2.5 hours)
    - Efficiency (target: >85%)
    - HRV during sleep (higher = better)
    - SpO2 (optional, target: >95%)
    """
    score = 0

    # Duration score (30 points)
    if 7 <= sleep_duration_hours <= 9:
        duration_score = 30
    elif sleep_duration_hours >= 6:
        duration_score = 20 + min(10, (sleep_duration_hours - 6) * 10)
    else:
        duration_score = max(0, sleep_duration_hours * 5)
    score += duration_score

    # Deep sleep score (25 points)
    if 1.5 <= deep_hours <= 2.5:
        deep_score = 25
    else:
        deep_score = max(0, 25 - abs(deep_hours - 2) * 10)
    score += deep_score

    # REM sleep score (20 points)
    if 1.5 <= rem_hours <= 2.5:
        rem_score = 20
    else:
        rem_score = max(0, 20 - abs(rem_hours - 2) * 8)
    score += rem_score

    # Efficiency score (15 points)
    efficiency_score = min(15, (efficiency_pct / 100) * 15)
    score += efficiency_score

    # HRV score (10 points) - higher HRV during sleep = better recovery
    hrv_score = min(10, (hrv / 80) * 10)
    score += hrv_score

    # SpO2 score (optional, bonus points)
    if spo2_avg:
        if spo2_avg >= 95:
            score += 5
        elif spo2_avg >= 90:
            score += 2

    return int(min(100, score))


def analyze_spo2_trends(df):
    """
    Analyze SpO2 (blood oxygen) trends and detect potential issues.
    Returns average SpO2, minimum, and alerts.
    """
    if "spo2" not in df.columns:
        return None

    spo2_data = df["spo2"].dropna()
    if len(spo2_data) == 0:
        return None

    avg_spo2 = spo2_data.mean()
    min_spo2 = spo2_data.min()

    # Detect issues
    alerts = []
    if avg_spo2 < 95:
        alerts.append("Average SpO2 below normal (95%)")
    if min_spo2 < 90:
        alerts.append("⚠️ Critical: SpO2 dropped below 90%")

    # Calculate time spent in different ranges
    excellent = len(spo2_data[spo2_data >= 98]) / len(spo2_data) * 100
    good = len(spo2_data[(spo2_data >= 95) & (spo2_data < 98)]) / len(spo2_data) * 100
    low = len(spo2_data[spo2_data < 95]) / len(spo2_data) * 100

    return {
        "avg": round(avg_spo2, 1),
        "min": round(min_spo2, 1),
        "max": round(spo2_data.max(), 1),
        "excellent_pct": round(excellent, 1),
        "good_pct": round(good, 1),
        "low_pct": round(low, 1),
        "alerts": alerts
    }


def predict_recovery(history_df=None):
    """
    Predict tomorrow's recovery based on historical patterns.
    Uses recent trends in HRV, RHR, strain, and sleep.
    """
    if history_df is None or len(history_df) < 3:
        return None

    recent = history_df.tail(7)

    # Analyze trends
    hrv_trend = recent["hrv"].diff().mean()  # Positive = improving
    rhr_trend = recent["rhr"].diff().mean()  # Negative = improving
    strain_avg = recent["strain"].mean()
    recovery_avg = recent["recovery"].mean()

    # Prediction model
    prediction = recovery_avg

    # Adjust based on trends
    if hrv_trend > 0:
        prediction += 5  # HRV improving
    elif hrv_trend < -5:
        prediction -= 5  # HRV declining

    if rhr_trend < 0:
        prediction += 3  # RHR improving
    elif rhr_trend > 2:
        prediction -= 3  # RHR increasing

    # Adjust based on recent strain
    if strain_avg > 15:
        prediction -= 5  # High strain may reduce recovery
    elif strain_avg < 8:
        prediction += 3  # Low strain helps recovery

    prediction = int(min(100, max(0, prediction)))

    return {
        "predicted_recovery": prediction,
        "confidence": "high" if len(recent) >= 7 else "medium",
        "factors": {
            "hrv_trend": "improving" if hrv_trend > 0 else "declining",
            "rhr_trend": "improving" if rhr_trend < 0 else "declining",
            "strain_level": "high" if strain_avg > 15 else "moderate" if strain_avg > 10 else "low"
        }
    }


def detect_overtraining(history_df=None, current_metrics=None):
    """
    Detect overtraining risk based on multiple factors.
    Returns risk level and recommendations.
    """
    if history_df is None or len(history_df) < 7:
        return {"risk": "unknown", "score": 0, "alerts": []}

    recent = history_df.tail(14)

    risk_score = 0
    alerts = []

    # Factor 1: Sustained high strain
    avg_strain = recent["strain"].tail(7).mean()
    if avg_strain > 16:
        risk_score += 3
        alerts.append("Very high average strain (7 days)")
    elif avg_strain > 13:
        risk_score += 1

    # Factor 2: Declining HRV
    hrv_trend = recent["hrv"].tail(7).mean() - recent["hrv"].head(7).mean()
    if hrv_trend < -10:
        risk_score += 3
        alerts.append("HRV declining significantly")
    elif hrv_trend < -5:
        risk_score += 1

    # Factor 3: Elevated RHR
    rhr_trend = recent["rhr"].tail(7).mean() - recent["rhr"].head(7).mean()
    if rhr_trend > 5:
        risk_score += 3
        alerts.append("Resting heart rate elevated")
    elif rhr_trend > 2:
        risk_score += 1

    # Factor 4: Low recovery
    avg_recovery = recent["recovery"].tail(7).mean()
    if avg_recovery < 50:
        risk_score += 2
        alerts.append("Poor average recovery")

    # Factor 5: High stress
    if "stress" in recent.columns:
        avg_stress = recent["stress"].tail(7).mean()
        if avg_stress > 7:
            risk_score += 2
            alerts.append("Elevated stress levels")

    # Determine risk level
    if risk_score >= 8:
        risk = "high"
        alerts.append("🚨 REST NEEDED: High overtraining risk")
    elif risk_score >= 5:
        risk = "moderate"
        alerts.append("⚠️ Consider rest day soon")
    elif risk_score >= 3:
        risk = "low"
    else:
        risk = "minimal"

    return {
        "risk": risk,
        "score": risk_score,
        "alerts": alerts,
        "recommendation": get_overtraining_recommendation(risk)
    }


def get_overtraining_recommendation(risk_level):
    """Get specific recommendations based on overtraining risk."""
    recommendations = {
        "high": "Take 2-3 rest days. Focus on sleep, hydration, and nutrition.",
        "moderate": "Reduce training intensity. Do active recovery only.",
        "low": "Monitor closely. Keep one rest day this week.",
        "minimal": "Training load is well managed. Continue current routine."
    }
    return recommendations.get(risk_level, "Continue monitoring")


def detect_workouts(df, hr_threshold_multiplier=1.3):
    """
    Auto-detect workout periods from heart rate data.
    Returns list of workout periods with start/end times and intensity.
    """
    if df.empty or "bpm" not in df.columns:
        return []

    # Calculate baseline HR (median of low values)
    baseline_hr = df["bpm"].quantile(0.25)
    workout_threshold = baseline_hr * hr_threshold_multiplier

    # Find elevated HR periods (sustained >30% above baseline for 10+ minutes)
    df["is_workout"] = df["bpm"] > workout_threshold

    # Group consecutive workout periods
    df["workout_group"] = (df["is_workout"] != df["is_workout"].shift()).cumsum()

    workouts = []
    for group_id, group in df[df["is_workout"]].groupby("workout_group"):
        if len(group) >= 10:  # At least 10 minutes
            avg_hr = group["bpm"].mean()
            max_hr = group["bpm"].max()
            duration_min = len(group)

            # Classify intensity
            if avg_hr > baseline_hr * 1.6:
                intensity = "High"
            elif avg_hr > baseline_hr * 1.45:
                intensity = "Moderate"
            else:
                intensity = "Light"

            workouts.append({
                "start": group["timestamp"].iloc[0],
                "end": group["timestamp"].iloc[-1],
                "duration_min": duration_min,
                "avg_hr": int(avg_hr),
                "max_hr": int(max_hr),
                "intensity": intensity
            })

    return workouts


def calculate_hr_zones(df, max_hr=None, age=None):
    """
    Calculate time spent in each heart rate zone.
    Zones: Zone 1 (50-60%), Zone 2 (60-70%), Zone 3 (70-80%),
           Zone 4 (80-90%), Zone 5 (90-100%)
    """
    if df.empty or "bpm" not in df.columns:
        return None

    # Estimate max HR if not provided
    if max_hr is None:
        if age:
            max_hr = 220 - age
        else:
            max_hr = df["bpm"].quantile(0.99)  # Use 99th percentile as proxy

    # Define zones
    zones = {
        "Zone 1 (Easy)": (max_hr * 0.5, max_hr * 0.6),
        "Zone 2 (Aerobic)": (max_hr * 0.6, max_hr * 0.7),
        "Zone 3 (Tempo)": (max_hr * 0.7, max_hr * 0.8),
        "Zone 4 (Threshold)": (max_hr * 0.8, max_hr * 0.9),
        "Zone 5 (Max)": (max_hr * 0.9, max_hr * 1.0),
    }

    zone_times = {}
    for zone_name, (lower, upper) in zones.items():
        time_in_zone = len(df[(df["bpm"] >= lower) & (df["bpm"] < upper)])
        zone_times[zone_name] = time_in_zone

    return zone_times


def calculate_training_load(history_df=None):
    """
    Calculate 7-day cumulative strain (training load).
    """
    if history_df is None or len(history_df) < 1:
        return 0

    recent = history_df.tail(7)
    return round(recent["strain"].sum(), 1)


def calculate_sleep_debt(history_df=None, target_hours=8):
    """
    Calculate cumulative sleep deficit over last 7 days.
    """
    if history_df is None or "sleep_duration_hours" not in history_df.columns or len(history_df) < 1:
        return None

    recent = history_df.tail(7)
    total_sleep = recent["sleep_duration_hours"].sum()
    target_sleep = target_hours * len(recent)
    debt = target_sleep - total_sleep

    return round(debt, 1)


def calculate_sleep_consistency(history_df=None):
    """
    Calculate sleep consistency score based on bedtime and wake time regularity.
    Score: 0-100 (100 = perfect consistency)
    """
    if history_df is None or "bedtime" not in history_df.columns or len(history_df) < 3:
        return None

    recent = history_df.tail(7)

    # Calculate standard deviation of bedtimes and wake times
    bedtime_std = recent["bedtime"].std() if "bedtime" in recent.columns else 0
    waketime_std = recent["waketime"].std() if "waketime" in recent.columns else 0

    # Lower std = better consistency
    # Penalize >1 hour variation
    consistency = 100 - min(100, (bedtime_std + waketime_std) * 10)

    return int(max(0, consistency))


def recommend_optimal_bedtime(history_df=None):
    """
    Recommend optimal bedtime based on best recovery days.
    """
    if history_df is None or len(history_df) < 7:
        return None

    # Find top 3 recovery days
    top_recovery_days = history_df.nlargest(3, "recovery")

    if "bedtime" not in top_recovery_days.columns:
        return None

    optimal_bedtime = top_recovery_days["bedtime"].mean()

    return {
        "recommended_bedtime": optimal_bedtime,
        "based_on": "Your best recovery days"
    }


def calculate_hourly_strain(df):
    """
    Calculate strain breakdown by hour of day.
    """
    if df.empty:
        return None

    df["hour"] = df["timestamp"].dt.hour
    hourly_strain = df.groupby("hour").agg({
        "bpm": lambda x: np.sum((x - x.quantile(0.05)) * 0.0001)
    }).rename(columns={"bpm": "strain"})

    return hourly_strain


def estimate_vo2_max(max_hr, resting_hr, age=None):
    """
    Estimate VO2 max from heart rate data.
    Uses simplified estimation formula.
    """
    if age is None:
        age = 30  # Default

    # Simplified VO2 max estimation
    # VO2max = 15.3 × (MHR / RHR)
    vo2_max = 15.3 * (max_hr / resting_hr)

    return round(vo2_max, 1)


def calculate_personal_records(history_df=None, current_metrics=None):
    """
    Track personal records: best recovery, lowest RHR, highest HRV, etc.
    """
    if history_df is None or len(history_df) == 0:
        return {}

    records = {
        "best_recovery": int(history_df["recovery"].max()),
        "best_recovery_date": history_df.loc[history_df["recovery"].idxmax(), "date"],
        "lowest_rhr": int(history_df["rhr"].min()),
        "lowest_rhr_date": history_df.loc[history_df["rhr"].idxmin(), "date"],
        "highest_hrv": round(history_df["hrv"].max(), 1),
        "highest_hrv_date": history_df.loc[history_df["hrv"].idxmax(), "date"],
        "max_strain": round(history_df["strain"].max(), 1),
        "max_strain_date": history_df.loc[history_df["strain"].idxmax(), "date"],
    }

    if "steps" in history_df.columns:
        records["max_steps"] = int(history_df["steps"].max())
        records["max_steps_date"] = history_df.loc[history_df["steps"].idxmax(), "date"]

    return records


def calculate_achievements(history_df=None, current_metrics=None):
    """
    Calculate achievement badges based on milestones.
    """
    if history_df is None:
        return []

    achievements = []

    # Consistency badges
    if len(history_df) >= 7:
        achievements.append({"name": "Week Warrior", "description": "7 days tracked", "icon": "🏅"})
    if len(history_df) >= 30:
        achievements.append({"name": "Monthly Master", "description": "30 days tracked", "icon": "🏆"})
    if len(history_df) >= 100:
        achievements.append({"name": "Century Club", "description": "100 days tracked", "icon": "💯"})

    # Performance badges
    if len(history_df) > 0:
        if history_df["recovery"].max() >= 90:
            achievements.append({"name": "Super Recovery", "description": "Recovery ≥ 90%", "icon": "⚡"})
        if history_df["hrv"].max() >= 100:
            achievements.append({"name": "HRV Hero", "description": "HRV ≥ 100ms", "icon": "💚"})
        if "steps" in history_df.columns and history_df["steps"].max() >= 15000:
            achievements.append({"name": "Step Master", "description": "15,000 steps in a day", "icon": "🚶"})

    return achievements


def recommend_rest_day(history_df=None, current_metrics=None):
    """
    Recommend if today should be a rest day.
    """
    if current_metrics is None:
        return None

    rest_needed = False
    reasons = []

    # Check current recovery
    if current_metrics.get("recovery", 100) < 40:
        rest_needed = True
        reasons.append("Low recovery score")

    # Check training load
    if history_df is not None and len(history_df) >= 3:
        recent_strain = history_df.tail(3)["strain"].mean()
        if recent_strain > 16:
            rest_needed = True
            reasons.append("High 3-day strain average")

    # Check readiness
    if current_metrics.get("readiness", 100) < 40:
        rest_needed = True
        reasons.append("Low training readiness")

    return {
        "rest_recommended": rest_needed,
        "reasons": reasons,
        "recommendation": "Take a rest day" if rest_needed else "You're good to train"
    }


def calculate_strain_goal(recovery_score):
    """
    Calculate recommended strain goal based on recovery.
    Higher recovery = can handle more strain.
    """
    if recovery_score >= 80:
        return {"min": 12, "max": 18, "label": "High intensity day"}
    elif recovery_score >= 60:
        return {"min": 8, "max": 14, "label": "Moderate training day"}
    elif recovery_score >= 40:
        return {"min": 4, "max": 10, "label": "Light activity day"}
    else:
        return {"min": 0, "max": 6, "label": "Recovery/rest day"}


def get_strain_coach_advice(current_strain, strain_goal, time_of_day_hour):
    """
    Provide coaching advice to hit strain goal.
    """
    goal_max = strain_goal["max"]
    remaining = goal_max - current_strain

    if current_strain >= goal_max:
        return "🎯 Goal achieved! Consider wrapping up for the day."
    elif remaining <= 2:
        return f"Almost there! Just {remaining:.1f} strain to go. A short walk would do it."
    elif time_of_day_hour < 12:
        return f"Good morning! Aim for {remaining:.1f} more strain today. Plan your workout accordingly."
    elif time_of_day_hour < 18:
        return f"You need {remaining:.1f} more strain. A workout or long walk this evening would hit your goal."
    else:
        return f"Evening check: {remaining:.1f} strain remaining. Consider a light evening activity if possible."


def get_metrics():
    """
    Main function: Calculate and return all fitness metrics.

    Returns dictionary with comprehensive metrics including:
    - Core: HRV, RHR, Strain, Recovery
    - Sleep: Duration, stages, efficiency, performance score
    - Advanced: Stress, Readiness, Respiratory rate, SpO2
    - Training: Strain goal, training load, overtraining alert
    - Predictions: Recovery prediction, rest day recommendation
    - And much more!
    """
    # Load merged data from Xiaomi + Coospo
    df = pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])

    # Load history for trend analysis
    history_path = "data/history.csv"
    history_df = None
    if os.path.exists(history_path):
        history_df = pd.read_csv(history_path, parse_dates=["date"])

    # Load user profile
    profile_path = "data/user_profile.json"
    user_profile = None
    if os.path.exists(profile_path):
        import json
        with open(profile_path) as f:
            user_profile = json.load(f)

    # ========================================================================
    # HRV (Heart Rate Variability) - RMSSD method
    # ========================================================================
    rr = df["rr_ms"].dropna()
    hrv = np.sqrt(np.mean(np.diff(rr)**2)) if len(rr) > 1 else 50

    # ========================================================================
    # RHR (Resting Heart Rate)
    # ========================================================================
    night = df[df["timestamp"].dt.hour.between(0, 6)]
    rhr = night["bpm"].quantile(0.05) if not night.empty else 60

    # ========================================================================
    # STEPS
    # ========================================================================
    total_steps = df["steps"].max() if "steps" in df.columns else 0

    # ========================================================================
    # STRAIN
    # ========================================================================
    excess = df["bpm"] - rhr
    hr_strain = min(21, np.sum(excess[excess > 0]) * 0.0001)
    step_strain = (total_steps / 10000) * 3
    strain = min(21, hr_strain + step_strain)

    # ========================================================================
    # RECOVERY
    # ========================================================================
    recovery = min(100, max(33, (hrv / 80) * 100 * (60 / rhr)))

    # ========================================================================
    # SLEEP METRICS
    # ========================================================================
    sleep_df = df[df["sleep_stage"] > 0]
    sleep_duration = len(sleep_df) / 60
    deep = len(sleep_df[sleep_df["sleep_stage"] == 2]) / 60
    rem = len(sleep_df[sleep_df["sleep_stage"] == 3]) / 60
    light = len(sleep_df[sleep_df["sleep_stage"] == 1]) / 60
    efficiency = (sleep_duration / 8) * 100 if sleep_duration > 0 else 0
    efficiency_str = f"{int(efficiency)}%"

    # ========================================================================
    # SLEEP PERFORMANCE SCORE (NEW!)
    # ========================================================================
    spo2_data = analyze_spo2_trends(df)
    spo2_avg = spo2_data["avg"] if spo2_data else None
    sleep_score = calculate_sleep_performance_score(
        sleep_duration, deep, rem, efficiency, hrv, spo2_avg
    )

    # ========================================================================
    # ADVANCED METRICS
    # ========================================================================
    stress = calculate_stress_score(df)
    readiness = calculate_training_readiness(hrv, rhr, recovery, efficiency_str)
    respiratory_rate = estimate_respiratory_rate(df)

    # ========================================================================
    # NEW FEATURES
    # ========================================================================

    # Strain Goal based on recovery
    strain_goal = calculate_strain_goal(recovery)

    # Recovery Prediction
    recovery_prediction = predict_recovery(history_df)

    # Overtraining Alert
    current_metrics = {"recovery": recovery, "readiness": readiness}
    overtraining = detect_overtraining(history_df, current_metrics)

    # Workout Auto-Detection
    workouts = detect_workouts(df.copy())

    # Heart Rate Zones
    age = user_profile.get("age") if user_profile else None
    hr_zones = calculate_hr_zones(df, age=age)

    # Training Load (7-day)
    training_load = calculate_training_load(history_df)

    # VO2 Max Estimation
    max_hr = df["bpm"].quantile(0.99)
    vo2_max = estimate_vo2_max(max_hr, rhr, age)

    # Personal Records
    personal_records = calculate_personal_records(history_df, current_metrics)

    # Achievements
    achievements = calculate_achievements(history_df, current_metrics)

    # Rest Day Recommendation
    rest_day = recommend_rest_day(history_df, current_metrics)

    # Strain Coach
    current_hour = datetime.now().hour
    strain_coach_advice = get_strain_coach_advice(strain, strain_goal, current_hour)

    # Hourly Strain Breakdown
    hourly_strain = calculate_hourly_strain(df.copy())

    # ========================================================================
    # RETURN ALL METRICS
    # ========================================================================
    return {
        # Core metrics
        "hrv": round(hrv, 1),
        "rhr": int(rhr),
        "strain": round(strain, 1),
        "recovery": int(recovery),

        # Sleep metrics
        "sleep_duration": f"{int(sleep_duration)}h {int((sleep_duration % 1)*60)}m",
        "sleep_duration_hours": sleep_duration,
        "deep": f"{int(deep)}h {int((deep % 1)*60)}m",
        "deep_hours": deep,
        "rem": f"{int(rem)}h {int((rem % 1)*60)}m",
        "rem_hours": rem,
        "light": f"{int(light)}h {int((light % 1)*60)}m",
        "light_hours": light,
        "efficiency": efficiency_str,
        "sleep_score": sleep_score,  # NEW!

        # Advanced metrics
        "stress": round(stress, 1),
        "readiness": readiness,
        "respiratory_rate": respiratory_rate,

        # Activity
        "steps": int(total_steps),

        # NEW FEATURES
        "spo2_data": spo2_data,
        "strain_goal": strain_goal,
        "recovery_prediction": recovery_prediction,
        "overtraining": overtraining,
        "workouts": workouts,
        "hr_zones": hr_zones,
        "training_load": training_load,
        "vo2_max": vo2_max,
        "personal_records": personal_records,
        "achievements": achievements,
        "rest_day": rest_day,
        "strain_coach": strain_coach_advice,
        "hourly_strain": hourly_strain,
    }


# For testing: run this file directly to see current metrics
if __name__ == "__main__":
    print(get_metrics())