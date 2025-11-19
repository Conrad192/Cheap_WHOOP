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
from strain_coach import get_strain_recommendation, get_smart_strain_goal
from workout_detector import detect_workouts, load_workouts, save_workout, calculate_hr_zones, get_zone_distribution
from alerts import check_overtraining_risk, should_rest_today, get_recovery_forecast
from insights import get_weekly_summary, get_monthly_insights, get_optimal_bedtime, get_day_strain_breakdown, calculate_calorie_burn
from nutrition import get_water_goal, log_water, log_calories, get_nutrition_summary, load_nutrition_log
from journal import add_entry, get_entries, get_all_entries, find_correlations, COMMON_TAGS
from reports import generate_pdf_report, export_csv
import numpy as np

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "❤️ Heart Data",
    "😴 Sleep",
    "📈 History",
    "⚖️ BMI & Metabolism",
    "🏃 Workouts",
    "🍎 Nutrition",
    "📝 Journal"
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
    # STRAIN COACH - New Feature
    # ========================================================================
    st.divider()
    st.subheader("🎯 Strain Coach")

    history_df = load_history()

    # Set strain goal
    col1, col2 = st.columns(2)
    with col1:
        if len(history_df) >= 3:
            recent_strains = history_df.tail(7)["strain"].tolist()
            suggested_goal = get_smart_strain_goal(m["recovery"], recent_strains)
        else:
            suggested_goal = 14

        strain_goal = st.slider("Today's Strain Goal", 7, 21, suggested_goal,
                                help="What strain do you want to hit today?")

    with col2:
        st.metric("Current Strain", f"{m['strain']:.1f}", f"Goal: {strain_goal}")

    # Get recommendation
    recommendation = get_strain_recommendation(m["strain"], strain_goal)

    if recommendation["status"] == "goal_met":
        st.success(recommendation["message"])
    else:
        st.info(recommendation["message"])

        if recommendation["recommendations"]:
            st.write("**Suggested activities to hit your goal:**")
            for rec in recommendation["recommendations"][:3]:
                st.write(f"• **{rec['activity']}**: {rec['duration_min']} minutes (+{rec['strain_gain']:.1f} strain)")

    # ========================================================================
    # REST DAY RECOMMENDATION - New Feature
    # ========================================================================
    st.divider()
    st.subheader("🛑 Rest Day Check")

    if len(history_df) >= 3:
        yesterday_strain = history_df.iloc[-1]["strain"] if len(history_df) > 0 else 0
        recent_recoveries = history_df.tail(3)["recovery"].tolist()

        rest_check = should_rest_today(m["recovery"], yesterday_strain, recent_recoveries)

        if rest_check["should_rest"]:
            if rest_check["urgency"] == "high":
                st.error(rest_check["message"])
            else:
                st.warning(rest_check["message"])
        else:
            st.success(rest_check["message"])

        st.caption(f"_{rest_check['reason']}_")
        st.write(f"💡 {rest_check['suggestion']}")
    else:
        st.info("Track for 3+ days to get rest day recommendations")

    # ========================================================================
    # RECOVERY PREDICTION - New Feature
    # ========================================================================
    if len(history_df) >= 7:
        st.divider()
        st.subheader("🔮 Recovery Forecast")

        recent_strains = history_df.tail(14)["strain"].tolist()
        recent_recoveries = history_df.tail(14)["recovery"].tolist()

        predicted_recovery = get_recovery_forecast(recent_strains, recent_recoveries)

        if predicted_recovery:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Today's Recovery", f"{m['recovery']}%")
            with col2:
                st.metric("Predicted Tomorrow", f"{predicted_recovery}%",
                         delta=f"{predicted_recovery - m['recovery']:+.0f}%")

            st.caption(f"Based on today's strain ({m['strain']:.1f}) and your recent patterns")

    # ========================================================================
    # OVERTRAINING RISK ALERT - New Feature
    # ========================================================================
    if len(history_df) >= 7:
        st.divider()
        st.subheader("⚠️ Overtraining Risk Assessment")

        risk_assessment = check_overtraining_risk(history_df)

        if risk_assessment["risk_level"] == "high":
            st.error(risk_assessment["message"])
        elif risk_assessment["risk_level"] == "moderate":
            st.warning(risk_assessment["message"])
        else:
            st.success(risk_assessment["message"])

        with st.expander("📊 See Details"):
            st.write("**Recent Stats:**")
            for key, value in risk_assessment["stats"].items():
                st.write(f"• {key.replace('_', ' ').title()}: {value}")

            if risk_assessment["recommendations"]:
                st.write("\n**Recommendations:**")
                for rec in risk_assessment["recommendations"]:
                    st.write(f"• {rec}")
    
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

    # ========================================================================
    # WEEKLY PERFORMANCE SUMMARY - New Feature
    # ========================================================================
    if len(history_df) >= 7:
        st.subheader("📅 Weekly Performance Summary")

        weekly = get_weekly_summary(history_df)

        if weekly:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Strain", f"{weekly['total_strain']:.1f}",
                         delta=f"{weekly['wow_strain_change']:+.1f} vs last week")
            with col2:
                st.metric("Avg Recovery", f"{weekly['avg_recovery']:.1f}%",
                         delta=f"{weekly['wow_recovery_change']:+.1f}% vs last week")
            with col3:
                st.metric("Avg HRV", f"{weekly['avg_hrv']:.1f} ms")
            with col4:
                st.metric("Total Steps", f"{weekly['total_steps']:,}",
                         delta=f"{weekly['wow_steps_change']:+,} vs last week")

            if weekly["best_day"] and weekly["worst_day"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"**Best Day:** {weekly['best_day']['date']} ({weekly['best_day']['recovery']}% recovery)")
                with col2:
                    st.error(f"**Worst Day:** {weekly['worst_day']['date']} ({weekly['worst_day']['recovery']}% recovery)")

        st.divider()

    # ========================================================================
    # MONTHLY TRENDS & INSIGHTS - New Feature
    # ========================================================================
    if len(history_df) >= 30:
        st.subheader("📊 Monthly Insights (Last 30 Days)")

        monthly = get_monthly_insights(history_df)

        if monthly:
            st.info(monthly["message"])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Avg Recovery", f"{monthly['avg_recovery']:.1f}%",
                         delta=f"{monthly.get('mom_recovery_change', 0):+.1f}% vs prev month")
            with col2:
                st.metric("Avg Strain", f"{monthly['avg_strain']:.1f}")
            with col3:
                st.metric("Avg HRV", f"{monthly['avg_hrv']:.1f} ms",
                         delta=f"{monthly.get('mom_hrv_change', 0):+.1f} ms vs prev month")

            st.caption(f"📅 {monthly['days_tracked']} days tracked this month")

        st.divider()

    # ========================================================================
    # OPTIMAL BEDTIME RECOMMENDATION - New Feature
    # ========================================================================
    if len(history_df) >= 7:
        bedtime_rec = get_optimal_bedtime(history_df)

        st.info(f"💤 **Optimal Bedtime:** {bedtime_rec['bedtime']} - {bedtime_rec['reason']}")

        st.divider()

    # ========================================================================
    # EXPORT & PDF REPORT - New Feature
    # ========================================================================
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Generate PDF Report"):
            user_profile = load_user_profile()

            if user_profile and len(history_df) >= 7:
                with st.spinner("Generating PDF..."):
                    result = generate_pdf_report(history_df, user_profile)

                    if result["success"]:
                        st.success(f"✅ PDF generated: {result['path']}")

                        # Offer download
                        with open(result["path"], "rb") as f:
                            st.download_button(
                                "⬇️ Download PDF",
                                f,
                                file_name="cheap_whoop_report.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error(f"❌ {result['error']}")
            else:
                st.warning("Need user profile and 7+ days of data")

    with col2:
        if st.button("📊 Export CSV"):
            if not history_df.empty:
                result = export_csv(history_df)

                if result["success"]:
                    st.success(f"✅ Exported {result['rows']} rows")

                    # Offer download
                    csv_data = history_df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download CSV",
                        csv_data,
                        file_name="cheap_whoop_history.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No data to export")

    st.divider()

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
# TAB 5: WORKOUTS - New Feature
# ============================================================================

