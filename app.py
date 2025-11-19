# ============================================================================
# CHEAP WHOOP - Advanced Fitness & Health Tracking App
# ============================================================================
# A low-cost alternative to WHOOP using affordable hardware (Xiaomi + Coospo)
#
# Features:
# - Heart rate monitoring with personalized max HR zones
# - HRV, sleep tracking, and recovery analysis
# - Blood sugar tracking and insulin sensitivity assessment
# - BMI, BMR, TDEE calculations
# - Step counting and activity tracking
# - Training readiness recommendations
# ============================================================================

import streamlit as st
import plotly.graph_objects as go
from metrics import get_metrics
import os
from datetime import datetime, timedelta
import pandas as pd
from pull_xiaomi import generate_xiaomi_data
from pull_coospo import generate_coospo_data
from merge import merge_data

# Import our new utility modules
from utils.health_calculations import (
    calculate_max_heart_rate, calculate_heart_rate_zones, get_current_zone,
    calculate_bmi, get_bmi_category, calculate_bmr, calculate_tdee,
    cm_to_inches, inches_to_cm, kg_to_lbs, lbs_to_kg
)
from utils.blood_sugar import (
    assess_insulin_sensitivity, save_glucose_measurement, load_glucose_history,
    assess_fasting_glucose, assess_postprandial_glucose
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=60)
def load_merged_data():
    """
    Load merged heart rate data from Xiaomi and Coospo devices.
    Cached for 60 seconds to improve performance.
    """
    try:
        return pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_history():
    """
    Load historical tracking data (recovery, strain, HRV, etc.).
    Cached for 5 minutes to improve performance.
    """
    history_path = "data/history.csv"
    if os.path.exists(history_path):
        df = pd.read_csv(history_path)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    return pd.DataFrame()

def load_user_profile():
    """Load user profile data (age, weight, height, sex, activity level)"""
    profile_path = "data/user_profile.json"
    if os.path.exists(profile_path):
        import json
        with open(profile_path) as f:
            return json.load(f)
    return None

def save_user_profile(profile):
    """Save user profile data to JSON file"""
    import json
    os.makedirs("data", exist_ok=True)
    with open("data/user_profile.json", "w") as f:
        json.dump(profile, f, indent=2)

# ============================================================================
# PAGE SETUP
# ============================================================================

st.set_page_config(page_title="Cheap WHOOP", layout="centered", page_icon="💪")
st.title("💪 Cheap WHOOP - Advanced Health Tracker")
st.caption("No $30/month subscription. Just $75 hardware + smart analytics.")

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "❤️ Heart Data",
    "😴 Sleep",
    "📈 History",
    "⚖️ BMI & Metabolism",
    "🩸 Blood Sugar"
])

# ============================================================================
# TAB 1: HEART DATA & RECOVERY
# ============================================================================

