# ============================================================================
# PULL_COOSPO.PY - Generate mock Coospo heart rate monitor data
# ============================================================================
# Simulates data from Coospo H808S chest strap during a workout.
# More accurate than wrist-based measurements for workout tracking.
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_coospo_data():
    """
    Generate realistic workout data from Coospo chest strap.
    
    Simulates a 30-minute workout with elevated heart rate.
    Chest straps are more accurate than wrist devices during exercise.
    """
    # Create data directory if it doesn't exist
    os.makedirs("data/raw", exist_ok=True)

    # ========================================================================
    # WORKOUT TIMING - 30 minutes starting at 7am
    # ========================================================================
    start = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
    times = [start + timedelta(seconds=i) for i in range(1800)]  # 30 min = 1800 seconds
    
    # ========================================================================
    # WORKOUT HEART RATE - Elevated during exercise
    # ========================================================================
    # Average 140 BPM during workout (much higher than resting ~70)
    # Variation ±20 BPM to simulate intensity changes
    # Clip to realistic range: 60-190 BPM
    bpm = np.clip(
        np.random.normal(140, 20, 1800),  # Mean=140, StdDev=20
        60,  # Min HR
        190  # Max HR
    ).astype(int)
    
    # ========================================================================
    # RR INTERVALS - Time between heartbeats
    # ========================================================================
    # Formula: 60,000 ms per minute / BPM
    # Add small natural variation
    rr = 60000 // bpm + np.random.normal(0, 10, 1800).astype(int)
    
    # ========================================================================
    # CREATE DATAFRAME
    # ========================================================================
    df = pd.DataFrame({
        "timestamp": times,
        "bpm": bpm,
        "rr_ms": rr
    })
    
    # ========================================================================
    # SAVE TO FILE
    # ========================================================================
    df.to_csv("data/raw/coospo_workout.csv", index=False)
    print("✅ Mock Coospo workout saved to data/raw/coospo_workout.csv")


# For testing: run this file directly to generate new workout data
if __name__ == "__main__":
    generate_coospo_data()