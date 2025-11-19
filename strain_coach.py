# ============================================================================
# STRAIN COACH - Proactive training guidance
# ============================================================================
# Tells you exactly what to do to hit your strain goal
# ============================================================================

import pandas as pd
import numpy as np

# Activity database with average strain per minute
ACTIVITIES = {
    "Run (easy)": 0.25,
    "Run (moderate)": 0.35,
    "Run (hard)": 0.50,
    "Cycle (easy)": 0.20,
    "Cycle (moderate)": 0.30,
    "Cycle (hard)": 0.45,
    "Walk": 0.10,
    "Swim": 0.35,
    "Strength Training": 0.30,
    "Yoga": 0.12,
    "HIIT": 0.55,
    "Sports (basketball, soccer, etc.)": 0.40,
}

def get_strain_recommendation(current_strain, goal_strain):
    """
    Calculate what activity you need to hit your strain goal.

    Args:
        current_strain: Your current strain (0-21)
        goal_strain: Your target strain (0-21)

    Returns:
        Dictionary with recommended activities and durations
    """
    if current_strain >= goal_strain:
        return {
            "status": "goal_met",
            "message": f"🎯 Goal achieved! You're at {current_strain:.1f} strain (goal: {goal_strain}).",
            "recommendations": []
        }

    remaining = goal_strain - current_strain

    # Generate recommendations for each activity type
    recommendations = []
    for activity, strain_per_min in ACTIVITIES.items():
        minutes_needed = remaining / strain_per_min

        # Only show reasonable durations (5 min to 120 min)
        if 5 <= minutes_needed <= 120:
            recommendations.append({
                "activity": activity,
                "duration_min": int(minutes_needed),
                "strain_gain": remaining
            })

    # Sort by shortest duration first (most efficient activities)
    recommendations.sort(key=lambda x: x["duration_min"])

    return {
        "status": "in_progress",
        "current": current_strain,
        "goal": goal_strain,
        "remaining": remaining,
        "message": f"You're at {current_strain:.1f} strain. Need {remaining:.1f} more to reach {goal_strain}.",
        "recommendations": recommendations[:5]  # Top 5 most efficient
    }


def get_smart_strain_goal(recovery, recent_strains, training_goal="balanced"):
    """
    Suggest an optimal strain goal based on recovery and recent history.

    Args:
        recovery: Today's recovery percentage (0-100)
        recent_strains: List of recent strain values (last 7 days)
        training_goal: "easy", "balanced", "aggressive"

    Returns:
        Recommended strain goal
    """
    # Base goal based on recovery
    if recovery >= 67:
        base_goal = 14  # High recovery = ready to train
    elif recovery >= 33:
        base_goal = 10  # Moderate recovery = light workout
    else:
        base_goal = 7   # Low recovery = rest day

    # Adjust based on recent history
    if len(recent_strains) >= 3:
        avg_recent = np.mean(recent_strains[-7:])

        # If training goal is aggressive, push a bit harder
        if training_goal == "aggressive" and recovery > 50:
            base_goal = min(18, avg_recent + 2)
        elif training_goal == "easy":
            base_goal = min(12, avg_recent - 1)
        else:  # balanced
            base_goal = min(16, avg_recent)

    return int(base_goal)


def calculate_activity_strain_contribution(duration_min, activity_type):
    """
    Calculate how much strain a specific activity will add.

    Args:
        duration_min: Duration in minutes
        activity_type: Type of activity (must be in ACTIVITIES dict)

    Returns:
        Estimated strain points
    """
    if activity_type not in ACTIVITIES:
        return 0

    return duration_min * ACTIVITIES[activity_type]