with tab1:
    # Load current metrics
    m = get_metrics()
    
    # Display status banner based on recovery score
    if m["recovery"] > 66:
        st.success("🟢 **Ready to Train** - Your body is recovered!")
    elif m["recovery"] > 33:
        st.warning("🟡 **Moderate Recovery** - Light workout recommended")
    else:
        st.error("🔴 **Rest Day** - Prioritize recovery today")
    
    # ========================================================================
    # DATA REFRESH BUTTON
    # ========================================================================
    if st.button("🔄 Refresh Data"):
        with st.spinner("Refreshing data..."):
            # Generate new mock data from devices
            generate_xiaomi_data()
            generate_coospo_data()
            merge_data()

            # Reload merged data
            daily_df = pd.read_csv("data/merged/daily_merged.csv")
            m = get_metrics()

            # Get current weight from profile
            profile = load_user_profile()
            current_weight = profile["weight_kg"] if profile else None

            # Create new history entry for today
            history_path = "data/history.csv"
            history_df = pd.DataFrame({
                "date": [datetime.now().strftime("%Y-%m-%d")],
                "recovery": [m["recovery"]],
                "strain": [m["strain"]],
                "rhr": [m["rhr"]],
                "hrv": [m["hrv"]],
                "stress": [m["stress"]],
                "readiness": [m["readiness"]],
                "steps": [m["steps"]],
                "weight_kg": [current_weight]
            })

            # Append to existing history or create new file
            if os.path.exists(history_path):
                old_history = pd.read_csv(history_path)
                combined = pd.concat([old_history, history_df])
                # Remove duplicate dates, keeping most recent
                combined["date"] = pd.to_datetime(combined["date"]).dt.date
                combined = combined.drop_duplicates(subset="date", keep="last")
            else:
                combined = history_df

            # Save updated history
            combined.to_csv(history_path, index=False)
            
            # Clear cached data to show new values
            st.cache_data.clear()
            
        st.success("Data updated and added to history!")
        st.rerun()

    # ========================================================================
    # MAIN GAUGES: STRAIN & RECOVERY
    # ========================================================================
    col1, col2 = st.columns(2)

    # STRAIN GAUGE
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=m["strain"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "<b>Strain</b>"},
            gauge={
                'axis': {'range': [0, 21]},
                'bar': {'color': "cyan"},
                'steps': [
                    {'range': [0, 7], 'color': "lightgray"},
                    {'range': [7, 14], 'color': "yellow"},
                    {'range': [14, 21], 'color': "red"}
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("What is Strain?"):
            st.write("""
            **Strain (0–21): Total cardiovascular load for the day**
            
            - Combines heart rate elevation + step count
            - 10,000 steps ≈ 3 strain points
            - NOT the same as stress (mental tension)
            
            **Scale:**
            - 0-7: Light day (resting)
            - 7-14: Moderate activity
            - 14-21: Hard training day
            """)

    # RECOVERY GAUGE
    with col2:
        color = "green" if m["recovery"] > 66 else "orange" if m["recovery"] > 33 else "red"
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=m["recovery"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "<b>Recovery</b>"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("What is Recovery?"):
            st.write("""
            **Recovery: How well you recovered overnight**
            
            Based on HRV and Resting Heart Rate measured during sleep.
            
            **Scale:**
            - 🟢 67-100: Great recovery
            - 🟡 34-66: Moderate recovery
            - 🔴 0-33: Poor recovery (rest day)
            """)

    # ========================================================================
    # HRV & RESTING HEART RATE
    # ========================================================================
    col_hrv, col_rhr = st.columns(2)
    with col_hrv:
        st.metric("HRV", f"{m['hrv']} ms", help="Higher HRV = better recovery")
    with col_rhr:
        st.metric("Resting HR", f"{m['rhr']} BPM", help="Lower RHR = better fitness")

    # ========================================================================
    # MAX HEART RATE & TRAINING ZONES (Personalized)
    # ========================================================================
    st.divider()
    st.subheader("🎯 Your Personalized Training Zones")

    # Get user profile for personalized max HR
    profile = load_user_profile()

    if profile:
        # Calculate personalized max HR using weight-adjusted formula
        max_hr = calculate_max_heart_rate(
            profile["age"],
            profile["weight_kg"],
            method="inbar"  # Weight-adjusted formula
        )

        # Show max HR and current HR comparison
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max Heart Rate", f"{max_hr} BPM",
                     help=f"Personalized using age ({profile['age']}) and weight ({profile['weight_kg']:.1f} kg)")

        with col2:
            # Get current HR from recent data
            df = load_merged_data()
            if not df.empty:
                current_hr = int(df["bpm"].iloc[-1])
                hr_percentage = (current_hr / max_hr) * 100
                st.metric("Current HR", f"{current_hr} BPM",
                         delta=f"{hr_percentage:.0f}% of max")
            else:
                st.metric("Current HR", "N/A", help="No data available")

        with col3:
            st.metric("Resting HR", f"{m['rhr']} BPM",
                     delta=f"{((m['rhr'] / max_hr) * 100):.0f}% of max")

        # Display heart rate zones
        zones = calculate_heart_rate_zones(max_hr)

        with st.expander("📊 View Your Training Zones"):
            st.write(f"**Based on your max HR of {max_hr} BPM:**")
            st.write("")

            for zone_key, zone_info in zones.items():
                min_hr, max_zone_hr = zone_info["range"]
                zone_name = zone_info["name"]
                zone_desc = zone_info["description"]
                zone_benefit = zone_info["benefit"]

                # Color-code zones
                if "Recovery" in zone_name:
                    color = "🟦"
                elif "Fat Burn" in zone_name:
                    color = "🟩"
                elif "Aerobic" in zone_name:
                    color = "🟨"
                elif "Threshold" in zone_name:
                    color = "🟧"
                else:
                    color = "🟥"

                st.write(f"{color} **{zone_name}**: {min_hr}-{max_zone_hr} BPM")
                st.caption(f"   ➜ {zone_desc} — *{zone_benefit}*")
                st.write("")
    else:
        st.info("💡 Complete your profile in the **BMI & Metabolism** tab to see personalized training zones!")

    # ========================================================================
    # STEP TRACKING SECTION
    # ========================================================================
    st.divider()
    st.subheader("🚶 Daily Activity")
    
    col1, col2, col3 = st.columns(3)
    
    # Steps with progress bar
    with col1:
        step_goal = 10000
        step_progress = (m["steps"] / step_goal) * 100
        st.metric("Steps Today", f"{m['steps']:,}", help=f"Goal: {step_goal:,} steps")
        st.progress(min(1.0, step_progress / 100))
    
    # Distance calculation (2000 steps ≈ 1 mile)
    with col2:
        miles = m["steps"] / 2000
        st.metric("Distance", f"{miles:.1f} mi", help="Estimated from steps")
    
    # Active calories from steps (0.04 cal per step)
    with col3:
        step_calories = m["steps"] * 0.04
        st.metric("Active Calories", f"{int(step_calories)} cal", help="From steps only")
    
    with st.expander("❓ How are steps used in Strain?"):
        st.write("""
        **Steps contribute to overall Strain:**
        
        - 10,000 steps ≈ 3 strain points
        - Combined with heart rate data
        
        **Example:**
        - Hard workout (HR strain: 12) + 8,000 steps (2.4) = **Total: 14.4**
        """)
    
    # ========================================================================
    # ADVANCED METRICS: STRESS, READINESS, BREATHING
    # ========================================================================
    st.divider()
    st.subheader("🧠 Advanced Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    # STRESS LEVEL
    with col1:
        stress_color = "🟢" if m["stress"] < 4 else "🟡" if m["stress"] < 7 else "🔴"
        st.metric("Stress Level", f"{stress_color} {m['stress']}/10", 
                  help="Based on HR and HRV patterns")
        
        with st.expander("❓ What is Stress?"):
            st.write("""
            **Stress = nervous system tension RIGHT NOW**
            
            NOT the same as Strain (physical work).
            
            **Scale:**
            - 🟢 0-3: Relaxed, calm
            - 🟡 4-6: Normal daily stress
            - 🔴 7-10: High stress (overtraining/anxiety)
            """)
    
    # TRAINING READINESS
    with col2:
        readiness_emoji = "💪" if m["readiness"] > 70 else "😐" if m["readiness"] > 40 else "😴"
        st.metric("Training Readiness", f"{readiness_emoji} {m['readiness']}%",
                  help="Should you train hard today?")
        
        with st.expander("❓ What is Readiness?"):
            st.write("""
            **Should you work out hard TODAY?**
            
            Combines:
            - 40% Recovery
            - 25% HRV
            - 20% Sleep quality
            - 15% Resting HR
            
            **Scale:**
            - 💪 70-100: GO HARD
            - 😐 40-69: Light workout
            - 😴 0-39: REST DAY
            """)
    
    # RESPIRATORY RATE
    with col3:
        if m["respiratory_rate"]:
            resp_status = "Normal" if 12 <= m["respiratory_rate"] <= 20 else "Check"
            st.metric("Breathing Rate", f"{m['respiratory_rate']} /min",
                      delta=resp_status, help="Normal: 12-20/min")
            
            with st.expander("❓ What is Breathing Rate?"):
                st.write("""
                **Breaths per minute at rest**
                
                Estimated from heart rate variability patterns.
                
                **Normal:** 12-20 breaths/min
                - 8-12: Very relaxed
                - 20-30: Elevated (stress/exercise)
                - 30+: Very high (check if at rest)
                """)
        else:
            st.metric("Breathing Rate", "N/A", help="Need more data")
    
    # Quick comparison guide
    with st.expander("🤔 Strain vs Stress? Recovery vs Readiness?"):
        st.write("""
        | Metric | Measures | Question |
        |--------|----------|----------|
        | **Strain** | Physical work | "How hard did I work?" |
        | **Stress** | Nervous tension | "How tense is my body?" |
        | **Recovery** | Sleep quality | "Did I recover overnight?" |
        | **Readiness** | Training decision | "Should I work out?" |
        """)
    
    # ========================================================================
    # BASELINE COMPARISON
    # ========================================================================
    st.divider()
    st.subheader("📊 Today vs. Your Baseline")
    
    history_df = load_history()
    if len(history_df) >= 7:
        # Calculate 30-day averages
        recent = history_df.tail(30)
        avg_hrv = recent["hrv"].mean()
        avg_rhr = recent["rhr"].mean()
        
        col1, col2 = st.columns(2)
        with col1:
            diff_hrv = m["hrv"] - avg_hrv
            st.metric("HRV vs Baseline", f"{m['hrv']} ms", delta=f"{diff_hrv:+.1f} ms")
        with col2:
            diff_rhr = m["rhr"] - avg_rhr
            st.metric("Resting HR vs Baseline", f"{m['rhr']} BPM", 
                      delta=f"{diff_rhr:+.1f} BPM", delta_color="inverse")
    else:
        st.info("📅 Track for 7+ days to see your baseline comparison")
    
    # ========================================================================
    # LIVE HEART RATE CHART
    # ========================================================================
    st.divider()
    st.subheader("📡 Live View - Last Hour")
    
    df = load_merged_data()
    
    if not df.empty:
        # Filter to last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        last_hour = df[df["timestamp"] > one_hour_ago]
        
        if not last_hour.empty:
            # Create smoothed line chart
            last_hour_sorted = last_hour.sort_values("timestamp")
            last_hour_sorted["bpm_smooth"] = last_hour_sorted["bpm"].rolling(window=8, center=True).mean()
            
            fig = go.Figure()
            
            # Raw data (faint background)
            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm"],
                mode="lines",
                line=dict(color="lightgray", width=1),
                opacity=0.3,
                showlegend=False
            ))
            
            # Smoothed heart rate
            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm_smooth"],
                mode="lines",
                name="Heart Rate",
                line=dict(color="red", width=3),
                fill="tozeroy",
                fillcolor="rgba(255, 0, 0, 0.1)"
            ))
            
            # Resting HR reference line
            fig.add_hline(
                y=m["rhr"], 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Resting HR ({m['rhr']} BPM)"
            )
            
            fig.update_layout(
                height=300,
                margin=dict(t=10, b=0, l=0, r=0),
                xaxis_title="Time",
                yaxis_title="BPM",
                showlegend=False,
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Current stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current HR", f"{last_hour['bpm'].iloc[-1]} BPM")
            with col2:
                st.metric("Avg (Last Hour)", f"{int(last_hour['bpm'].mean())} BPM")
            with col3:
                st.metric("Max (Last Hour)", f"{last_hour['bpm'].max()} BPM")
        else:
            st.info("No data in the last hour. Click refresh to generate new data!")
    else:
        st.info("No data available. Click refresh to start tracking!")

# ============================================================================
# TAB 2: SLEEP ANALYSIS
# ============================================================================

with tab2:
    st.subheader("😴 Sleep Analysis")
    m = get_metrics()

    # Display sleep metrics in table format
    sleep_data = {
        "Duration": m["sleep_duration"],
        "Deep": m["deep"],
        "REM": m["rem"],
        "Light": m["light"],
        "Efficiency": m["efficiency"]
    }

    st.table(sleep_data)

    with st.expander("What is Sleep Analysis?"):
        st.write("""
        Sleep stages are estimated using:
        - HRV dips (indicates deep sleep)
        - Heart rate trends (lower during deep sleep)
        - Movement patterns from wearable
        """)

# ============================================================================
# TAB 3: HISTORY TRENDS
# ============================================================================

with tab3:
    st.subheader("📈 History Trends")
    
    history_df = load_history()
    
    if not history_df.empty:
        # Group by date to handle any duplicates
        daily = history_df.groupby("date", as_index=False).mean()

        # Time range filter
        filter_range = st.selectbox(
            "Time Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
        )

        if filter_range != "All Time":
            days = int(filter_range.split()[1])
            cutoff = datetime.now().date() - pd.Timedelta(days=days)
            daily = daily[daily["date"] >= cutoff]

        # Metric selector
        metric = st.selectbox(
            "Select Metric to View",
            ["recovery", "strain", "rhr", "hrv", "stress", "readiness", "steps", "weight_kg"],
            index=0
        )

        daily["date_str"] = daily["date"].astype(str)

        # Special handling for weight (show both units)
        if metric == "weight_kg":
            if "weight_kg" not in daily.columns:
                st.warning("⚠️ Weight tracking not available yet.")
                st.info("Go to **BMI & Metabolism** tab → Save profile → Refresh data")
            else:
                daily_with_weight = daily[daily["weight_kg"].notna()]
                
                if not daily_with_weight.empty:
                    # Create weight chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily_with_weight["date_str"],
                        y=daily_with_weight["weight_kg"],
                        mode="lines+markers",
                        line=dict(width=3),
                        marker=dict(size=8)
                    ))
                    
                    fig.update_layout(
                        title="Weight Over Time",
                        xaxis_title="Date",
                        yaxis_title="Weight (kg)",
                        xaxis=dict(type="category")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show weight change stats
                    first_weight = daily_with_weight["weight_kg"].iloc[0]
                    last_weight = daily_with_weight["weight_kg"].iloc[-1]
                    weight_change = last_weight - first_weight
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Starting", f"{first_weight:.1f} kg")
                        st.caption(f"({kg_to_lbs(first_weight):.1f} lbs)")
                    with col2:
                        st.metric("Current", f"{last_weight:.1f} kg")
                        st.caption(f"({kg_to_lbs(last_weight):.1f} lbs)")
                    with col3:
                        st.metric("Change", f"{weight_change:+.1f} kg")
                        st.caption(f"({kg_to_lbs(weight_change):+.1f} lbs)")
                else:
                    st.info("No weight data yet. Update in BMI & Metabolism tab.")
        else:
            # Standard metric chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily["date_str"],
                y=daily[metric],
                mode="lines+markers",
                line=dict(width=3)
            ))
            
            # Proper axis labels
            y_labels = {
                "recovery": "Recovery (%)",
                "strain": "Strain (0-21)",
                "rhr": "Resting HR (BPM)",
                "hrv": "HRV (ms)",
                "stress": "Stress (0-10)",
                "readiness": "Readiness (%)",
                "steps": "Steps"
            }
            
            fig.update_layout(
                title=f"{metric.capitalize()} Over Time",
                xaxis_title="Date",
                yaxis_title=y_labels.get(metric, metric.capitalize()),
                xaxis=dict(type="category")
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No history yet. Refresh in the Heart tab to start tracking.")

# ============================================================================
# TAB 4: BMI & METABOLISM CALCULATOR
# ============================================================================

with tab4:
    st.subheader("⚖️ Body Metrics & Metabolism Calculator")
    
    # Load existing profile
    profile = load_user_profile()
    
    # Unit preference toggles
    col_unit1, col_unit2 = st.columns(2)
    with col_unit1:
        height_unit = st.radio("Height Unit", ["Centimeters (cm)", "Inches (in)"], horizontal=True)
    with col_unit2:
        weight_unit = st.radio("Weight Unit", ["Kilograms (kg)", "Pounds (lbs)"], horizontal=True)
    
    use_cm = "Centimeters" in height_unit
    use_kg = "Kilograms" in weight_unit
    
    # ========================================================================
    # USER PROFILE FORM
    # ========================================================================
    with st.form("user_profile_form"):
        st.write("**Enter your information:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age input
            age = st.number_input(
                "Age (years)", 
                min_value=10, 
                max_value=120, 
                value=profile["age"] if profile else 30,
                step=1
            )
            
            # Weight input with unit conversion
            if use_kg:
                weight_input = st.number_input(
                    "Weight (kg)", 
                    min_value=20.0, 
                    max_value=300.0, 
                    value=profile["weight_kg"] if profile else 70.0,
                    step=0.1
                )
                weight_kg = weight_input
            else:
                default_lbs = kg_to_lbs(profile["weight_kg"]) if profile else 154.0
                weight_input = st.number_input(
                    "Weight (lbs)", 
                    min_value=44.0, 
                    max_value=660.0, 
                    value=default_lbs,
                    step=0.1
                )
                weight_kg = lbs_to_kg(weight_input)
            
            # Height input with unit conversion
            if use_cm:
                height_input = st.number_input(
                    "Height (cm)", 
                    min_value=100.0, 
                    max_value=250.0, 
                    value=profile["height_cm"] if profile else 170.0,
                    step=0.1
                )
                height_cm = height_input
            else:
                default_inches = cm_to_inches(profile["height_cm"]) if profile else 67.0
                height_input = st.number_input(
                    "Height (inches)", 
                    min_value=39.0, 
                    max_value=98.0, 
                    value=default_inches,
                    step=0.1
                )
                height_cm = inches_to_cm(height_input)
        
        with col2:
            # Sex selector
            sex = st.selectbox(
                "Sex",
                ["Male", "Female"],
                index=0 if (profile and profile["sex"] == "Male") else 0
            )
            
            # Activity level measurement method
            activity_method = st.radio(
                "Activity measurement:",
                ["Average Daily Steps", "Weekly Exercise Minutes"],
                index=0
            )
            
            if activity_method == "Average Daily Steps":
                avg_steps = st.number_input(
                    "Average steps per day",
                    min_value=0,
                    max_value=50000,
                    value=profile.get("avg_steps_per_day", 5000) if profile else 5000,
                    step=500
                )
                activity_minutes = None
            else:
                activity_minutes = st.number_input(
                    "Exercise minutes per week",
                    min_value=0,
                    max_value=2000,
                    value=profile.get("activity_minutes_per_week", 150) if profile else 150,
                    step=10
                )
                avg_steps = None
        
        submitted = st.form_submit_button("💾 Calculate & Save")
    
    # ========================================================================
    # SAVE PROFILE & UPDATE HISTORY
    # ========================================================================
    if submitted:
        # Save profile (always in metric units internally)
        new_profile = {
            "age": age,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "sex": sex,
            "avg_steps_per_day": avg_steps,
            "activity_minutes_per_week": activity_minutes,
            "last_updated": datetime.now().isoformat()
        }
        save_user_profile(new_profile)
        profile = new_profile
        
        # Update today's history entry with new weight
        history_path = "data/history.csv"
        m = get_metrics()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_date = datetime.now().date()
        
        if os.path.exists(history_path):
            existing_history = pd.read_csv(history_path)
            existing_history["date"] = pd.to_datetime(existing_history["date"]).dt.date
            
            if today_date in existing_history["date"].values:
                # Update existing entry
                existing_history.loc[existing_history["date"] == today_date, "weight_kg"] = weight_kg
                existing_history.to_csv(history_path, index=False)
                st.success("✅ Profile saved and weight updated!")
            else:
                # Create new entry
                new_entry = pd.DataFrame({
                    "date": [today_str],
                    "recovery": [m.get("recovery", 0)],
                    "strain": [m.get("strain", 0)],
                    "rhr": [m.get("rhr", 0)],
                    "hrv": [m.get("hrv", 0)],
                    "stress": [m.get("stress", 0)],
                    "readiness": [m.get("readiness", 0)],
                    "steps": [m.get("steps", 0)],
                    "weight_kg": [weight_kg]
                })
                combined = pd.concat([existing_history, new_entry])
                combined.to_csv(history_path, index=False)
                st.success("✅ Profile saved and logged to history!")
        else:
            # Create new history file
            new_entry = pd.DataFrame({
                "date": [today_str],
                "recovery": [m.get("recovery", 0)],
                "strain": [m.get("strain", 0)],
                "rhr": [m.get("rhr", 0)],
                "hrv": [m.get("hrv", 0)],
                "stress": [m.get("stress", 0)],
                "readiness": [m.get("readiness", 0)],
                "steps": [m.get("steps", 0)],
                "weight_kg": [weight_kg]
            })
            new_entry.to_csv(history_path, index=False)
            st.success("✅ Profile saved and history started!")
        
        st.cache_data.clear()
        st.rerun()
    
    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    if profile:
        st.divider()
        
        # Calculate all metrics
        bmi = calculate_bmi(profile["weight_kg"], profile["height_cm"])
        bmi_category, bmi_color = get_bmi_category(bmi)
        bmr = calculate_bmr(profile["weight_kg"], profile["height_cm"], profile["age"], profile["sex"])
        tdee = calculate_tdee(bmr, profile.get("activity_minutes_per_week"), profile.get("avg_steps_per_day"))
        
        st.subheader("📊 Your Results")
        
        col1, col2, col3 = st.columns(3)
        
        # BMI Display with gauge
        with col1:
            st.metric("BMI", f"{bmi:.1f}", delta=bmi_category)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=bmi,
                title={'text': "<b>BMI</b>"},
                gauge={
                    'axis': {'range': [15, 40]},
                    'bar': {'color': bmi_color},
                    'steps': [
                        {'range': [15, 18.5], 'color': "lightblue"},
                        {'range': [18.5, 25], 'color': "lightgreen"},
                        {'range': [25, 30], 'color': "lightyellow"},
                        {'range': [30, 40], 'color': "lightcoral"}
                    ]
                }
            ))
            fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # BMR Display
        with col2:
            st.metric("BMR", f"{int(bmr)} cal/day", help="Calories at complete rest")
            st.write("")
            st.caption(f"💡 Weight: **{profile['weight_kg']:.1f} kg** / **{kg_to_lbs(profile['weight_kg']):.1f} lbs**")
            st.caption(f"💡 Height: **{profile['height_cm']:.1f} cm** / **{cm_to_inches(profile['height_cm']):.1f} in**")
        
        # TDEE Display
        with col3:
            st.metric("TDEE", f"{int(tdee)} cal/day", help="Total daily calories burned")
            st.write("")
            st.success("**Total Daily Energy Expenditure** including all activity")
        
        # ====================================================================
        # CALORIE BREAKDOWN
        # ====================================================================
        st.divider()
        st.subheader("🔥 Calorie Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**To maintain weight:**")
            st.write(f"- Eat **{int(tdee)}** cal/day")
            st.write("")
            st.write("**To lose 0.5 kg/week:**")
            st.write(f"- Eat **{int(tdee - 500)}** cal/day")
            st.write("")
            st.write("**To gain 0.5 kg/week:**")
            st.write(f"- Eat **{int(tdee + 500)}** cal/day")
        
        with col2:
            activity_calories = tdee - bmr
            st.write("**Your calorie sources:**")
            st.write(f"- Base metabolism: {int(bmr)} cal")
            st.write(f"- Activity: {int(activity_calories)} cal")
            st.write(f"- Total: {int(tdee)} cal")
            
            # Activity level label
            if profile.get("avg_steps_per_day"):
                steps = profile["avg_steps_per_day"]
                if steps < 3000:
                    level = "Sedentary"
                elif steps < 5000:
                    level = "Lightly Active"
                elif steps < 7500:
                    level = "Moderately Active"
                elif steps < 10000:
                    level = "Very Active"
                else:
                    level = "Extremely Active"
                st.info(f"📱 **{level}** ({steps:,} steps/day)")
        
        # Educational info
        with st.expander("ℹ️ Understanding These Metrics"):
            st.write("""
            **BMI:** Height/weight ratio. Not perfect (doesn't account for muscle).
            - Underweight: < 18.5
            - Normal: 18.5-24.9
            - Overweight: 25-29.9
            - Obese: ≥ 30
            
            **BMR:** Calories burned at rest (Mifflin-St Jeor equation).
            
            **TDEE:** Total daily burn including activity.
            
            **Weight Math:**
            - 1 kg fat = ~7,700 calories
            - 500 cal/day deficit = 0.5 kg loss/week
            """)
        
        # ====================================================================
        # TRAINING INSIGHTS
        # ====================================================================
        st.divider()
        st.subheader("💡 Training Insights")
        
        m = get_metrics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Today's Strain:** {m['strain']:.1f}/21")
            estimated_calories = int(activity_calories * (m['strain'] / 14))
            st.write(f"**Est. calories from activity:** ~{estimated_calories} cal")
        
        with col2:
            st.write(f"**Training Readiness:** {m['readiness']}%")
            if m['readiness'] > 70:
                st.success("✅ Ready for hard workout!")
            elif m['readiness'] > 40:
                st.warning("⚠️ Light workout only")
            else:
                st.error("🛑 Rest day - focus on recovery")
    else:
        st.info("👆 Fill out the form above to calculate your metrics!")

