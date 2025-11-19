# ============================================================================
# ALERTS - Overtraining detection and rest day recommendations
# ============================================================================
# Warns when you're pushing too hard and suggests rest days
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def check_overtraining_risk(history_df, lookback_days=7):
    """
    Check if user is at risk of overtraining.

    Criteria for overtraining:
    - 4+ days of high strain (>14) in last 7 days
    - Average recovery < 50% in last 7 days
    - Declining HRV trend
    - Elevated resting HR trend

    Args:
        history_df: DataFrame with columns [date, strain, recovery, hrv, rhr]
        lookback_days: Number of days to analyze (default 7)

    Returns:
        Dictionary with risk assessment and recommendations
    """
    if len(history_df) < lookback_days:
        return {
            "risk_level": "unknown",
            "message": "Need more data to assess overtraining risk",
            "recommendations": []
        }

    # Get recent data
    recent = history_df.tail(lookback_days).copy()

    # Count high strain days (>14)
    high_strain_days = (recent["strain"] > 14).sum()

    # Calculate average recovery
    avg_recovery = recent["recovery"].mean()

    # Check HRV trend (declining = bad)
    hrv_trend = recent["hrv"].diff().mean()

    # Check RHR trend (increasing = bad)
    rhr_trend = recent["rhr"].diff().mean()

    # Risk scoring
    risk_score = 0

    if high_strain_days >= 4:
        risk_score += 3
    elif high_strain_days >= 2:
        risk_score += 1

    if avg_recovery < 50:
        risk_score += 3
    elif avg_recovery < 60:
        risk_score += 1

    if hrv_trend < -2:  # HRV declining
        risk_score += 2

    if rhr_trend > 2:  # RHR increasing
        risk_score += 2

    # Determine risk level
    if risk_score >= 7:
        risk_level = "high"
        message = "⚠️ HIGH OVERTRAINING RISK - You've had high strain with poor recovery"
        recommendations = [
            "Take 2-3 rest days",
            "Focus on sleep (aim for 8+ hours)",
            "Stay hydrated",
            "Consider light stretching or yoga only",
            "Consult a professional if fatigue persists"
        ]
    elif risk_score >= 4:
        risk_level = "moderate"
        message = "⚠️ MODERATE RISK - Your body needs more recovery time"
        recommendations = [
            "Take 1 rest day soon",
            "Reduce training intensity this week",
            "Prioritize sleep quality",
            "Monitor your recovery closely"
        ]
    else:
        risk_level = "low"
        message = "✅ Low overtraining risk - Keep balancing training and recovery"
        recommendations = [
            "Continue current training load",
            "Maintain good sleep habits",
            "Listen to your body"
        ]

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "message": message,
        "recommendations": recommendations,
        "stats": {
            "high_strain_days": high_strain_days,
            "avg_recovery": round(avg_recovery, 1),
            "hrv_trend": "declining" if hrv_trend < 0 else "stable/improving",
            "rhr_trend": "increasing" if rhr_trend > 0 else "stable/decreasing"
        }
    }


def should_rest_today(recovery, strain_yesterday, recent_recoveries):
    """
    Simple yes/no: Should you rest today?

    Args:
        recovery: Today's recovery percentage
        strain_yesterday: Yesterday's strain
        recent_recoveries: List of last 3 days' recovery scores

    Returns:
        Dictionary with recommendation
    """
    rest_score = 0

    # Low recovery today
    if recovery < 40:
        rest_score += 3
    elif recovery < 60:
        rest_score += 1

    # High strain yesterday
    if strain_yesterday > 16:
        rest_score += 2

    # Declining recovery trend
    if len(recent_recoveries) >= 3:
        if all(recent_recoveries[i] > recent_recoveries[i+1]
               for i in range(len(recent_recoveries)-1)):
            rest_score += 2

    # Decision
    if rest_score >= 5:
        return {
            "should_rest": True,
            "urgency": "high",
            "message": "🛑 REST DAY - Your body needs recovery",
            "reason": f"Recovery: {recovery}%, Recent strain: {strain_yesterday}",
            "suggestion": "Focus on sleep, hydration, and light stretching only"
        }
    elif rest_score >= 3:
        return {
            "should_rest": True,
            "urgency": "moderate",
            "message": "😴 REST DAY RECOMMENDED - Light activity only",
            "reason": f"Recovery: {recovery}%, showing signs of fatigue",
            "suggestion": "Easy walk or yoga is fine, but avoid intense training"
        }
    else:
        return {
            "should_rest": False,
            "urgency": "none",
            "message": "💪 You can train today based on recovery",
            "reason": f"Recovery: {recovery}%, body is ready",
            "suggestion": "Train according to your plan, but listen to your body"
        }


def get_recovery_forecast(recent_strains, recent_recoveries):
    """
    Predict tomorrow's recovery based on today's strain.

    Simple model: Higher strain today = lower recovery tomorrow

    Args:
        recent_strains: List of recent strain values (last 7-14 days)
        recent_recoveries: List of recent recovery values (last 7-14 days)

    Returns:
        Predicted recovery percentage
    """
    if len(recent_strains) < 3 or len(recent_recoveries) < 3:
        return None

    # Simple correlation: for every 2 points of strain, recovery drops ~3%
    # (This is a simplification - real WHOOP uses ML)

    today_strain = recent_strains[-1]
    avg_strain = np.mean(recent_strains)

    # Calculate typical recovery
    avg_recovery = np.mean(recent_recoveries)

    # Adjust based on today's strain vs average
    strain_diff = today_strain - avg_strain

    # Higher strain = lower recovery tomorrow
    predicted_recovery = avg_recovery - (strain_diff * 1.5)

    # Clamp to 0-100
    predicted_recovery = max(0, min(100, predicted_recovery))

    return int(predicted_recovery)