with tab5:
    st.subheader("🏃 Workout Auto-Detection")

    # Auto-detect workouts from today's data
    df = load_merged_data()
    m = get_metrics()

    if not df.empty:
        if st.button("🔍 Detect Workouts from Today's Data"):
            with st.spinner("Analyzing heart rate data..."):
                workouts = detect_workouts(df, m["rhr"])

                if workouts:
                    st.success(f"✅ Detected {len(workouts)} workout(s)!")

                    for workout in workouts:
                        save_workout(workout)

                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.info("No workouts detected (need HR elevated 20+ BPM above resting for 10+ min)")

    st.divider()

    # Display all workouts
    st.subheader("📋 Workout History")

    all_workouts = load_workouts()

    if all_workouts:
        # Show today's workouts
        today = datetime.now().strftime("%Y-%m-%d")
        today_workouts = [w for w in all_workouts if w["date"] == today]

        if today_workouts:
            st.write("**Today's Workouts:**")
            for i, w in enumerate(today_workouts, 1):
                with st.expander(f"Workout {i}: {w['start_time']} - {w['end_time']} ({w['duration_min']} min)"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Duration", f"{w['duration_min']} min")
                    with col2:
                        st.metric("Avg HR", f"{w['avg_hr']} BPM")
                    with col3:
                        st.metric("Max HR", f"{w['max_hr']} BPM")

                    st.write(f"**Strain:** {w['strain']:.1f}")

                    if w.get("auto_detected"):
                        st.caption("🤖 Auto-detected")

        st.divider()

        # Show all workouts in table
        st.write("**All Workouts:**")
        workout_df = pd.DataFrame(all_workouts)
        workout_df = workout_df.sort_values("date", ascending=False)

        st.dataframe(workout_df[["date", "start_time", "duration_min", "avg_hr", "max_hr", "strain"]],
                    use_container_width=True)

        # Summary stats
        st.divider()
        st.subheader("📊 Workout Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Workouts", len(all_workouts))
        with col2:
            total_duration = sum(w["duration_min"] for w in all_workouts)
            st.metric("Total Time", f"{total_duration} min")
        with col3:
            total_strain = sum(w["strain"] for w in all_workouts)
            st.metric("Total Strain", f"{total_strain:.1f}")
    else:
        st.info("No workouts logged yet. Use 'Detect Workouts' button above or refresh data in Heart Data tab.")

    # ========================================================================
    # HR ZONES DURING WORKOUTS - New Feature
    # ========================================================================
    st.divider()
    st.subheader("💓 Heart Rate Zones")

    user_profile = load_user_profile()
    age = user_profile["age"] if user_profile else 30

    max_hr = 220 - age

    st.write(f"**Based on your max HR ({max_hr} BPM):**")

    zones_data = [
        ["Zone 1 (Recovery)", f"{int(max_hr * 0.5)}-{int(max_hr * 0.6)} BPM", "50-60% max HR", "Easy recovery"],
        ["Zone 2 (Endurance)", f"{int(max_hr * 0.6)}-{int(max_hr * 0.7)} BPM", "60-70% max HR", "Build base fitness"],
        ["Zone 3 (Tempo)", f"{int(max_hr * 0.7)}-{int(max_hr * 0.8)} BPM", "70-80% max HR", "Improve efficiency"],
        ["Zone 4 (Threshold)", f"{int(max_hr * 0.8)}-{int(max_hr * 0.9)} BPM", "80-90% max HR", "Race pace"],
        ["Zone 5 (Maximum)", f"{int(max_hr * 0.9)}+ BPM", "90-100% max HR", "Max effort"]
    ]

    zones_df = pd.DataFrame(zones_data, columns=["Zone", "Heart Rate", "% of Max", "Purpose"])
    st.table(zones_df)

# ============================================================================
# TAB 6: NUTRITION - New Feature
# ============================================================================

with tab6:
    st.subheader("🍎 Nutrition & Hydration Tracking")

    m = get_metrics()
    today = datetime.now().strftime("%Y-%m-%d")

    # Get nutrition summary for today
    nutrition = get_nutrition_summary(today)

    # ========================================================================
    # HYDRATION TRACKING
    # ========================================================================
    st.subheader("💧 Hydration")

    # Calculate water goal based on strain
    water_goal = get_water_goal(m["strain"])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Today's Water", f"{nutrition['water_oz']} oz")
        st.caption(f"{nutrition['water_ml']} ml")

    with col2:
        st.metric("Goal", f"{water_goal['oz']} oz")
        st.caption(f"{water_goal['ml']} ml ({water_goal['glasses']} glasses)")

    # Progress bar
    progress = min(1.0, nutrition['water_oz'] / water_goal['oz'])
    st.progress(progress)

    # Log water
    col1, col2 = st.columns(2)

    with col1:
        water_to_add = st.number_input("Add Water (oz)", min_value=0, max_value=64, value=8, step=4)

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("➕ Log Water"):
            log_water(water_to_add, today)
            st.success(f"Added {water_to_add} oz!")
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # ========================================================================
    # CALORIE TRACKING
    # ========================================================================
    st.subheader("🔥 Calorie Tracking")

    user_profile = load_user_profile()

    if user_profile:
        # Calculate calorie burn
        bmr = calculate_bmr(user_profile["weight_kg"], user_profile["height_cm"],
                           user_profile["age"], user_profile["sex"])

        calories = calculate_calorie_burn(bmr, m["strain"], m["steps"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Calories Burned", f"{calories['total']} cal")
            st.caption("Total for today")

        with col2:
            st.metric("BMR", f"{calories['base_bmr']} cal")
            st.caption("At rest")

        with col3:
            st.metric("Activity", f"{calories['activity']} cal")
            st.caption("From movement")

        st.divider()

        # Log calories consumed
        st.write("**Log Food:**")

        col1, col2 = st.columns(2)

        with col1:
            meal_name = st.text_input("Meal Description", placeholder="e.g., Breakfast, Lunch, Snack")

        with col2:
            calories_consumed = st.number_input("Calories", min_value=0, max_value=3000, value=0, step=50)

        if st.button("➕ Log Meal"):
            if calories_consumed > 0:
                log_calories(calories_consumed, meal_name, today)
                st.success(f"Logged {calories_consumed} cal!")
                st.cache_data.clear()
                st.rerun()

        st.divider()

        # Show today's meals
        if nutrition['meals']:
            st.write("**Today's Meals:**")
            for meal in nutrition['meals']:
                st.write(f"• **{meal['time']}** - {meal['meal']}: {meal['calories']} cal")

        # Summary
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Calories In", f"{nutrition['calories']} cal")

        with col2:
            st.metric("Calories Out", f"{calories['total']} cal")

        with col3:
            net = nutrition['calories'] - calories['total']
            st.metric("Net", f"{net:+} cal")

        if net < -500:
            st.success("✅ Good calorie deficit for weight loss")
        elif net > 500:
            st.info("💪 Calorie surplus for muscle gain")
        else:
            st.info("⚖️ Maintaining weight")
    else:
        st.warning("Set up your profile in BMI & Metabolism tab to track calories")

# ============================================================================
# TAB 7: JOURNAL - New Feature
# ============================================================================

with tab7:
    st.subheader("📝 Daily Journal")

    today = datetime.now().strftime("%Y-%m-%d")

    # ========================================================================
    # ADD JOURNAL ENTRY
    # ========================================================================
    st.write("**How are you feeling today?**")

    # Quick tag selection
    selected_tags = st.multiselect(
        "Quick Tags (optional)",
        COMMON_TAGS,
        help="Select tags to help find patterns later"
    )

    # Custom text entry
    journal_text = st.text_area(
        "Journal Entry",
        placeholder="e.g., Felt tired today, didn't sleep well...",
        height=100
    )

    if st.button("💾 Save Entry"):
        if journal_text:
            add_entry(journal_text, selected_tags, today)
            st.success("✅ Journal entry saved!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("Please write something first")

    st.divider()

    # ========================================================================
    # VIEW TODAY'S ENTRIES
    # ========================================================================
    st.subheader("📖 Today's Entries")

    today_entries = get_entries(today)

    if today_entries:
        for i, entry in enumerate(today_entries, 1):
            with st.expander(f"Entry {i} - {entry['timestamp']}"):
                st.write(entry['text'])
                if entry['tags']:
                    st.caption(f"Tags: {', '.join(entry['tags'])}")
    else:
        st.info("No entries for today yet")

    st.divider()

    # ========================================================================
    # CORRELATIONS & INSIGHTS
    # ========================================================================
    st.subheader("🔍 Pattern Analysis")

    history_df = load_history()

    if len(history_df) >= 7:
        correlations = find_correlations(history_df)

        st.info(correlations["message"])

        if correlations["correlations"]:
            st.write("**Tag Correlations with Metrics:**")

            corr_data = []
            for corr in correlations["correlations"][:10]:  # Top 10
                corr_data.append([
                    corr["tag"],
                    corr["count"],
                    f"{corr['avg_recovery']:.1f}%",
                    f"{corr['avg_strain']:.1f}"
                ])

            corr_df = pd.DataFrame(corr_data,
                                  columns=["Tag", "Times Used", "Avg Recovery", "Avg Strain"])

            st.table(corr_df)

            st.caption("💡 Use this to find patterns - e.g., 'tired' tag on low recovery days")
    else:
        st.info("Track for 7+ days to see correlations between journal entries and metrics")

    st.divider()

    # ========================================================================
    # VIEW ALL ENTRIES
    # ========================================================================
    st.subheader("📚 All Journal Entries")

    all_journal = get_all_entries()

    if all_journal:
        # Show entries by date (most recent first)
        dates = sorted(all_journal.keys(), reverse=True)

        for date in dates[:10]:  # Show last 10 days
            with st.expander(f"📅 {date}"):
                for entry in all_journal[date]["entries"]:
                    st.write(f"**{entry['timestamp']}**: {entry['text']}")
                    if entry['tags']:
                        st.caption(f"Tags: {', '.join(entry['tags'])}")
                    st.write("---")
    else:
        st.info("No journal entries yet. Start logging above!")