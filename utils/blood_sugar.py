"""
============================================================================
BLOOD_SUGAR.PY - Blood glucose tracking and insulin sensitivity analysis
============================================================================
Functions for:
- Blood sugar tracking (pre/post meal)
- Insulin sensitivity assessment
- Glucose spike analysis
- Health status evaluation
============================================================================
"""

import os
import pandas as pd
import json
from datetime import datetime


# ============================================================================
# BLOOD SUGAR ASSESSMENT FUNCTIONS
# ============================================================================

def assess_fasting_glucose(glucose_mg_dl):
    """
    Assess fasting blood glucose level (should be measured after 8+ hours of fasting).

    Parameters:
    -----------
    glucose_mg_dl : float
        Fasting glucose in mg/dL

    Returns:
    --------
    dict : Assessment with status, category, and advice

    Reference Ranges (American Diabetes Association):
    -------------------------------------------------
    - Normal: < 100 mg/dL
    - Prediabetes: 100-125 mg/dL
    - Diabetes: ≥ 126 mg/dL
    """

    if glucose_mg_dl < 70:
        return {
            "status": "Low (Hypoglycemia)",
            "color": "blue",
            "emoji": "⚠️",
            "category": "concerning",
            "advice": "Your fasting glucose is LOW. Eat something immediately and consult a doctor if symptoms persist."
        }
    elif glucose_mg_dl < 100:
        return {
            "status": "Normal",
            "color": "green",
            "emoji": "✅",
            "category": "healthy",
            "advice": "Excellent! Your fasting glucose is in the healthy range."
        }
    elif glucose_mg_dl < 126:
        return {
            "status": "Prediabetes",
            "color": "orange",
            "emoji": "⚠️",
            "category": "warning",
            "advice": "Your fasting glucose indicates PREDIABETES. Consider lifestyle changes: reduce sugar/refined carbs, exercise regularly, and consult a doctor."
        }
    else:
        return {
            "status": "Diabetes Range",
            "color": "red",
            "emoji": "🔴",
            "category": "concerning",
            "advice": "Your fasting glucose is in the DIABETES range. Please consult a healthcare provider immediately for proper diagnosis and treatment."
        }


def assess_postprandial_glucose(glucose_mg_dl, hours_after_meal):
    """
    Assess post-meal (postprandial) blood glucose level.

    Parameters:
    -----------
    glucose_mg_dl : float
        Post-meal glucose in mg/dL
    hours_after_meal : float
        Time elapsed since start of meal (typically 1-2 hours)

    Returns:
    --------
    dict : Assessment with status, category, and advice

    Reference Ranges (1-2 hours after eating):
    ------------------------------------------
    - Normal: < 140 mg/dL
    - Prediabetes: 140-199 mg/dL
    - Diabetes: ≥ 200 mg/dL
    """

    if hours_after_meal < 1.0:
        advice_note = "⚠️ Note: Ideally measure 1-2 hours after meal start for accurate assessment."
    else:
        advice_note = ""

    if glucose_mg_dl < 140:
        return {
            "status": "Normal",
            "color": "green",
            "emoji": "✅",
            "category": "healthy",
            "advice": f"Great! Your post-meal glucose is healthy. {advice_note}"
        }
    elif glucose_mg_dl < 200:
        return {
            "status": "Elevated (Prediabetes range)",
            "color": "orange",
            "emoji": "⚠️",
            "category": "warning",
            "advice": f"Your post-meal glucose is ELEVATED. This may indicate insulin resistance. Consider reducing carb portions and consulting a doctor. {advice_note}"
        }
    else:
        return {
            "status": "Very High (Diabetes range)",
            "color": "red",
            "emoji": "🔴",
            "category": "concerning",
            "advice": f"Your post-meal glucose is VERY HIGH. Please consult a healthcare provider immediately. {advice_note}"
        }


