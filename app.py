# ============================================================================
# CHEAP WHOOP - Fitness Tracking App
# ============================================================================
# A low-cost alternative to WHOOP using affordable hardware (Xiaomi + Coospo)
# Tracks heart rate, HRV, sleep, steps, body metrics, and provides
# training recommendations based on recovery data.
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

# Unit conversion functions
def cm_to_inches(cm):
    return cm / 2.54

def inches_to_cm(inches):
    return inches * 2.54

def kg_to_lbs(kg):
    return kg * 2.20462

def lbs_to_kg(lbs):
    return lbs / 2.20462

# Metabolic calculations
def calculate_bmr(weight_kg, height_cm, age, sex):
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.
    Returns calories burned per day at complete rest.
    """
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return bmr

def calculate_tdee(bmr, activity_minutes_per_week=None, avg_steps_per_day=None):
    """
    Calculate Total Daily Energy Expenditure.
    Uses either activity minutes OR step count for activity multiplier.
    """
    # Prefer steps if both are provided (more accurate)
    if avg_steps_per_day:
        if avg_steps_per_day < 3000:
            activity_factor = 1.2  # Sedentary
        elif avg_steps_per_day < 5000:
            activity_factor = 1.375  # Lightly active
        elif avg_steps_per_day < 7500:
            activity_factor = 1.55  # Moderately active
        elif avg_steps_per_day < 10000:
            activity_factor = 1.725  # Very active
        else:
            activity_factor = 1.9  # Extremely active
    elif activity_minutes_per_week:
        if activity_minutes_per_week < 30:
            activity_factor = 1.2
        elif activity_minutes_per_week < 150:
            activity_factor = 1.375
        elif activity_minutes_per_week < 300:
            activity_factor = 1.55
        elif activity_minutes_per_week < 420:
            activity_factor = 1.725
        else:
            activity_factor = 1.9
    else:
        activity_factor = 1.2  # Default to sedentary
    
    return bmr * activity_factor

def calculate_bmi(weight_kg, height_cm):
    """Calculate Body Mass Index"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_bmi_category(bmi):
    """Return BMI category and color for visualization"""
    if bmi < 18.5:
        return "Underweight", "blue"
    elif bmi < 25:
        return "Normal weight", "green"
    elif bmi < 30:
        return "Overweight", "orange"
    else:
        return "Obese", "red"

# ============================================================================
# PAGE SETUP
# ============================================================================

