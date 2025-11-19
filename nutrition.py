# ============================================================================
# NUTRITION - Hydration and nutrition tracking
# ============================================================================
# Log water and calories with simple interface
# ============================================================================

import json
import os
from datetime import datetime

def get_water_goal(strain):
    """
    Calculate water goal based on strain.

    Rule: 8oz per strain point (WHOOP's recommendation)

    Args:
        strain: Today's strain value (0-21)

    Returns:
        Water goal in oz and ml
    """
    oz = max(64, strain * 8)  # Minimum 64oz per day

    ml = int(oz * 29.5735)  # Convert to ml

    return {
        "oz": int(oz),
        "ml": ml,
        "glasses": round(oz / 8, 1)  # 8oz per glass
    }


def load_nutrition_log():
    """
    Load nutrition log from file.

    Returns:
        Dictionary with dates as keys
    """
    log_file = "data/nutrition_log.json"

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return json.load(f)
    return {}


def save_nutrition_log(log):
    """
    Save nutrition log to file.

    Args:
        log: Dictionary with nutrition data
    """
    os.makedirs("data", exist_ok=True)
    with open("data/nutrition_log.json", "w") as f:
        json.dump(log, f, indent=2)


def log_water(oz, date=None):
    """
    Log water intake for a specific date.

    Args:
        oz: Ounces of water
        date: Date string "YYYY-MM-DD" (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    log = load_nutrition_log()

    if date not in log:
        log[date] = {"water_oz": 0, "calories": 0, "notes": []}

    log[date]["water_oz"] += oz

    save_nutrition_log(log)


def log_calories(calories, meal_name="", date=None):
    """
    Log calorie intake for a specific date.

    Args:
        calories: Calories consumed
        meal_name: Optional meal description
        date: Date string "YYYY-MM-DD" (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    log = load_nutrition_log()

    if date not in log:
        log[date] = {"water_oz": 0, "calories": 0, "notes": []}

    log[date]["calories"] += calories

    if meal_name:
        log[date]["notes"].append({
            "time": datetime.now().strftime("%H:%M"),
            "meal": meal_name,
            "calories": calories
        })

    save_nutrition_log(log)


def get_nutrition_summary(date=None):
    """
    Get nutrition summary for a specific date.

    Args:
        date: Date string "YYYY-MM-DD" (defaults to today)

    Returns:
        Dictionary with nutrition stats
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    log = load_nutrition_log()

    if date not in log:
        return {
            "water_oz": 0,
            "water_ml": 0,
            "calories": 0,
            "meals": []
        }

    day_data = log[date]

    return {
        "water_oz": day_data.get("water_oz", 0),
        "water_ml": int(day_data.get("water_oz", 0) * 29.5735),
        "calories": day_data.get("calories", 0),
        "meals": day_data.get("notes", [])
    }


def reset_day(date=None):
    """
    Reset nutrition tracking for a specific date.

    Args:
        date: Date string "YYYY-MM-DD" (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    log = load_nutrition_log()

    if date in log:
        log[date] = {"water_oz": 0, "calories": 0, "notes": []}
        save_nutrition_log(log)