# ============================================================================
# TAB 5: BLOOD SUGAR TRACKING
# ============================================================================

with tab5:
    st.subheader("🩸 Blood Sugar & Insulin Sensitivity Tracker")

    st.info("""
    **📋 How to use this tracker:**
    1. Measure your fasting blood glucose (before eating)
    2. Eat your meal
    3. Wait 1-2 hours after starting your meal
    4. Measure your blood glucose again (post-meal)
    5. Enter both values below to assess your insulin sensitivity
    """)

    # ========================================================================
    # BLOOD GLUCOSE INPUT FORM
    # ========================================================================
    with st.form("blood_sugar_form"):
        st.write("### 📊 Enter Your Measurements")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Before Meal (Fasting):**")
            fasting_glucose = st.number_input(
                "Fasting Blood Glucose (mg/dL)",
                min_value=40.0,
                max_value=400.0,
                value=90.0,
                step=1.0,
                help="Measure BEFORE eating (ideally after 8+ hours of fasting)"
            )

            # Show real-time fasting assessment
            fasting_assess = assess_fasting_glucose(fasting_glucose)
            st.caption(f"{fasting_assess['emoji']} {fasting_assess['status']}")

        with col2:
            st.write("**After Meal (Postprandial):**")
            postprandial_glucose = st.number_input(
                "Post-Meal Blood Glucose (mg/dL)",
                min_value=40.0,
                max_value=400.0,
                value=120.0,
                step=1.0,
                help="Measure 1-2 hours AFTER starting your meal"
            )

            hours_after = st.number_input(
                "Hours after meal started",
                min_value=0.5,
                max_value=4.0,
                value=1.0,
                step=0.25,
                help="Ideally 1-2 hours for accurate results"
            )

        # Meal information
        col3, col4 = st.columns(2)
        with col3:
            meal_type = st.selectbox(
                "Meal Type",
                ["Breakfast", "Lunch", "Dinner", "Snack"],
                help="Which meal did you test?"
            )

        with col4:
            notes = st.text_input(
                "Notes (optional)",
                placeholder="e.g., 'High carb pasta meal'",
                help="Any details about the meal"
            )

        # Submit button
        submitted = st.form_submit_button("🔬 Analyze My Results", use_container_width=True)

    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    if submitted:
        # Get comprehensive assessment
        assessment = assess_insulin_sensitivity(
            fasting_glucose,
            postprandial_glucose,
            hours_after
        )

        # Save to history
        save_glucose_measurement(
            fasting_glucose,
            postprandial_glucose,
            hours_after,
            meal_type,
            notes
        )

        st.success("✅ Measurement saved to history!")
        st.divider()

        # ====================================================================
        # OVERALL HEALTH STATUS
        # ====================================================================
        st.subheader(f"{assessment['overall_emoji']} Overall Assessment")

        # Large, prominent status display
        status_color_map = {
            "green": "🟢",
            "lightgreen": "🟢",
            "orange": "🟠",
            "red": "🔴"
        }

        status_emoji = status_color_map.get(assessment['overall_color'], "⚪")

        st.markdown(f"### {status_emoji} {assessment['overall_status']}")
        st.markdown(f"**Insulin Sensitivity Score: {assessment['sensitivity_score']}/100**")

        # Progress bar for sensitivity score
        score_color = assessment['overall_color']
        st.progress(assessment['sensitivity_score'] / 100)

        # Risk level
        if assessment['risk_level'] == "Low Risk":
            st.success(f"**Risk Level:** {assessment['risk_level']}")
        elif "Moderate" in assessment['risk_level']:
            st.warning(f"**Risk Level:** {assessment['risk_level']}")
        else:
            st.error(f"**Risk Level:** {assessment['risk_level']}")

        st.divider()

        # ====================================================================
        # DETAILED BREAKDOWN
        # ====================================================================
        st.subheader("📋 Detailed Analysis")

        col1, col2, col3 = st.columns(3)

        # Fasting glucose
        with col1:
            fasting = assessment['fasting_assessment']
            st.metric(
                "Fasting Glucose",
                f"{fasting_glucose:.0f} mg/dL",
                delta=fasting['status']
            )
            if fasting['category'] == 'healthy':
                st.success(f"{fasting['emoji']} {fasting['status']}")
            elif fasting['category'] == 'warning':
                st.warning(f"{fasting['emoji']} {fasting['status']}")
            else:
                st.error(f"{fasting['emoji']} {fasting['status']}")

        # Post-meal glucose
        with col2:
            postprandial = assessment['postprandial_assessment']
            st.metric(
                f"Post-Meal ({hours_after}h)",
                f"{postprandial_glucose:.0f} mg/dL",
                delta=postprandial['status']
            )
            if postprandial['category'] == 'healthy':
                st.success(f"{postprandial['emoji']} {postprandial['status']}")
            elif postprandial['category'] == 'warning':
                st.warning(f"{postprandial['emoji']} {postprandial['status']}")
            else:
                st.error(f"{postprandial['emoji']} {postprandial['status']}")

        # Glucose spike
        with col3:
            spike = assessment['spike_assessment']
            st.metric(
                "Glucose Spike",
                f"{spike['spike_mg_dl']:.0f} mg/dL",
                delta=spike['status']
            )
            spike_color_map = {
                "green": st.success,
                "lightgreen": st.success,
                "orange": st.warning,
                "red": st.error,
                "blue": st.info
            }
            display_func = spike_color_map.get(spike['color'], st.info)
            display_func(f"{spike['emoji']} {spike['status']}")

        st.divider()

        # ====================================================================
        # RECOMMENDATIONS
        # ====================================================================
        st.subheader("💡 Personalized Recommendations")

        # Main recommendation
        if assessment['sensitivity_score'] >= 80:
            st.success(assessment['recommendation'])
        elif assessment['sensitivity_score'] >= 60:
            st.info(assessment['recommendation'])
        elif assessment['sensitivity_score'] >= 40:
            st.warning(assessment['recommendation'])
        else:
            st.error(assessment['recommendation'])

        # Additional educational info
        with st.expander("📚 Understanding Your Results"):
            st.write("""
            **What is Insulin Sensitivity?**
            - Insulin sensitivity is how well your cells respond to insulin
            - High sensitivity = GOOD (cells efficiently absorb glucose)
            - Low sensitivity (insulin resistance) = BAD (risk for type 2 diabetes)

            **Healthy Blood Sugar Ranges:**
            - **Fasting:** 70-99 mg/dL (normal), 100-125 (prediabetes), 126+ (diabetes)
            - **Post-meal (1-2h):** < 140 mg/dL (normal), 140-199 (prediabetes), 200+ (diabetes)
            - **Glucose Spike:** < 30-40 mg/dL (excellent control)

            **How to Improve Insulin Sensitivity:**
            1. **Diet:** Reduce refined carbs and sugar, increase fiber, eat more vegetables
            2. **Exercise:** 150+ min/week, especially strength training
            3. **Sleep:** 7-9 hours quality sleep per night
            4. **Weight:** Lose excess weight (even 5-10% helps significantly)
            5. **Stress:** Manage stress through meditation, yoga, or other relaxation
            6. **Fasting:** Consider intermittent fasting (consult doctor first)

            **When to See a Doctor:**
            - Fasting glucose consistently > 100 mg/dL
            - Post-meal glucose > 140 mg/dL
            - Large glucose spikes (> 50 mg/dL)
            - Symptoms: excessive thirst, frequent urination, fatigue, blurred vision
            """)

        # Spike visualization
        with st.expander("📊 Visualize Your Glucose Response"):
            import plotly.graph_objects as go

            # Create a simple visualization of the glucose curve
            fig = go.Figure()

            # Simulated glucose curve (simplified model)
            time_points = [0, hours_after]
            glucose_values = [fasting_glucose, postprandial_glucose]

            fig.add_trace(go.Scatter(
                x=time_points,
                y=glucose_values,
                mode='lines+markers',
                name='Your Glucose',
                line=dict(color=assessment['overall_color'], width=4),
                marker=dict(size=12)
            ))

            # Add healthy reference range
            fig.add_hline(y=140, line_dash="dash", line_color="orange",
                         annotation_text="Post-meal threshold (140 mg/dL)")
            fig.add_hline(y=100, line_dash="dash", line_color="green",
                         annotation_text="Fasting threshold (100 mg/dL)")

            fig.update_layout(
                title="Your Glucose Response Curve",
                xaxis_title="Hours After Meal",
                yaxis_title="Blood Glucose (mg/dL)",
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

    # ========================================================================
    # GLUCOSE HISTORY
    # ========================================================================
    st.divider()
    st.subheader("📊 Your Blood Sugar History")

    history = load_glucose_history()

    if not history.empty:
        # Summary statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_fasting = history['fasting_mg_dl'].mean()
            st.metric("Avg Fasting", f"{avg_fasting:.1f} mg/dL")

        with col2:
            avg_postprandial = history['postprandial_mg_dl'].mean()
            st.metric("Avg Post-Meal", f"{avg_postprandial:.1f} mg/dL")

        with col3:
            avg_sensitivity = history['sensitivity_score'].mean()
            st.metric("Avg Sensitivity Score", f"{avg_sensitivity:.0f}/100")

        # History table
        st.write("### Recent Measurements")

        # Format the display dataframe
        display_df = history[['date', 'meal_type', 'fasting_mg_dl', 'postprandial_mg_dl',
                              'spike_mg_dl', 'sensitivity_score', 'notes']].copy()
        display_df.columns = ['Date', 'Meal', 'Fasting', 'Post-Meal', 'Spike', 'Score', 'Notes']

        # Sort by most recent first
        display_df = display_df.sort_values('Date', ascending=False)

        st.dataframe(display_df.head(10), use_container_width=True)

        # Trend visualization
        with st.expander("📈 View Trends Over Time"):
            metric_choice = st.selectbox(
                "Select metric to visualize:",
                ["Sensitivity Score", "Fasting Glucose", "Post-Meal Glucose", "Glucose Spike"]
            )

            metric_map = {
                "Sensitivity Score": "sensitivity_score",
                "Fasting Glucose": "fasting_mg_dl",
                "Post-Meal Glucose": "postprandial_mg_dl",
                "Glucose Spike": "spike_mg_dl"
            }

            metric_col = metric_map[metric_choice]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=history['date'],
                y=history[metric_col],
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=8)
            ))

            fig.update_layout(
                title=f"{metric_choice} Over Time",
                xaxis_title="Date",
                yaxis_title=metric_choice,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("📝 No history yet. Complete the form above to start tracking your blood sugar!")

    # Educational section
    with st.expander("❓ Why Track Blood Sugar?"):
        st.write("""
        **Blood sugar tracking is important even if you're not diabetic:**

        ✅ **Early Detection:** Catch prediabetes before it becomes diabetes
        ✅ **Performance:** Stable blood sugar = better energy and focus
        ✅ **Weight Management:** Understanding glucose response helps optimize diet
        ✅ **Longevity:** Good glucose control reduces aging and disease risk
        ✅ **Athletic Performance:** Optimize fueling for workouts and recovery

        **Best Practices:**
        - Test at the same times for consistency
        - Track what you eat to identify problem foods
        - Aim for minimal glucose spikes (< 30 mg/dL)
        - Test different meal compositions to find what works for you
        - Share results with your doctor during checkups
        """)