st.set_page_config(page_title="Cheap WHOOP", layout="centered")
st.title("💪 Cheap WHOOP")
st.caption("No $30/month. Just $75 hardware + your code.")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["❤️ Heart Data", "😴 Sleep", "📈 History", "⚖️ BMI & Metabolism"])

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
                "weight_kg": [current_weight],
                # Sleep metrics
                "sleep_score": [m["sleep_score"]],
                "sleep_duration_hours": [m["sleep_duration_hours"]],
                "sleep_efficiency_pct": [m["sleep_efficiency_pct"]],
                "sleep_sufficiency": [m["sleep_sufficiency"]],
                "sleep_consistency": [m["sleep_consistency"]],
                "sleep_debt_minutes": [m["sleep_debt_minutes"]],
                "restorative_sleep_pct": [m["restorative_sleep_pct"]],
                "deep_hours": [m["deep_hours"]],
                "rem_hours": [m["rem_hours"]],
                "light_hours": [m["light_hours"]]
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
    st.subheader("😴 Sleep Performance")
    m = get_metrics()

    # ========================================================================
    # SLEEP PERFORMANCE SCORE GAUGE (similar to WHOOP)
    # ========================================================================
    col1, col2 = st.columns(2)

    with col1:
        # Main Sleep Performance Score Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=m["sleep_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "<b>Sleep Performance</b>"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "mediumpurple"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 85], 'color': "lightyellow"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        # Sleep Performance Interpretation
        if m["sleep_score"] >= 85:
            st.success("🌟 **Excellent Sleep!** You're well-rested and recovered.")
        elif m["sleep_score"] >= 70:
            st.info("😊 **Good Sleep** - Adequate rest for most activities.")
        elif m["sleep_score"] >= 60:
            st.warning("😴 **Fair Sleep** - Consider improving sleep quality.")
        else:
            st.error("🚨 **Poor Sleep** - Prioritize rest and recovery.")

    with col2:
        # Sleep Need vs Actual
        st.metric(
            "Sleep Duration",
            m["sleep_duration"],
            delta=f"Need: {m['sleep_need_hours']}h"
        )

        # Sleep Debt
        debt_hours = m["sleep_debt_minutes"] / 60
        debt_label = "🟢 No Debt" if m["sleep_debt_minutes"] < 30 else f"⚠️ {int(m['sleep_debt_minutes'])} min debt"
        st.metric(
            "Sleep Debt",
            debt_label,
            delta="Optimal: <30 min" if m["sleep_debt_minutes"] < 30 else "Need more sleep"
        )

        # Restorative Sleep
        st.metric(
            "Restorative Sleep",
            f"{m['restorative_sleep_pct']}%",
            delta="Target: 50%" if m["restorative_sleep_pct"] >= 50 else "Need more deep/REM"
        )

    # ========================================================================
    # SLEEP SCORE COMPONENTS
    # ========================================================================
    st.markdown("---")
    st.subheader("📊 Sleep Score Components")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Sufficiency",
            f"{m['sleep_sufficiency']}%",
            help="Did you get enough sleep based on your needs? (40% of score)"
        )

    with col2:
        st.metric(
            "Efficiency",
            f"{m['sleep_efficiency_pct']}%",
            help="% of time in bed actually asleep (30% of score). Target: >85%"
        )

    with col3:
        st.metric(
            "Consistency",
            f"{m['sleep_consistency']}%",
            help="Regularity of sleep/wake times over 4 days (20% of score). Target: >90%"
        )

    with col4:
        st.metric(
            "Low Stress",
            f"{m['sleep_stress_score']}%",
            help="Physiological stress during sleep (10% of score). Higher = less stress"
        )

    # ========================================================================
    # SLEEP STAGES BREAKDOWN
    # ========================================================================
    st.markdown("---")
    st.subheader("🌙 Sleep Stages Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        # Sleep stages table
        sleep_data = {
            "Stage": ["Total Sleep", "Light", "Deep", "REM"],
            "Duration": [
                m["sleep_duration"],
                m["light"],
                m["deep"],
                m["rem"]
            ]
        }
        st.table(sleep_data)

    with col2:
        # Sleep stages pie chart
        stages_fig = go.Figure(data=[go.Pie(
            labels=['Light', 'Deep', 'REM'],
            values=[m['light_hours'], m['deep_hours'], m['rem_hours']],
            marker=dict(colors=['lightblue', 'darkblue', 'purple'])
        )])
        stages_fig.update_layout(
            title="Sleep Stage Distribution",
            height=300
        )
        st.plotly_chart(stages_fig, use_container_width=True)

    # ========================================================================
    # SLEEP ANALYSIS EXPLANATION
    # ========================================================================
    with st.expander("ℹ️ How Sleep Performance is Calculated"):
        st.write("""
        **Sleep Performance Score** is calculated using 4 components (similar to WHOOP):

        1. **Sufficiency (40%)**: Did you get enough sleep based on your needs?
           - Baseline: 8 hours
           - Adjusted based on previous day's strain

        2. **Efficiency (30%)**: Quality of sleep - % of time in bed actually asleep
           - Target: >85% (Average: 94.4%)
           - Measures sleep disruptions

        3. **Consistency (20%)**: Regularity of sleep/wake times over last 4 days
           - Target: >90% for optimal circadian rhythm
           - Tracks sleep schedule stability

        4. **Low Stress (10%)**: Physiological stress during sleep
           - Based on heart rate and HRV during sleep
           - Lower stress = better recovery

        **Additional Metrics:**
        - **Sleep Debt**: Accumulated deficit (optimal: <30-45 minutes)
        - **Restorative Sleep**: % time in Deep + REM stages (target: ~50%)

        **Sleep Stages:**
        - Light: Transition sleep, easily awakened
        - Deep: Physical recovery, immune system boost
        - REM: Mental recovery, memory consolidation
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
            ["recovery", "strain", "rhr", "hrv", "stress", "readiness", "sleep_score", "sleep_duration_hours", "sleep_efficiency_pct", "restorative_sleep_pct", "steps", "weight_kg"],
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
                "sleep_score": "Sleep Performance (%)",
                "sleep_duration_hours": "Sleep Duration (hours)",
                "sleep_efficiency_pct": "Sleep Efficiency (%)",
                "restorative_sleep_pct": "Restorative Sleep (%)",
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