def calculate_glucose_spike(fasting_mg_dl, postprandial_mg_dl):
    """
    Calculate the glucose spike from a meal.

    Parameters:
    -----------
    fasting_mg_dl : float
        Pre-meal (fasting) glucose
    postprandial_mg_dl : float
        Post-meal glucose

    Returns:
    --------
    dict : Spike information with assessment

    Healthy Spike:
    --------------
    - Should rise < 30-40 mg/dL from baseline
    - Larger spikes indicate poor glucose control
    """

    spike = postprandial_mg_dl - fasting_mg_dl

    if spike < 0:
        return {
            "spike_mg_dl": spike,
            "status": "Decreased",
            "color": "blue",
            "emoji": "⬇️",
            "assessment": "Your glucose decreased after eating. This is unusual - ensure you measured correctly."
        }
    elif spike < 30:
        return {
            "spike_mg_dl": spike,
            "status": "Excellent",
            "color": "green",
            "emoji": "✅",
            "assessment": "Excellent glucose control! Your body handled this meal very well."
        }
    elif spike < 50:
        return {
            "spike_mg_dl": spike,
            "status": "Good",
            "color": "lightgreen",
            "emoji": "👍",
            "assessment": "Good glucose response. Your insulin sensitivity is healthy."
        }
    elif spike < 70:
        return {
            "spike_mg_dl": spike,
            "status": "Moderate",
            "color": "orange",
            "emoji": "⚠️",
            "assessment": "Moderate spike. Consider reducing refined carbs/sugar in this meal."
        }
    else:
        return {
            "spike_mg_dl": spike,
            "status": "High",
            "color": "red",
            "emoji": "🔴",
            "assessment": "Large glucose spike! This indicates poor glucose control. Reduce carbs and consult a doctor."
        }


def assess_insulin_sensitivity(fasting_mg_dl, postprandial_mg_dl, hours_after_meal):
    """
    Comprehensive insulin sensitivity assessment based on glucose measurements.

    Parameters:
    -----------
    fasting_mg_dl : float
        Pre-meal glucose
    postprandial_mg_dl : float
        Post-meal glucose
    hours_after_meal : float
        Time elapsed since meal start

    Returns:
    --------
    dict : Comprehensive assessment with:
        - Overall health status
        - Insulin sensitivity score (0-100)
        - Detailed recommendations
        - Risk category
    """

    # Assess individual components
    fasting_assessment = assess_fasting_glucose(fasting_mg_dl)
    postprandial_assessment = assess_postprandial_glucose(postprandial_mg_dl, hours_after_meal)
    spike_assessment = calculate_glucose_spike(fasting_mg_dl, postprandial_mg_dl)

    # Calculate insulin sensitivity score (0-100)
    # Based on:
    # 1. Fasting glucose (40% weight)
    # 2. Post-meal glucose (30% weight)
    # 3. Glucose spike (30% weight)

    # Fasting score (ideal < 90, concerning > 125)
    fasting_score = max(0, min(100, 100 - ((fasting_mg_dl - 85) * 2)))

    # Postprandial score (ideal < 120, concerning > 180)
    postprandial_score = max(0, min(100, 100 - ((postprandial_mg_dl - 115) * 1.5)))

    # Spike score (ideal < 30, concerning > 60)
    spike_mg_dl = spike_assessment["spike_mg_dl"]
    spike_score = max(0, min(100, 100 - ((spike_mg_dl - 25) * 2)))

    # Weighted average
    sensitivity_score = int(
        fasting_score * 0.4 +
        postprandial_score * 0.3 +
        spike_score * 0.3
    )

    # Determine overall status
    if sensitivity_score >= 80:
        overall_status = "Excellent Insulin Sensitivity"
        overall_emoji = "🟢"
        overall_color = "green"
        risk_level = "Low Risk"
        recommendation = (
            "Your glucose control is excellent! Your body is efficiently managing blood sugar. "
            "Keep up your healthy lifestyle with balanced nutrition and regular exercise."
        )
    elif sensitivity_score >= 60:
        overall_status = "Good Insulin Sensitivity"
        overall_emoji = "🟡"
        overall_color = "lightgreen"
        risk_level = "Low-Moderate Risk"
        recommendation = (
            "Your insulin sensitivity is generally good, but there's room for improvement. "
            "Focus on: reducing refined carbs, increasing fiber intake, regular exercise (especially strength training), "
            "and maintaining healthy body weight."
        )
    elif sensitivity_score >= 40:
        overall_status = "Reduced Insulin Sensitivity"
        overall_emoji = "🟠"
        overall_color = "orange"
        risk_level = "Moderate-High Risk"
        recommendation = (
            "Your results suggest REDUCED insulin sensitivity (insulin resistance). "
            "This is a warning sign for prediabetes/type 2 diabetes. "
            "STRONGLY RECOMMENDED: Consult a doctor, reduce sugar/refined carbs significantly, "
            "exercise 150+ min/week, prioritize sleep, and manage stress."
        )
    else:
        overall_status = "Poor Insulin Sensitivity (Insulin Resistant)"
        overall_emoji = "🔴"
        overall_color = "red"
        risk_level = "High Risk"
        recommendation = (
            "Your results indicate POOR insulin sensitivity (significant insulin resistance). "
            "This requires immediate attention. PLEASE CONSULT A HEALTHCARE PROVIDER for proper evaluation and treatment. "
            "Lifestyle changes needed: eliminate refined sugar, focus on whole foods, "
            "daily exercise, weight management, and potential medical intervention."
        )

    return {
        "sensitivity_score": sensitivity_score,
        "overall_status": overall_status,
        "overall_emoji": overall_emoji,
        "overall_color": overall_color,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "fasting_assessment": fasting_assessment,
        "postprandial_assessment": postprandial_assessment,
        "spike_assessment": spike_assessment
    }


