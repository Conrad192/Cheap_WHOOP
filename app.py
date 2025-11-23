# ============================================================================
# CHEAP WHOOP - Enhanced Fitness Tracking App
# ============================================================================
# A comprehensive low-cost alternative to WHOOP with advanced features
# ============================================================================

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from metrics import get_metrics
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pull_xiaomi import generate_xiaomi_data
from pull_coospo import generate_coospo_data
from merge import merge_data
import json
import io

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=60)
def load_merged_data():
    """Load merged heart rate data from devices"""
    try:
        return pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_history():
    """Load historical tracking data"""
    history_path = "data/history.csv"
    if os.path.exists(history_path):
        df = pd.read_csv(history_path)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    return pd.DataFrame()

def load_user_profile():
    """Load user profile data"""
    profile_path = "data/user_profile.json"
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            return json.load(f)
    return None

def save_user_profile(profile):
    """Save user profile data"""
    os.makedirs("data", exist_ok=True)
    with open("data/user_profile.json", "w") as f:
        json.dump(profile, f, indent=2)

def load_journal():
    """Load journal entries"""
    journal_path = "data/journal.json"
    if os.path.exists(journal_path):
        with open(journal_path) as f:
            return json.load(f)
    return {}

def save_journal(entries):
    """Save journal entries"""
    os.makedirs("data", exist_ok=True)
    with open("data/journal.json", "w") as f:
        json.dump(entries, f, indent=2)

def load_activity_log():
    """Load workout activity types"""
    log_path = "data/activity_log.json"
    if os.path.exists(log_path):
        with open(log_path) as f:
            return json.load(f)
    return {}

def save_activity_log(log):
    """Save workout activity types"""
    os.makedirs("data", exist_ok=True)
    with open("data/activity_log.json", "w") as f:
        json.dump(log, f, indent=2)

# Unit conversions
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
    """Calculate Basal Metabolic Rate"""
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return bmr

def calculate_tdee(bmr, activity_minutes_per_week=None, avg_steps_per_day=None):
    """Calculate Total Daily Energy Expenditure"""
    if avg_steps_per_day:
        if avg_steps_per_day < 3000:
            activity_factor = 1.2
        elif avg_steps_per_day < 5000:
            activity_factor = 1.375
        elif avg_steps_per_day < 7500:
            activity_factor = 1.55
        elif avg_steps_per_day < 10000:
            activity_factor = 1.725
        else:
            activity_factor = 1.9
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
        activity_factor = 1.2
    return bmr * activity_factor

