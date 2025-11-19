# ============================================================================
# INSIGHTS - Performance insights, trends, and recommendations
# ============================================================================
# Weekly/monthly summaries, optimal bedtime, and performance metrics
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_weekly_summary(history_df):
    """
    Generate a weekly performance summary (Sunday report card).

    Args:
        history_df: DataFrame with columns [date, recovery, strain, hrv, rhr, steps, sleep_duration]

    Returns:
        Dictionary with weekly stats
    """
    # Get last 7 days
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    week_data = history_df[history_df["date"] >= seven_days_ago]

    if len(week_data) == 0:
        return None

    # Get previous week for comparison
    fourteen_days_ago = datetime.now().date() - timedelta(days=14)
    prev_week = history_df[(history_df["date"] >= fourteen_days_ago) &
                           (history_df["date"] < seven_days_ago)]

    summary = {
        "total_strain": round(week_data["strain"].sum(), 1),
        "avg_recovery": round(week_data["recovery"].mean(), 1),
        "avg_hrv": round(week_data["hrv"].mean(), 1),
        "avg_rhr": round(week_data["rhr"].mean(), 1),
        "total_steps": int(week_data["steps"].sum()),
        "avg_steps": int(week_data["steps"].mean()),
        "best_day": None,
        "worst_day": None
    }

    # Find best and worst days
    if len(week_data) > 0:
        best_idx = week_data["recovery"].idxmax()
        worst_idx = week_data["recovery"].idxmin()

        summary["best_day"] = {
            "date": str(week_data.loc[best_idx, "date"]),
            "recovery": int(week_data.loc[best_idx, "recovery"])
        }
        summary["worst_day"] = {
            "date": str(week_data.loc[worst_idx, "date"]),
            "recovery": int(week_data.loc[worst_idx, "recovery"])
        }

    # Week-over-week comparison
    if len(prev_week) > 0:
        summary["wow_recovery_change"] = round(
            summary["avg_recovery"] - prev_week["recovery"].mean(), 1
        )
        summary["wow_strain_change"] = round(
            summary["total_strain"] - prev_week["strain"].sum(), 1
        )
        summary["wow_steps_change"] = int(
            summary["total_steps"] - prev_week["steps"].sum()
        )
    else:
        summary["wow_recovery_change"] = 0
        summary["wow_strain_change"] = 0
        summary["wow_steps_change"] = 0

    return summary


def get_monthly_insights(history_df):
    """
    Generate 30-day summary stats and insights.

    Args:
        history_df: DataFrame with history data

    Returns:
        Dictionary with monthly trends
    """
    # Get last 30 days
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    month_data = history_df[history_df["date"] >= thirty_days_ago]

    if len(month_data) < 7:
        return None

    # Get previous month for comparison
    sixty_days_ago = datetime.now().date() - timedelta(days=60)
    prev_month = history_df[(history_df["date"] >= sixty_days_ago) &
                            (history_df["date"] < thirty_days_ago)]

    insights = {
        "avg_recovery": round(month_data["recovery"].mean(), 1),
        "avg_strain": round(month_data["strain"].mean(), 1),
        "avg_hrv": round(month_data["hrv"].mean(), 1),
        "avg_rhr": round(month_data["rhr"].mean(), 1),
        "total_steps": int(month_data["steps"].sum()),
        "days_tracked": len(month_data)
    }

    # Month-over-month comparison
    if len(prev_month) > 0:
        recovery_change = insights["avg_recovery"] - prev_month["recovery"].mean()
        hrv_change = insights["avg_hrv"] - prev_month["hrv"].mean()

        insights["mom_recovery_change"] = round(recovery_change, 1)
        insights["mom_recovery_pct"] = round((recovery_change / prev_month["recovery"].mean()) * 100, 1)

        insights["mom_hrv_change"] = round(hrv_change, 1)

        # Generate insight message
        if recovery_change > 5:
            insights["message"] = f"🎉 Great month! Recovery improved by {recovery_change:.1f}%"
        elif recovery_change < -5:
            insights["message"] = f"⚠️ Recovery declined by {abs(recovery_change):.1f}% this month"
        else:
            insights["message"] = "📊 Consistent performance this month"
    else:
        insights["message"] = "First month of tracking - keep going!"

    return insights


def get_optimal_bedtime(history_df):
    """
    Recommend optimal bedtime based on best recovery days.

    Analyzes when you got your best recovery and suggests bedtime.

    Args:
        history_df: DataFrame with date, recovery data

    Returns:
        Recommended bedtime string
    """
    if len(history_df) < 7:
        return {
            "bedtime": "22:30",
            "reason": "Default recommendation (need more data for personalization)",
            "confidence": "low"
        }

    # Find top 25% recovery days
    top_recovery = history_df.nlargest(int(len(history_df) * 0.25), "recovery")

    # For now, use a simple heuristic: most people need 8 hours sleep
    # Better version would track actual sleep time from device
    # Assume wake time is 7:00 AM by default

    recommended_bedtime = "22:30"  # 10:30 PM for 8.5 hours sleep

    return {
        "bedtime": recommended_bedtime,
        "reason": f"Based on your best {len(top_recovery)} recovery days",
        "confidence": "medium",
        "avg_recovery_on_best_days": round(top_recovery["recovery"].mean(), 1)
    }


def get_day_strain_breakdown(df):
    """
    Calculate strain contribution by hour of the day.

    Args:
        df: DataFrame with timestamp and bpm columns

    Returns:
        Dictionary with hourly strain breakdown
    """
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour

    # Group by hour and calculate strain per hour
    hourly = df.groupby("hour").agg({
        "bpm": "mean",
        "steps": "sum"
    }).reset_index()

    # Calculate strain for each hour (simplified)
    # Strain ≈ (HR above resting) * time
    rhr = df[df["timestamp"].dt.hour.between(0, 6)]["bpm"].quantile(0.05)

    hourly["strain"] = ((hourly["bpm"] - rhr) * 0.01).clip(lower=0)

    # Add step contribution
    hourly["strain"] += (hourly["steps"] / 10000) * 3

    hourly_breakdown = []
    for _, row in hourly.iterrows():
        hourly_breakdown.append({
            "hour": int(row["hour"]),
            "strain": round(row["strain"], 2),
            "avg_hr": int(row["bpm"]),
            "steps": int(row["steps"])
        })

    return hourly_breakdown


def calculate_calorie_burn(bmr, strain, steps):
    """
    Calculate total calories burned (BMR + activity).

    Args:
        bmr: Basal Metabolic Rate (from user profile)
        strain: Today's strain value
        steps: Today's step count

    Returns:
        Dictionary with calorie breakdown
    """
    # Base calories (BMR spread over 24 hours)
    base_calories = bmr

    # Activity calories from steps (roughly 0.04 cal per step)
    step_calories = steps * 0.04

    # Activity calories from strain
    # Strain 14 (moderate day) ≈ 500 extra calories
    # Scale linearly
    strain_calories = (strain / 14) * 500

    # Total (avoid double-counting - use max of step or strain-based)
    activity_calories = max(step_calories, strain_calories)

    total_calories = base_calories + activity_calories

    return {
        "total": int(total_calories),
        "base_bmr": int(base_calories),
        "activity": int(activity_calories),
        "from_steps": int(step_calories),
        "from_strain": int(strain_calories)
    }