# ============================================================================
# DATA STORAGE FUNCTIONS
# ============================================================================

def save_glucose_measurement(fasting_mg_dl, postprandial_mg_dl, hours_after_meal, meal_type, notes=""):
    """
    Save a glucose measurement to history.

    Parameters:
    -----------
    fasting_mg_dl : float
        Pre-meal glucose
    postprandial_mg_dl : float
        Post-meal glucose
    hours_after_meal : float
        Time between measurements
    meal_type : str
        Type of meal (breakfast, lunch, dinner, snack)
    notes : str, optional
        Additional notes about the meal

    Returns:
    --------
    None
    """
    os.makedirs("data", exist_ok=True)
    filepath = "data/glucose_history.csv"

    # Get assessment
    assessment = assess_insulin_sensitivity(fasting_mg_dl, postprandial_mg_dl, hours_after_meal)

    # Create new entry
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "meal_type": meal_type,
        "fasting_mg_dl": fasting_mg_dl,
        "postprandial_mg_dl": postprandial_mg_dl,
        "hours_after_meal": hours_after_meal,
        "spike_mg_dl": assessment["spike_assessment"]["spike_mg_dl"],
        "sensitivity_score": assessment["sensitivity_score"],
        "notes": notes
    }

    # Append to CSV
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    else:
        df = pd.DataFrame([new_entry])

    df.to_csv(filepath, index=False)


def load_glucose_history():
    """
    Load glucose measurement history.

    Returns:
    --------
    pd.DataFrame : History of glucose measurements
    """
    filepath = "data/glucose_history.csv"
    if os.path.exists(filepath):
        return pd.read_csv(filepath, parse_dates=["timestamp"])
    return pd.DataFrame()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test scenarios
    print("=== BLOOD SUGAR ASSESSMENT TESTS ===\n")

    # Test 1: Healthy person
    print("Test 1: Healthy Person")
    print("-" * 50)
    assessment = assess_insulin_sensitivity(
        fasting_mg_dl=88,
        postprandial_mg_dl=115,
        hours_after_meal=1.5
    )
    print(f"Sensitivity Score: {assessment['sensitivity_score']}/100")
    print(f"Status: {assessment['overall_emoji']} {assessment['overall_status']}")
    print(f"Risk: {assessment['risk_level']}")
    print(f"Spike: {assessment['spike_assessment']['spike_mg_dl']} mg/dL")
    print()

    # Test 2: Prediabetic
    print("Test 2: Prediabetic")
    print("-" * 50)
    assessment = assess_insulin_sensitivity(
        fasting_mg_dl=110,
        postprandial_mg_dl=165,
        hours_after_meal=1.0
    )
    print(f"Sensitivity Score: {assessment['sensitivity_score']}/100")
    print(f"Status: {assessment['overall_emoji']} {assessment['overall_status']}")
    print(f"Risk: {assessment['risk_level']}")
    print(f"Spike: {assessment['spike_assessment']['spike_mg_dl']} mg/dL")
    print()

    # Test 3: Diabetic range
    print("Test 3: Diabetic Range")
    print("-" * 50)
    assessment = assess_insulin_sensitivity(
        fasting_mg_dl=135,
        postprandial_mg_dl=220,
        hours_after_meal=1.5
    )
    print(f"Sensitivity Score: {assessment['sensitivity_score']}/100")
    print(f"Status: {assessment['overall_emoji']} {assessment['overall_status']}")
    print(f"Risk: {assessment['risk_level']}")
    print(f"Spike: {assessment['spike_assessment']['spike_mg_dl']} mg/dL")