def calculate_bmi(weight_kg, height_cm):
    """Calculate Body Mass Index"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_bmi_category(bmi):
    """Return BMI category and color"""
    if bmi < 18.5:
        return "Underweight", "blue"
    elif bmi < 25:
        return "Normal weight", "green"
    elif bmi < 30:
        return "Overweight", "orange"
    else:
        return "Obese", "red"

def export_to_csv():
    """Export all data to CSV"""
    history_df = load_history()
    if history_df.empty:
        return None

    buffer = io.StringIO()
    history_df.to_csv(buffer, index=False)
    return buffer.getvalue()

# ============================================================================
# THEME SETUP
# ============================================================================

# Load theme preference
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# ============================================================================
# PAGE SETUP
# ============================================================================

st.set_page_config(
    page_title="Cheap WHOOP Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme CSS
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #262730;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# Settings sidebar
with st.sidebar:
    st.title("Settings")

    # Theme toggle
    theme_options = ["Light", "Dark"]
    current_theme = "Dark" if st.session_state.theme == "dark" else "Light"
    selected_theme = st.radio("Theme", theme_options, index=theme_options.index(current_theme), horizontal=True)

    new_theme = "dark" if selected_theme == "Dark" else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.divider()

    # Export button
    st.subheader("Export Data")
    csv_data = export_to_csv()
    if csv_data:
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"cheap_whoop_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available for export")

    st.divider()

    # Quick stats
    st.subheader("Statistics")
    history_df = load_history()
    if not history_df.empty:
        st.metric("Days Tracked", len(history_df))
        st.metric("Avg Recovery", f"{int(history_df['recovery'].mean())}%")
        st.metric("Avg Strain", f"{history_df['strain'].mean():.1f}")

st.title("Cheap WHOOP Pro")
st.caption("Professional fitness tracking without the subscription.")

# Create compact tabs
tabs = st.tabs([
    "Dashboard",
    "Heart & Training",
    "Sleep",
    "Workouts",
    "Trends",
    "Achievements",
    "Journal",
    "Body Metrics"
])

# ============================================================================
# TAB 1: DASHBOARD - Overview of everything
# ============================================================================

with tabs[0]:
    st.header("Today's Dashboard")

    # Load metrics
    m = get_metrics()

    # Top status banner
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if m["recovery"] > 66:
            st.success("**Ready to Train** - Your body is recovered")
        elif m["recovery"] > 33:
            st.warning("**Moderate Recovery** - Light workout recommended")
        else:
            st.error("**Rest Day** - Prioritize recovery today")

    with col2:
        if st.button("Refresh Data", use_container_width=True):
            with st.spinner("Refreshing..."):
                generate_xiaomi_data()
                generate_coospo_data()
                merge_data()

                # Update history
                m = get_metrics()
                profile = load_user_profile()
                current_weight = profile["weight_kg"] if profile else None

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
                    "sleep_duration_hours": [m["sleep_duration_hours"]]
                })

                if os.path.exists(history_path):
                    old_history = pd.read_csv(history_path)
                    combined = pd.concat([old_history, history_df])
                    combined["date"] = pd.to_datetime(combined["date"]).dt.date
                    combined = combined.drop_duplicates(subset="date", keep="last")
                else:
                    combined = history_df

                combined.to_csv(history_path, index=False)
                st.cache_data.clear()

            st.success("Data updated successfully")
            st.rerun()

    with col3:
        today = datetime.now().strftime("%m/%d/%Y")
        st.info(f"Date: {today}")

    st.divider()

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Recovery", f"{m['recovery']}%",
                 help="Recovery Score (0-100%): Calculated from HRV and RHR overnight data. Formula: (HRV/80) × 100 × (60/RHR). Higher scores (67-100%) indicate full recovery and readiness for intense training. Moderate scores (34-66%) suggest light activity. Low scores (0-33%) indicate need for rest.")
    with col2:
        st.metric("Strain", f"{m['strain']:.1f}",
                 help="Cardiovascular Strain (0-21 scale): Combines heart rate elevation above resting baseline and daily step count. Calculated from cumulative heart rate excess above RHR + step-based component (10,000 steps ≈ 3 strain points). 0-7: Light day, 7-14: Moderate activity, 14-21: Hard training.")
    with col3:
        st.metric("HRV", f"{m['hrv']} ms",
                 help="Heart Rate Variability (RMSSD method): Measures beat-to-beat variation in heart rate using R-R intervals. Calculated as root mean square of successive differences between heartbeats. Higher values (50-80+ ms) indicate better recovery, stress adaptation, and cardiovascular fitness. Lower values may indicate fatigue, stress, or overtraining.")
    with col4:
        st.metric("RHR", f"{m['rhr']} BPM",
                 help="Resting Heart Rate: Calculated from the lowest 5% of heart rate readings during nighttime hours (12 AM - 6 AM). Lower values (40-60 BPM for athletes, 60-100 for general population) indicate better cardiovascular fitness. Trends over time are more important than single values.")
    with col5:
        st.metric("Sleep Score", f"{m['sleep_score']}/100",
                 help="Sleep Performance Score (0-100): Weighted combination of sleep duration (40%), deep sleep quality (30%), and REM sleep quality (30%). Duration scored against 8-hour target, deep sleep against 2-hour target, REM against 2-hour target. Scores 80+: Excellent, 65-79: Good, 50-64: Fair, <50: Poor.")

    st.divider()

    # Strain Coach & Goal
    st.subheader("Today's Training Goal")

    strain_goal = m["strain_goal"]
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"**Recommended Strain:** {strain_goal['min']}-{strain_goal['max']} ({strain_goal['label']})")
        st.write(f"**Coach:** {m['strain_coach']}")

        # Progress bar
        progress = min(1.0, m['strain'] / strain_goal['max'])
        st.progress(progress)
        st.caption(f"Current: {m['strain']:.1f} / Goal: {strain_goal['max']}")

    with col2:
        # Hydration reminder
        if m['strain'] > 12:
            st.warning("**Hydration Alert**\nHigh strain detected. Increase fluid intake.")
        elif m['strain'] > 8:
            st.info("Stay properly hydrated")

    st.divider()

    # Overtraining Alert
    overtraining = m["overtraining"]
    if overtraining["risk"] in ["high", "moderate"]:
        st.error(f"**Overtraining Alert**: {overtraining['risk'].upper()} risk")
        for alert in overtraining["alerts"]:
            st.write(f"- {alert}")
        st.write(f"**Recommendation:** {overtraining['recommendation']}")
        st.divider()

    # Rest Day Recommendation
    rest_day = m["rest_day"]
    if rest_day and rest_day["rest_recommended"]:
        st.warning("**Rest Day Recommended**")
        st.write("Reasons:")
        for reason in rest_day["reasons"]:
            st.write(f"- {reason}")
        st.divider()

    # Recovery Prediction
    recovery_pred = m["recovery_prediction"]
    if recovery_pred:
        st.subheader("Tomorrow's Recovery Forecast")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Predicted Recovery", f"{recovery_pred['predicted_recovery']}%")

        with col2:
            st.metric("Confidence", recovery_pred["confidence"].capitalize())

        with col3:
            factors = recovery_pred["factors"]
            st.write("**Key Factors:**")
            st.caption(f"HRV: {factors['hrv_trend']}")
            st.caption(f"RHR: {factors['rhr_trend']}")
            st.caption(f"Strain: {factors['strain_level']}")

        st.divider()

    # Quick Training Load
    st.subheader("7-Day Training Load")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Strain (7d)", f"{m['training_load']:.1f}")
    with col2:
        st.metric("Daily Average", f"{m['training_load']/7:.1f}")
    with col3:
        load_status = "High" if m['training_load'] > 100 else "Moderate" if m['training_load'] > 70 else "Low"
        st.metric("Load Status", load_status)

    # Achievements Banner
    achievements = m["achievements"]
    if achievements:
        st.divider()
        st.subheader("Recent Achievements")
        cols = st.columns(min(4, len(achievements)))
        for i, achievement in enumerate(achievements[:4]):
            with cols[i]:
                st.info(f"**{achievement['name']}**\n\n{achievement['description']}")

# ============================================================================
# TAB 2: HEART & TRAINING - Detailed heart metrics
# ============================================================================

with tabs[1]:
    st.header("Heart Data & Training")

    m = get_metrics()

    # Main Gauges
    col1, col2 = st.columns(2)

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
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': m["strain_goal"]["max"]
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

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

    # HRV & RHR
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("HRV", f"{m['hrv']} ms",
                 help="Heart Rate Variability (RMSSD): Root mean square of successive R-R interval differences. Higher values indicate better parasympathetic nervous system activity, recovery capacity, and stress resilience. Typical ranges: 20-80ms (highly individual).")
    with col2:
        st.metric("RHR", f"{m['rhr']} BPM",
                 help="Resting Heart Rate: Lowest 5% of nighttime heart rate (12 AM-6 AM). Lower values indicate better cardiovascular fitness and efficiency. Athletes: 40-60 BPM, General: 60-100 BPM. Improving fitness typically lowers RHR over time.")
    with col3:
        st.metric("Stress", f"{m['stress']}/10",
                 help="Stress Score (0-10): Calculated from hourly heart rate and HRV patterns. High HR + low HRV variation = higher stress. This measures nervous system tension (sympathetic activation), not physical workload. Useful for identifying mental/emotional stress throughout the day.")
    with col4:
        st.metric("Readiness", f"{m['readiness']}%",
                 help="Training Readiness (0-100%): Weighted combination of HRV (25%), RHR (15%), Recovery (40% - most important), and Sleep Efficiency (20%). Answers 'Should I work out hard today?' Higher scores indicate you're physiologically prepared for intense training.")

    st.divider()

    # VO2 Max
    st.subheader("VO2 Max Estimation")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("VO2 Max", f"{m['vo2_max']} ml/kg/min",
                 help="VO2 Max Estimation: Maximum oxygen uptake capacity during intense exercise. Estimated from RHR and age using formula: 15.3 × (max HR / RHR). Higher values indicate better aerobic fitness and endurance capacity. Elite athletes: 60-80+, Good: 45-60, Average: 35-45, Below Average: <35.")

    with col2:
        if m['vo2_max'] > 55:
            category = "Excellent"
        elif m['vo2_max'] > 45:
            category = "Good"
        elif m['vo2_max'] > 35:
            category = "Average"
        else:
            category = "Below Average"
        st.metric("Category", category,
                 help="VO2 Max Category: Fitness classification based on estimated oxygen uptake capacity. Excellent (>55): Elite endurance, Good (45-55): High fitness, Average (35-45): Moderate fitness, Below Average (<35): Needs improvement.")

    with col3:
        st.metric("Respiratory Rate", f"{m['respiratory_rate']}/min" if m['respiratory_rate'] else "N/A",
                 help="Respiratory Rate Estimation: Breaths per minute estimated from heart rate variability patterns (respiratory sinus arrhythmia - RSA). Breathing causes regular oscillations in heart rate. Normal resting range: 12-20 breaths/min. Lower rates often indicate better cardiovascular fitness and relaxation.")

    st.divider()

    # SpO2 Trends
    if m["spo2_data"]:
        st.subheader("Blood Oxygen (SpO2) Trends")

        spo2 = m["spo2_data"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Average", f"{spo2['avg']}%",
                     help="Average Blood Oxygen Saturation: Mean SpO2 level across all readings. Normal healthy range: 95-100%. Values below 95% may indicate respiratory issues. Consistent readings 95%+ indicate good oxygen delivery to tissues.")
        with col2:
            st.metric("Minimum", f"{spo2['min']}%",
                     help="Minimum SpO2: Lowest blood oxygen reading detected. Critical threshold: <90% requires medical attention. Occasional drops to 90-94% during deep sleep can be normal, but persistent low values may indicate sleep apnea or other respiratory conditions.")
        with col3:
            st.metric("Maximum", f"{spo2['max']}%",
                     help="Maximum SpO2: Highest blood oxygen reading. Normal maximum is typically 98-100%. Healthy individuals usually maintain high saturation (97-100%) during most of the day and night.")
        with col4:
            st.metric("Excellent %", f"{spo2['excellent_pct']}%",
                     help="Time at Excellent Levels (≥98%): Percentage of time with optimal blood oxygen saturation. Higher percentages indicate better respiratory function and oxygen delivery. Target: >80% of time at excellent levels for optimal health.")

        # SpO2 Distribution
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(data=[
                go.Bar(name='Excellent (≥98%)', x=['SpO2 Distribution'], y=[spo2['excellent_pct']], marker_color='green'),
                go.Bar(name='Good (95-98%)', x=['SpO2 Distribution'], y=[spo2['good_pct']], marker_color='yellow'),
                go.Bar(name='Low (<95%)', x=['SpO2 Distribution'], y=[spo2['low_pct']], marker_color='red')
            ])
            fig.update_layout(barmode='stack', height=300, title="SpO2 Time Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if spo2['alerts']:
                st.warning("**Alerts:**")
                for alert in spo2['alerts']:
                    st.write(f"- {alert}")
            else:
                st.success("All SpO2 readings normal")

        st.divider()

    # Heart Rate Zones
    if m["hr_zones"]:
        st.subheader("Heart Rate Zones")

        zones = m["hr_zones"]
        zone_names = list(zones.keys())
        zone_values = list(zones.values())

        # Convert minutes to percentages
        total_time = sum(zone_values)
        if total_time > 0:
            zone_percentages = [(v/total_time)*100 for v in zone_values]

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = go.Figure(data=[
                    go.Bar(x=zone_names, y=zone_values, marker_color=['lightgray', 'lightblue', 'yellow', 'orange', 'red'])
                ])
                fig.update_layout(title="Time in Each Zone (minutes)", height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.write("**Zone Breakdown:**")
                for name, minutes, pct in zip(zone_names, zone_values, zone_percentages):
                    st.write(f"**{name}:** {minutes} min ({pct:.1f}%)")

        st.divider()

    # Hourly Strain Breakdown
    if m["hourly_strain"] is not None and not m["hourly_strain"].empty:
        st.subheader("Hourly Strain Breakdown")

        hourly_df = m["hourly_strain"].reset_index()

        # Get the column names (first is timestamp, second is strain values)
        timestamp_col = hourly_df.columns[0]
        strain_col = hourly_df.columns[1]

        # Format hours as readable time (12 AM, 1 PM, etc.)
        hourly_df['hour_label'] = pd.to_datetime(hourly_df[timestamp_col]).dt.strftime('%I %p').str.lstrip('0')

        fig = go.Figure(data=[
            go.Bar(
                x=hourly_df['hour_label'],
                y=hourly_df[strain_col],
                marker_color='cyan',
                hovertemplate='<b>%{x}</b><br>Strain: %{y:.2f}<extra></extra>'
            )
        ])
        fig.update_layout(
            title="Strain by Hour of Day",
            xaxis_title="Hour",
            yaxis_title="Strain",
            height=400,
            xaxis={'categoryorder': 'array', 'categoryarray': hourly_df['hour_label'].tolist()}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

    # Live Heart Rate Chart
    st.subheader("Live Heart Rate - Last Hour")

    df = load_merged_data()

    if not df.empty:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        last_hour = df[df["timestamp"] > one_hour_ago]

        if not last_hour.empty:
            last_hour_sorted = last_hour.sort_values("timestamp")
            last_hour_sorted["bpm_smooth"] = last_hour_sorted["bpm"].rolling(window=8, center=True).mean()

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm"],
                mode="lines",
                line=dict(color="lightgray", width=1),
                opacity=0.3,
                showlegend=False
            ))

            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm_smooth"],
                mode="lines",
                name="Heart Rate",
                line=dict(color="red", width=3),
                fill="tozeroy",
                fillcolor="rgba(255, 0, 0, 0.1)"
            ))

            fig.add_hline(
                y=m["rhr"],
                line_dash="dash",
                line_color="green",
                annotation_text=f"Resting HR ({m['rhr']} BPM)"
            )

            fig.update_layout(height=400, xaxis_title="Time", yaxis_title="BPM", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current HR", f"{last_hour['bpm'].iloc[-1]} BPM")
            with col2:
                st.metric("Avg (Last Hour)", f"{int(last_hour['bpm'].mean())} BPM")
            with col3:
                st.metric("Max (Last Hour)", f"{last_hour['bpm'].max()} BPM")

# ============================================================================
# TAB 3: SLEEP ANALYSIS
# ============================================================================

with tabs[2]:
    st.header("Sleep Analysis")

    m = get_metrics()

    # Sleep Performance Score (prominent display)
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=m["sleep_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "<b>Sleep Performance Score</b>"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "lightyellow"},
                    {'range': [75, 100], 'color': "lightgreen"}
                ]
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if m["sleep_score"] >= 80:
            st.success("**Excellent Sleep**")
        elif m["sleep_score"] >= 65:
            st.info("**Good Sleep**")
        elif m["sleep_score"] >= 50:
            st.warning("**Fair Sleep**")
        else:
            st.error("**Poor Sleep**")

        st.write(f"**Duration:** {m['sleep_duration']}")
        st.write(f"**Efficiency:** {m['efficiency']}")

    with col3:
        st.write("**Sleep Stages:**")
        st.write(f"Deep: {m['deep']}")
        st.write(f"REM: {m['rem']}")
        st.write(f"Light: {m['light']}")

    st.divider()

    # Sleep Stages Breakdown
    st.subheader("Sleep Stages Breakdown")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Pie chart of sleep stages
        deep_hours = m["deep_hours"]
        rem_hours = m["rem_hours"]
        light_hours = m["light_hours"]

        fig = go.Figure(data=[go.Pie(
            labels=['Deep', 'REM', 'Light'],
            values=[deep_hours, rem_hours, light_hours],
            hole=.3,
            marker_colors=['darkblue', 'purple', 'lightblue']
        )])
        fig.update_layout(title="Sleep Stage Distribution", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Target vs Actual:**")
        st.write(f"Deep Sleep: {m['deep']}")
        st.caption("Target: 1.5-2.5 hours")

        st.write(f"REM Sleep: {m['rem']}")
        st.caption("Target: 1.5-2.5 hours")

        st.write(f"Light Sleep: {m['light']}")
        st.caption("Variable")

        # Sleep quality indicators
        if deep_hours >= 1.5 and rem_hours >= 1.5:
            st.success("Sleep stage targets met")
        else:
            st.warning("Sleep stages below optimal")

    st.divider()

    # Sleep Consistency & Recommendations (placeholder for future implementation)
    st.subheader("Sleep Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.info("**Sleep Consistency Score**\n\nTrack for 7+ days to see your sleep consistency analysis")

    with col2:
        st.info("**Optimal Bedtime**\n\nBased on your best recovery days, we'll recommend your optimal bedtime")

    # SpO2 during sleep
    if m["spo2_data"]:
        st.divider()
        st.subheader("Blood Oxygen During Sleep")
        spo2 = m["spo2_data"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg SpO2 (Sleep)", f"{spo2['avg']}%")
        with col2:
            st.metric("Lowest SpO2", f"{spo2['min']}%")
        with col3:
            if spo2['min'] < 90:
                st.error("Low oxygen detected")
            else:
                st.success("Normal levels")

# ============================================================================
# TAB 4: WORKOUTS
# ============================================================================

with tabs[3]:
    st.header("Workout Analysis")

    m = get_metrics()

    # Auto-detected workouts
    workouts = m["workouts"]

    if workouts:
        st.subheader("Auto-Detected Workouts")
        st.caption("Workouts detected from elevated heart rate periods")

        for i, workout in enumerate(workouts, 1):
            with st.expander(f"Workout #{i} - {workout['intensity']} Intensity"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Start Time", workout['start'].strftime("%H:%M"))
                with col2:
                    st.metric("Duration", f"{workout['duration_min']} min")
                with col3:
                    st.metric("Avg HR", f"{workout['avg_hr']} BPM")
                with col4:
                    st.metric("Max HR", f"{workout['max_hr']} BPM")

                # Option to tag workout type
                st.write("**Tag this workout:**")
                workout_types = ["Run", "Bike", "Lift", "Swim", "Walk", "HIIT", "Yoga", "Other"]
                selected_type = st.selectbox(
                    "Activity Type",
                    workout_types,
                    key=f"workout_type_{i}"
                )

                if st.button(f"Save Type", key=f"save_workout_{i}"):
                    activity_log = load_activity_log()
                    workout_key = workout['start'].strftime("%Y-%m-%d %H:%M")
                    activity_log[workout_key] = selected_type
                    save_activity_log(activity_log)
                    st.success(f"Saved as {selected_type}!")
    else:
        st.info("No workouts detected today. Workouts are automatically detected when your heart rate is elevated for 10+ minutes.")

    st.divider()

    # Activity Log Summary
    st.subheader("Activity Log")

    activity_log = load_activity_log()
    if activity_log:
        # Convert to DataFrame
        log_data = []
        for timestamp, activity_type in activity_log.items():
            log_data.append({"Date/Time": timestamp, "Activity": activity_type})

        log_df = pd.DataFrame(log_data)
        st.dataframe(log_df, use_container_width=True)

        # Activity type distribution
        activity_counts = log_df['Activity'].value_counts()

        fig = go.Figure(data=[
            go.Bar(x=activity_counts.index, y=activity_counts.values, marker_color='teal')
        ])
        fig.update_layout(title="Activity Type Distribution", xaxis_title="Activity", yaxis_title="Count", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activities logged yet. Tag your workouts above to build your activity log!")

# ============================================================================
# TAB 5: TRENDS & ANALYTICS
# ============================================================================

with tabs[4]:
    st.header("Trends & Analytics")

    history_df = load_history()

    if not history_df.empty:
        # Time range filter
        col1, col2 = st.columns([1, 3])

        with col1:
            time_range = st.selectbox(
                "Time Range",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
            )

        # Filter data
        if time_range != "All Time":
            days = int(time_range.split()[1])
            cutoff = datetime.now().date() - timedelta(days=days)
            filtered_df = history_df[history_df["date"] >= cutoff]
        else:
            filtered_df = history_df

        # Weekly Summary Report
        if datetime.now().weekday() == 6:  # Sunday
            st.info("**Weekly Summary** - Your training overview for the week")

        st.subheader("Weekly Strain vs Recovery")

        if len(filtered_df) >= 7:
            weekly_df = filtered_df.tail(7)

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Bar(x=weekly_df['date'].astype(str), y=weekly_df['strain'], name="Strain", marker_color='cyan'),
                secondary_y=False
            )

            fig.add_trace(
                go.Scatter(x=weekly_df['date'].astype(str), y=weekly_df['recovery'], name="Recovery",
                          line=dict(color='green', width=3), mode='lines+markers'),
                secondary_y=True
            )

            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Strain (0-21)", secondary_y=False)
            fig.update_yaxes(title_text="Recovery (%)", secondary_y=True)
            fig.update_layout(height=500, title="7-Day Strain vs Recovery")

            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Monthly Trends Comparison
        st.subheader("Monthly Trends Comparison")

        if len(history_df) >= 30:
            # Get last 30 days and previous 30 days
            last_30 = history_df.tail(30)
            prev_30 = history_df.iloc[-60:-30] if len(history_df) >= 60 else pd.DataFrame()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                current_avg_recovery = last_30['recovery'].mean()
                prev_avg_recovery = prev_30['recovery'].mean() if not prev_30.empty else current_avg_recovery
                delta_recovery = current_avg_recovery - prev_avg_recovery
                st.metric("Avg Recovery", f"{current_avg_recovery:.1f}%", delta=f"{delta_recovery:+.1f}%")

            with col2:
                current_avg_strain = last_30['strain'].mean()
                prev_avg_strain = prev_30['strain'].mean() if not prev_30.empty else current_avg_strain
                delta_strain = current_avg_strain - prev_avg_strain
                st.metric("Avg Strain", f"{current_avg_strain:.1f}", delta=f"{delta_strain:+.1f}")

            with col3:
                current_avg_hrv = last_30['hrv'].mean()
                prev_avg_hrv = prev_30['hrv'].mean() if not prev_30.empty else current_avg_hrv
                delta_hrv = current_avg_hrv - prev_avg_hrv
                st.metric("Avg HRV", f"{current_avg_hrv:.1f} ms", delta=f"{delta_hrv:+.1f} ms")

            with col4:
                current_avg_rhr = last_30['rhr'].mean()
                prev_avg_rhr = prev_30['rhr'].mean() if not prev_30.empty else current_avg_rhr
                delta_rhr = current_avg_rhr - prev_avg_rhr
                st.metric("Avg RHR", f"{current_avg_rhr:.1f} BPM", delta=f"{delta_rhr:+.1f}", delta_color="inverse")

        st.divider()

        # RHR & HRV Trends
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("RHR Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered_df['date'].astype(str),
                y=filtered_df['rhr'],
                mode='lines+markers',
                line=dict(color='red', width=2),
                name='RHR'
            ))
            # Add trend line
            if len(filtered_df) > 1:
                z = np.polyfit(range(len(filtered_df)), filtered_df['rhr'], 1)
                p = np.poly1d(z)
                fig.add_trace(go.Scatter(
                    x=filtered_df['date'].astype(str),
                    y=p(range(len(filtered_df))),
                    mode='lines',
                    line=dict(color='pink', dash='dash'),
                    name='Trend'
                ))
            fig.update_layout(height=400, yaxis_title="RHR (BPM)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Interpretation
            if len(filtered_df) > 1:
                if z[0] < -0.1:
                    st.success("RHR decreasing - fitness improving")
                elif z[0] > 0.1:
                    st.warning("RHR increasing - may need more recovery")
                else:
                    st.info("RHR is stable")

        with col2:
            st.subheader("HRV Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered_df['date'].astype(str),
                y=filtered_df['hrv'],
                mode='lines+markers',
                line=dict(color='green', width=2),
                name='HRV'
            ))
            # Add trend line
            if len(filtered_df) > 1:
                z = np.polyfit(range(len(filtered_df)), filtered_df['hrv'], 1)
                p = np.poly1d(z)
                fig.add_trace(go.Scatter(
                    x=filtered_df['date'].astype(str),
                    y=p(range(len(filtered_df))),
                    mode='lines',
                    line=dict(color='lightgreen', dash='dash'),
                    name='Trend'
                ))
            fig.update_layout(height=400, yaxis_title="HRV (ms)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Interpretation
            if len(filtered_df) > 1:
                if z[0] > 0.5:
                    st.success("HRV increasing - great adaptation")
                elif z[0] < -0.5:
                    st.warning("HRV decreasing - may be overtrained")
                else:
                    st.info("HRV is stable")

        st.divider()

        # Individual metric selector
        st.subheader("Individual Metric Analysis")

        metric = st.selectbox(
            "Select Metric",
            ["recovery", "strain", "rhr", "hrv", "stress", "readiness", "steps"],
            index=0
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filtered_df['date'].astype(str),
            y=filtered_df[metric],
            mode='lines+markers',
            line=dict(width=3),
            fill='tozeroy'
        ))

        y_labels = {
            "recovery": "Recovery (%)",
            "strain": "Strain (0-21)",
            "rhr": "RHR (BPM)",
            "hrv": "HRV (ms)",
            "stress": "Stress (0-10)",
            "readiness": "Readiness (%)",
            "steps": "Steps"
        }

        fig.update_layout(
            title=f"{metric.capitalize()} Over Time",
            xaxis_title="Date",
            yaxis_title=y_labels.get(metric, metric.capitalize()),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average", f"{filtered_df[metric].mean():.1f}")
        with col2:
            st.metric("Minimum", f"{filtered_df[metric].min():.1f}")
        with col3:
            st.metric("Maximum", f"{filtered_df[metric].max():.1f}")
        with col4:
            st.metric("Std Dev", f"{filtered_df[metric].std():.1f}")

    else:
        st.info("No historical data yet. Click 'Refresh Data' in the Dashboard to start tracking!")

# ============================================================================
# TAB 6: ACHIEVEMENTS & RECORDS
# ============================================================================

with tabs[5]:
    st.header("Achievements & Personal Records")

    m = get_metrics()

    # Achievements
    st.subheader("Your Achievements")

    achievements = m["achievements"]

    if achievements:
        cols = st.columns(3)
        for i, achievement in enumerate(achievements):
            with cols[i % 3]:
                st.success(f"**{achievement['name']}**\n\n{achievement['description']}")
    else:
        st.info("Keep tracking to unlock achievements")

    st.divider()

    # Personal Records
    st.subheader("Personal Records")

    records = m["personal_records"]

    if records:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Performance Records:**")
            st.metric("Best Recovery", f"{records.get('best_recovery', 'N/A')}%")
            st.caption(f"Date: {records.get('best_recovery_date', 'N/A')}")

            st.metric("Highest HRV", f"{records.get('highest_hrv', 'N/A')} ms")
            st.caption(f"Date: {records.get('highest_hrv_date', 'N/A')}")

            st.metric("Lowest RHR", f"{records.get('lowest_rhr', 'N/A')} BPM")
            st.caption(f"Date: {records.get('lowest_rhr_date', 'N/A')}")

        with col2:
            st.write("**Activity Records:**")
            st.metric("Max Strain", f"{records.get('max_strain', 'N/A')}")
            st.caption(f"Date: {records.get('max_strain_date', 'N/A')}")

            if 'max_steps' in records:
                st.metric("Max Steps", f"{records.get('max_steps', 'N/A'):,}")
                st.caption(f"Date: {records.get('max_steps_date', 'N/A')}")
    else:
        st.info("Track for a few days to establish your personal records!")

# ============================================================================
# TAB 7: JOURNAL
# ============================================================================

with tabs[6]:
    st.header("Daily Journal")

    # Load existing journals
    journal = load_journal()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Today's entry
    st.subheader("Today's Entry")

    existing_entry = journal.get(today_str, "")

    col1, col2 = st.columns([3, 1])

    with col1:
        journal_text = st.text_area(
            "How are you feeling? Any notes about your training, sleep, or recovery?",
            value=existing_entry,
            height=150,
            key="journal_entry"
        )

    with col2:
        if st.button("Save Entry", use_container_width=True):
            journal[today_str] = journal_text
            save_journal(journal)
            st.success("Saved")

        if st.button("Clear", use_container_width=True):
            if today_str in journal:
                del journal[today_str]
                save_journal(journal)
                st.rerun()

    st.divider()

    # Cycle Tracking (for menstrual cycle)
    st.subheader("Cycle Tracking")

    with st.expander("Menstrual Cycle Tracker"):
        st.write("Track your cycle to see how it affects your training and recovery.")

        col1, col2, col3 = st.columns(3)

        with col1:
            cycle_start = st.date_input("Cycle Start Date")

        with col2:
            cycle_day = st.number_input("Current Cycle Day", min_value=1, max_value=40, value=1)

        with col3:
            cycle_phase = st.selectbox("Phase", ["Menstrual", "Follicular", "Ovulation", "Luteal"])

        if st.button("Save Cycle Info"):
            # Save to journal with special prefix
            cycle_key = f"cycle_{today_str}"
            journal[cycle_key] = {
                "start_date": str(cycle_start),
                "day": cycle_day,
                "phase": cycle_phase
            }
            save_journal(journal)
            st.success("Cycle info saved!")

    st.divider()

    # Previous entries
    st.subheader("Previous Entries")

    # Filter out cycle entries and sort by date (most recent first)
    regular_entries = {k: v for k, v in journal.items() if not k.startswith("cycle_")}
    sorted_entries = sorted(regular_entries.items(), key=lambda x: x[0], reverse=True)

    if sorted_entries:
        for date_str, entry in sorted_entries[:7]:  # Show last 7 entries
            if entry:  # Only show non-empty entries
                with st.expander(f"{date_str}"):
                    st.write(entry)
    else:
        st.info("No previous entries yet")

# ============================================================================
# TAB 8: BODY METRICS
# ============================================================================

with tabs[7]:
    st.header("Body Metrics & Metabolism")

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

    # User Profile Form
    with st.form("user_profile_form"):
        st.write("**Enter your information:**")

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age (years)",
                min_value=10,
                max_value=120,
                value=profile["age"] if profile else 30,
                step=1
            )

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
            sex = st.selectbox(
                "Sex",
                ["Male", "Female"],
                index=0 if (profile and profile["sex"] == "Male") else 0
            )

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

        submitted = st.form_submit_button("Calculate & Save")

    # Save Profile & Update History
    if submitted:
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
                existing_history.loc[existing_history["date"] == today_date, "weight_kg"] = weight_kg
                existing_history.to_csv(history_path, index=False)
            else:
                new_entry = pd.DataFrame({
                    "date": [today_str],
                    "recovery": [m.get("recovery", 0)],
                    "strain": [m.get("strain", 0)],
                    "rhr": [m.get("rhr", 0)],
                    "hrv": [m.get("hrv", 0)],
                    "stress": [m.get("stress", 0)],
                    "readiness": [m.get("readiness", 0)],
                    "steps": [m.get("steps", 0)],
                    "weight_kg": [weight_kg],
                    "sleep_duration_hours": [m.get("sleep_duration_hours", 0)]
                })
                combined = pd.concat([existing_history, new_entry])
                combined.to_csv(history_path, index=False)
        else:
            new_entry = pd.DataFrame({
                "date": [today_str],
                "recovery": [m.get("recovery", 0)],
                "strain": [m.get("strain", 0)],
                "rhr": [m.get("rhr", 0)],
                "hrv": [m.get("hrv", 0)],
                "stress": [m.get("stress", 0)],
                "readiness": [m.get("readiness", 0)],
                "steps": [m.get("steps", 0)],
                "weight_kg": [weight_kg],
                "sleep_duration_hours": [m.get("sleep_duration_hours", 0)]
            })
            new_entry.to_csv(history_path, index=False)

        st.cache_data.clear()
        st.success("Profile saved successfully")
        st.rerun()

    # Display Results
    if profile:
        st.divider()

        bmi = calculate_bmi(profile["weight_kg"], profile["height_cm"])
        bmi_category, bmi_color = get_bmi_category(bmi)
        bmr = calculate_bmr(profile["weight_kg"], profile["height_cm"], profile["age"], profile["sex"])
        tdee = calculate_tdee(bmr, profile.get("activity_minutes_per_week"), profile.get("avg_steps_per_day"))

        st.subheader("Your Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("BMI", f"{bmi:.1f}", delta=bmi_category,
                     help="Body Mass Index: Weight-to-height ratio calculated as weight_kg / (height_m)². Categories: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30). Note: BMI doesn't account for muscle mass, bone density, or body composition. Athletes with high muscle mass may have elevated BMI despite being healthy.")

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

        with col2:
            st.metric("BMR", f"{int(bmr)} cal/day",
                     help="Basal Metabolic Rate: Calories burned at complete rest using Mifflin-St Jeor equation. For males: (10×weight_kg) + (6.25×height_cm) - (5×age) + 5. For females: same - 161. This is your baseline energy expenditure for vital functions (breathing, circulation, cell production). Accounts for ~60-70% of total daily calories.")
            st.write("")
            st.caption(f"Weight: **{profile['weight_kg']:.1f} kg** / **{kg_to_lbs(profile['weight_kg']):.1f} lbs**")
            st.caption(f"Height: **{profile['height_cm']:.1f} cm** / **{cm_to_inches(profile['height_cm']):.1f} in**")

        with col3:
            st.metric("TDEE", f"{int(tdee)} cal/day",
                     help="Total Daily Energy Expenditure: Total calories burned per day = BMR × activity factor. Activity factor calculated from daily steps or weekly exercise minutes: Sedentary (<3000 steps): 1.2×BMR, Lightly Active (3000-5000): 1.375×BMR, Moderately Active (5000-7500): 1.55×BMR, Very Active (7500-10000): 1.725×BMR, Extremely Active (>10000): 1.9×BMR. This is your maintenance calorie level.")
            st.write("")
            st.success("**Total Daily Energy Expenditure** including all activity")

        # Calorie Breakdown
        st.divider()
        st.subheader("Calorie Breakdown")

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
                st.info(f"**{level}** ({steps:,} steps/day)")

        # Weight Tracking Chart
        history_df = load_history()
        if not history_df.empty and "weight_kg" in history_df.columns:
            weight_data = history_df[history_df["weight_kg"].notna()]

            if len(weight_data) > 1:
                st.divider()
                st.subheader("Weight Trend")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=weight_data['date'].astype(str),
                    y=weight_data['weight_kg'],
                    mode='lines+markers',
                    line=dict(color='purple', width=3),
                    fill='tozeroy'
                ))
                fig.update_layout(height=400, xaxis_title="Date", yaxis_title="Weight (kg)")
                st.plotly_chart(fig, use_container_width=True)

                first_weight = weight_data['weight_kg'].iloc[0]
                last_weight = weight_data['weight_kg'].iloc[-1]
                weight_change = last_weight - first_weight

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Starting", f"{first_weight:.1f} kg ({kg_to_lbs(first_weight):.1f} lbs)")
                with col2:
                    st.metric("Current", f"{last_weight:.1f} kg ({kg_to_lbs(last_weight):.1f} lbs)")
                with col3:
                    st.metric("Change", f"{weight_change:+.1f} kg ({kg_to_lbs(abs(weight_change)):+.1f} lbs)")
    else:
        st.info("Fill out the form above to calculate your metrics")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Cheap WHOOP Pro v2.0 - Professional fitness tracking")
st.caption("Track daily for optimal insights and accuracy")
