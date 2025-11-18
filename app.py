# Import tools
import streamlit as st
import plotly.graph_objects as go
from metrics import get_metrics
import os
from datetime import datetime, timedelta
import pandas as pd
from pull_xiaomi import generate_xiaomi_data
from pull_coospo import generate_coospo_data
from merge import merge_data

# Cache functions to speed up app
@st.cache_data(ttl=60)
def load_merged_data():
    """Load the main data file and remember it for 60 seconds"""
    try:
        return pd.read_csv("data/merged/daily_merged.csv", parse_dates=["timestamp"])
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_history():
    """Load history and remember it for 5 minutes"""
    history_path = "data/history.csv"
    if os.path.exists(history_path):
        df = pd.read_csv(history_path)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    return pd.DataFrame()

def cm_to_inches(cm):
    """Convert centimeters to inches"""
    return cm / 2.54

def inches_to_cm(inches):
    """Convert inches to centimeters"""
    return inches * 2.54

def kg_to_lbs(kg):
    """Convert kilograms to pounds"""
    return kg * 2.20462

def lbs_to_kg(lbs):
    """Convert pounds to kilograms"""
    return lbs / 2.20462

def load_user_profile():
    """Load user profile data (age, weight, height, etc.)"""
    profile_path = "data/user_profile.json"
    if os.path.exists(profile_path):
        import json
        with open(profile_path) as f:
            return json.load(f)
    return None

def save_user_profile(profile):
    """Save user profile data"""
    import json
    os.makedirs("data", exist_ok=True)
    with open("data/user_profile.json", "w") as f:
        json.dump(profile, f, indent=2)

def calculate_bmr(weight_kg, height_cm, age, sex):
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation (most accurate).
    Returns calories per day at complete rest.
    """
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return bmr

def calculate_tdee(bmr, activity_minutes_per_week=None, avg_steps_per_day=None):
    """
    Calculate Total Daily Energy Expenditure.
    Uses either activity minutes OR step count (prefers steps if both provided).
    """
    if avg_steps_per_day:
        # Steps-based calculation (more accurate)
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
        # Activity minutes-based calculation
        if activity_minutes_per_week < 30:
            activity_factor = 1.2  # Sedentary
        elif activity_minutes_per_week < 150:
            activity_factor = 1.375  # Lightly active
        elif activity_minutes_per_week < 300:
            activity_factor = 1.55  # Moderately active
        elif activity_minutes_per_week < 420:
            activity_factor = 1.725  # Very active
        else:
            activity_factor = 1.9  # Extremely active
    else:
        activity_factor = 1.2  # Default to sedentary
    
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

# Page setup
st.set_page_config(page_title="Cheap WHOOP", layout="centered")
st.title("💪 Cheap WHOOP 1")
st.caption("No $30/month. Just $75 hardware + your code.")

# Tabs with icons
tab1, tab2, tab3, tab4 = st.tabs(["❤️ Heart Data", "😴 Sleep", "📈 History", "⚖️ BMI & Metabolism"])


# ----------------------------
# TAB 1 – HEART DATA + REFRESH
# ----------------------------
with tab1:
    # Get metrics first
    m = get_metrics()
    
    # Status banner
    if m["recovery"] > 66:
        st.success("🟢 **Ready to Train** - Your body is recovered!")
    elif m["recovery"] > 33:
        st.warning("🟡 **Moderate Recovery** - Light workout recommended")
    else:
        st.error("🔴 **Rest Day** - Prioritize recovery today")
    
    # Refresh button with spinner
    if st.button("🔄 Refresh Data"):
        with st.spinner("Refreshing data..."):
            generate_xiaomi_data()
            generate_coospo_data()
            merge_data()

            # Read merged data
            daily_df = pd.read_csv("data/merged/daily_merged.csv")
            m = get_metrics()

            # Load user profile to get current weight
            profile = load_user_profile()
            current_weight = profile["weight_kg"] if profile else None

            # Build new history row with NEW metrics
            history_path = "data/history.csv"
            history_df = pd.DataFrame({
                "date": [datetime.now().strftime("%Y-%m-%d")],
                "recovery": [m["recovery"]],
                "strain": [m["strain"]],
                "rhr": [m["rhr"]],
                "hrv": [m["hrv"]],
                "stress": [m["stress"]],
                "readiness": [m["readiness"]],
                "weight_kg": [current_weight]
            })

            # Append to history cleanly
            if os.path.exists(history_path):
                old_history = pd.read_csv(history_path)
                combined = pd.concat([old_history, history_df])

                # Remove duplicates by date
                combined["date"] = pd.to_datetime(combined["date"]).dt.date
                combined = combined.drop_duplicates(subset="date", keep="last")
            else:
                combined = history_df

            # Save clean history file
            combined.to_csv(history_path, index=False)
            
            # Clear cache so new data shows
            st.cache_data.clear()
            
        st.success("Data updated and added to history!")
        st.rerun()  # Reload page to show new data

    col1, col2 = st.columns(2)

    # Strain gauge
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
            **Strain (0–21): Measures total cardiovascular load for the day.**
            
            **What it means:**
            - How much physical WORK you did today
            - Counts exercise, walking, stairs, any movement
            - NOT the same as stress (that's mental/nervous tension)
            
            **Scale:**
            - 0-7: Light day (mostly resting)
            - 7-14: Moderate activity
            - 14-21: Hard training day
            
            **Example:** A 5-mile run = strain of 15-18
            """)

    # Recovery gauge
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
            **Recovery: Based on HRV and Resting HR.**
            
            **What it means:**
            - How well you recovered OVERNIGHT
            - Purely physiological (HRV + resting heart rate)
            - Measured when you wake up
            
            **Scale:**
            - 🟢 67-100: Great recovery, ready to train
            - 🟡 34-66: Moderate, go easy
            - 🔴 0-33: Poor recovery, rest day
            
            **Not the same as Training Readiness!**
            Recovery = "Did I sleep well?"
            Readiness = "Should I work out today?"
            """)

    col_hrv, col_rhr = st.columns(2)
    with col_hrv:
        st.metric("HRV", f"{m['hrv']} ms", help="Higher HRV = better recovery.")

    with col_rhr:
        st.metric("Resting HR", f"{m['rhr']} BPM", help="Lower RHR = better fitness.")
    
    # NEW METRICS SECTION
    st.divider()
    st.subheader("🧠 Advanced Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Stress score with color coding
        stress_color = "🟢" if m["stress"] < 4 else "🟡" if m["stress"] < 7 else "🔴"
        st.metric(
            "Stress Level", 
            f"{stress_color} {m['stress']}/10",
            help="Based on HR and HRV patterns. Lower = better."
        )
        with st.expander("❓ What is Stress Level?"):
            st.write("""
            **Stress measures how tense your nervous system is RIGHT NOW.**
            
            **Not the same as Strain!**
            - You can be stressed sitting at your desk (anxiety, illness)
            - You can have low stress after a great workout (body handled it well)
            
            **Scale:**
            - 🟢 0-3: Relaxed, calm, recovered
            - 🟡 4-6: Normal daily stress
            - 🔴 7-10: High stress (overtraining, anxiety, or sick)
            
            **Example:** Stressful work meeting = high stress but low strain
            """)
    
    with col2:
        # Training readiness
        readiness_emoji = "💪" if m["readiness"] > 70 else "😐" if m["readiness"] > 40 else "😴"
        st.metric(
            "Training Readiness",
            f"{readiness_emoji} {m['readiness']}%",
            help="Combined score: Should you train hard today?"
        )
        with st.expander("❓ What is Training Readiness?"):
            st.write("""
            **Should you work out hard TODAY? This is your answer.**
            
            **Not the same as Recovery!**
            - Recovery = Did you sleep well?
            - Readiness = Considering EVERYTHING, should you train?
            
            Combines:
            - 40% Recovery (most important)
            - 25% HRV 
            - 20% Sleep quality
            - 15% Resting heart rate
            
            **Scale:**
            - 💪 70-100: GO HARD! Body is ready
            - 😐 40-69: Light/moderate workout only
            - 😴 0-39: REST DAY - your body needs it
            
            **Example:** Recovery is 80% but you only slept 4 hours → Readiness drops to 60%
            """)
    
    with col3:
        # Respiratory rate
        if m["respiratory_rate"]:
            resp_status = "Normal" if 12 <= m["respiratory_rate"] <= 20 else "Check"
            st.metric(
                "Breathing Rate",
                f"{m['respiratory_rate']} /min",
                delta=resp_status,
                help="Estimated from HRV patterns. Normal: 12-20/min"
            )
            with st.expander("❓ What is Breathing Rate?"):
                st.write("""
                **How many breaths you take per minute.**
                
                Estimated from your heart rate patterns (breathing affects HRV).
                
                **Normal range:** 12-20 breaths/min at rest
                
                **What it means:**
                - 8-12: Very relaxed, deep breathing (meditation, sleep)
                - 12-20: Normal resting rate ✅
                - 20-30: Elevated (exercise, stress, anxiety)
                - 30+: Very high (intense exercise or potential health issue)
                
                **Why it matters:** 
                - Consistently high rate at rest → check for illness or overtraining
                - Very low rate → excellent relaxation and recovery
                """)
        else:
            st.metric("Breathing Rate", "N/A", help="Need more data")
    
    # Main comparison expander
    with st.expander("🤔 Strain vs Stress? Recovery vs Readiness?"):
        st.write("""
        ### Quick Comparison Guide
        
        | Metric | Measures | Time | Question |
        |--------|----------|------|----------|
        | **Strain** | Physical work | Today | "How hard did I work?" |
        | **Stress** | Nervous tension | Now | "How tense is my body?" |
        | **Recovery** | Sleep quality | This AM | "Did I recover overnight?" |
        | **Readiness** | Training decision | Today | "Should I work out?" |
        
        ---
        
        **Example Day:**
        
        Yesterday you did a hard workout (Strain: 16) but felt great (Stress: 3).
        
        You slept 8 hours (Recovery: 88%) and feel strong this morning (Readiness: 85%).
        
        **Decision: Train hard today!** 💪
        
        ---
        
        **Another Example:**
        
        You didn't work out (Strain: 4) but had a stressful day at work (Stress: 7).
        
        You slept poorly, 5 hours (Recovery: 45%) and feel tired (Readiness: 38%).
        
        **Decision: REST today!** 😴
        """)
    
    # Compare to baseline
    st.divider()
    st.subheader("📊 Today vs. Your Baseline")
    
    history_df = load_history()
    if len(history_df) >= 7:  # Need at least a week of data
        # Calculate your average over last 30 days
        recent = history_df.tail(30)
        avg_hrv = recent["hrv"].mean()
        avg_rhr = recent["rhr"].mean()
        
        # Show comparison
        col1, col2 = st.columns(2)
        with col1:
            diff_hrv = m["hrv"] - avg_hrv
            st.metric(
                "HRV vs Baseline", 
                f"{m['hrv']} ms", 
                delta=f"{diff_hrv:+.1f} ms"
            )
        with col2:
            diff_rhr = m["rhr"] - avg_rhr
            st.metric(
                "Resting HR vs Baseline", 
                f"{m['rhr']} BPM", 
                delta=f"{diff_rhr:+.1f} BPM",
                delta_color="inverse"  # Red when higher is bad for RHR
            )
    else:
        st.info("📅 Track for 7+ days to see your baseline comparison")
    
    # NEW: Live Heart Rate Chart
    st.divider()
    st.subheader("📡 Live View - Last Hour")
    
    df = load_merged_data()
    
    if not df.empty:
        # Get data from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        last_hour = df[df["timestamp"] > one_hour_ago]
        
        if not last_hour.empty:
            # Create heart rate chart
            fig = go.Figure()
            
            # Calculate 5-minute rolling average for smoother line
            last_hour_sorted = last_hour.sort_values("timestamp")
            last_hour_sorted["bpm_smooth"] = last_hour_sorted["bpm"].rolling(window=8, center=True).mean()
            
            # Show raw data as faint background (optional)
            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm"],
                mode="lines",
                name="Raw",
                line=dict(color="lightgray", width=1),
                opacity=0.3,
                showlegend=False
            ))
            
            # Add smooth heart rate line
            fig.add_trace(go.Scatter(
                x=last_hour_sorted["timestamp"],
                y=last_hour_sorted["bpm_smooth"],
                mode="lines",
                name="Heart Rate (Smoothed)",
                line=dict(color="red", width=3),
                fill="tozeroy",
                fillcolor="rgba(255, 0, 0, 0.1)"
            ))
            
            # Add resting HR reference line
            fig.add_hline(
                y=m["rhr"], 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Resting HR ({m['rhr']} BPM)",
                annotation_position="right"
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
            
            # Show current stats
            col1, col2, col3 = st.columns(3)
            with col1:
                current_hr = last_hour["bpm"].iloc[-1]
                st.metric("Current HR", f"{current_hr} BPM")
            with col2:
                avg_hr = last_hour["bpm"].mean()
                st.metric("Avg (Last Hour)", f"{int(avg_hr)} BPM")
            with col3:
                max_hr = last_hour["bpm"].max()
                st.metric("Max (Last Hour)", f"{max_hr} BPM")
        else:
            st.info("No data in the last hour. Click refresh to generate new data!")
    else:
        st.info("No data available. Click refresh to start tracking!")

# ----------------------------
# TAB 2 – SLEEP DATA
# ----------------------------
with tab2:
    st.subheader("Sleep Analysis")
    m = get_metrics()

    sleep_data = {
        "Duration": m["sleep_duration"],
        "Deep": m["deep"],
        "REM": m["rem"],
        "Light": m["light"],
        "Efficiency": m["efficiency"]
    }

    st.table(sleep_data)

    with st.expander("What is Sleep Analysis?"):
        st.write("Sleep stages are estimated using HRV dips, HR trends, and movement.")


# ----------------------------
# TAB 3 – HISTORY TRENDS
# ----------------------------
with tab3:
    st.subheader("History Trends")
    
    history_df = load_history()
    
    if not history_df.empty:
        # Group by date (in case of duplicates)
        daily = history_df.groupby("date", as_index=False).mean()

        # Time-range filter
        filter_range = st.selectbox(
            "Time Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
        )

        if filter_range != "All Time":
            days = int(filter_range.split()[1])
            cutoff = datetime.now().date() - pd.Timedelta(days=days)
            daily = daily[daily["date"] >= cutoff]

        # Metric selection - NOW WITH NEW METRICS + WEIGHT
        metric = st.selectbox(
            "Select Metric to View",
            ["recovery", "strain", "rhr", "hrv", "stress", "readiness", "weight_kg"],
            index=0
        )

        # Convert date to string to avoid Plotly timestamp autoscaling
        daily["date_str"] = daily["date"].astype(str)

        # Plot
        fig = go.Figure()
        
        # Special handling for weight (show in kg and include conversion info)
        if metric == "weight_kg":
            # Check if weight_kg column exists (for backward compatibility)
            if "weight_kg" not in daily.columns:
                st.warning("⚠️ Weight tracking not available in your history yet.")
                st.info("To start tracking weight:\n1. Go to the **BMI & Metabolism** tab\n2. Enter your weight and save\n3. Click **🔄 Refresh Data** in the Heart Data tab\n4. Your weight will be logged to history!")
            else:
                # Filter out null weights
                daily_with_weight = daily[daily["weight_kg"].notna()]
                
                if not daily_with_weight.empty:
                    fig.add_trace(go.Scatter(
                        x=daily_with_weight["date_str"],
                        y=daily_with_weight[metric],
                        mode="lines+markers",
                        name="Weight (kg)",
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
                    
                    # Show weight change stats in BOTH units
                    first_weight = daily_with_weight["weight_kg"].iloc[0]
                    last_weight = daily_with_weight["weight_kg"].iloc[-1]
                    weight_change = last_weight - first_weight
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Starting Weight", 
                            f"{first_weight:.1f} kg",
                            help=f"{kg_to_lbs(first_weight):.1f} lbs"
                        )
                        st.caption(f"({kg_to_lbs(first_weight):.1f} lbs)")
                    with col2:
                        st.metric(
                            "Current Weight", 
                            f"{last_weight:.1f} kg",
                            help=f"{kg_to_lbs(last_weight):.1f} lbs"
                        )
                        st.caption(f"({kg_to_lbs(last_weight):.1f} lbs)")
                    with col3:
                        delta_color = "inverse" if weight_change > 0 else "normal"
                        st.metric(
                            "Total Change", 
                            f"{weight_change:+.1f} kg",
                            delta_color=delta_color
                        )
                        st.caption(f"({kg_to_lbs(weight_change):+.1f} lbs)")
                else:
                    st.info("No weight data recorded yet. Update your weight in the BMI & Metabolism tab and refresh data to start tracking.")
        else:
            fig.add_trace(go.Scatter(
                x=daily["date_str"],
                y=daily[metric],
                mode="lines+markers",
                name=metric.capitalize()
            ))
            
            # Create proper axis labels based on metric
            y_label_map = {
                "recovery": "Recovery (%)",
                "strain": "Strain (0-21)",
                "rhr": "Resting Heart Rate (BPM)",
                "hrv": "HRV (ms)",
                "stress": "Stress Level (0-10)",
                "readiness": "Training Readiness (%)"
            }
            
            y_label = y_label_map.get(metric, metric.capitalize())

            fig.update_layout(
                title=f"{metric.capitalize()} Over Time",
                xaxis_title="Date",
                yaxis_title=y_label,
                xaxis=dict(type="category")
            )

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("No history yet. Refresh in the Heart tab to start tracking.")


# ----------------------------
# TAB 4 – BMI & METABOLISM
# ----------------------------
with tab4:
    st.subheader("⚖️ Body Metrics & Metabolism Calculator")
    
    # Load existing profile if available
    profile = load_user_profile()
    
    # Unit preference toggles
    col_unit1, col_unit2 = st.columns(2)
    with col_unit1:
        height_unit = st.radio("Height Unit", ["Centimeters (cm)", "Inches (in)"], horizontal=True)
    with col_unit2:
        weight_unit = st.radio("Weight Unit", ["Kilograms (kg)", "Pounds (lbs)"], horizontal=True)
    
    use_cm = "Centimeters" in height_unit
    use_kg = "Kilograms" in weight_unit
    
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
            
            # Weight input with unit conversion
            if use_kg:
                weight_input = st.number_input(
                    "Weight (kg)", 
                    min_value=20.0, 
                    max_value=300.0, 
                    value=profile["weight_kg"] if profile else 70.0,
                    step=0.1,
                    help="1 kg = 2.2 lbs"
                )
                weight_kg = weight_input
            else:
                default_lbs = kg_to_lbs(profile["weight_kg"]) if profile else 154.0
                weight_input = st.number_input(
                    "Weight (lbs)", 
                    min_value=44.0, 
                    max_value=660.0, 
                    value=default_lbs,
                    step=0.1,
                    help="1 lb = 0.45 kg"
                )
                weight_kg = lbs_to_kg(weight_input)
            
            # Height input with unit conversion
            if use_cm:
                height_input = st.number_input(
                    "Height (cm)", 
                    min_value=100.0, 
                    max_value=250.0, 
                    value=profile["height_cm"] if profile else 170.0,
                    step=0.1,
                    help="1 inch = 2.54 cm"
                )
                height_cm = height_input
            else:
                default_inches = cm_to_inches(profile["height_cm"]) if profile else 67.0
                height_input = st.number_input(
                    "Height (inches)", 
                    min_value=39.0, 
                    max_value=98.0, 
                    value=default_inches,
                    step=0.1,
                    help="1 inch = 2.54 cm"
                )
                height_cm = inches_to_cm(height_input)
        
        with col2:
            sex = st.selectbox(
                "Sex",
                ["Male", "Female"],
                index=0 if (profile and profile["sex"] == "Male") else 0
            )
            
            st.write("**Activity Level** (choose ONE):")
            
            activity_method = st.radio(
                "How would you like to measure activity?",
                ["Average Daily Steps", "Weekly Exercise Minutes"],
                index=0 if (profile and profile.get("avg_steps_per_day")) else 0
            )
            
            if activity_method == "Average Daily Steps":
                avg_steps = st.number_input(
                    "Average steps per day",
                    min_value=0,
                    max_value=50000,
                    value=profile.get("avg_steps_per_day", 5000) if profile else 5000,
                    step=500,
                    help="Check your phone's step counter for your average"
                )
                activity_minutes = None
            else:
                activity_minutes = st.number_input(
                    "Exercise minutes per week",
                    min_value=0,
                    max_value=2000,
                    value=profile.get("activity_minutes_per_week", 150) if profile else 150,
                    step=10,
                    help="Total moderate-to-vigorous physical activity per week"
                )
                avg_steps = None
        
        submitted = st.form_submit_button("💾 Calculate & Save")
    
    if submitted:
        # Save profile (always store in metric)
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
        
        # Auto-update history with new weight
        history_path = "data/history.csv"
        m = get_metrics()
        
        # Check if there's already an entry for today
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(history_path):
            existing_history = pd.read_csv(history_path)
            existing_history["date"] = pd.to_datetime(existing_history["date"]).dt.date
            
            # Check if today's entry exists
            today_date = datetime.now().date()
            if today_date in existing_history["date"].values:
                # Update existing row with new weight
                existing_history.loc[existing_history["date"] == today_date, "weight_kg"] = weight_kg
                existing_history.to_csv(history_path, index=False)
                st.success("✅ Profile saved and today's weight updated in history!")
            else:
                # Create new entry for today
                new_entry = pd.DataFrame({
                    "date": [today_str],
                    "recovery": [m.get("recovery", 0)],
                    "strain": [m.get("strain", 0)],
                    "rhr": [m.get("rhr", 0)],
                    "hrv": [m.get("hrv", 0)],
                    "stress": [m.get("stress", 0)],
                    "readiness": [m.get("readiness", 0)],
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
                "weight_kg": [weight_kg]
            })
            new_entry.to_csv(history_path, index=False)
            st.success("✅ Profile saved and history tracking started!")
        
        # Clear cache and rerun to show updated data
        st.cache_data.clear()
        st.rerun()
    
    # Display results if profile exists
    if profile:
        st.divider()
        
        # Calculate metrics
        bmi = calculate_bmi(profile["weight_kg"], profile["height_cm"])
        bmi_category, bmi_color = get_bmi_category(bmi)
        bmr = calculate_bmr(profile["weight_kg"], profile["height_cm"], profile["age"], profile["sex"])
        tdee = calculate_tdee(bmr, profile.get("activity_minutes_per_week"), profile.get("avg_steps_per_day"))
        
        # Display weight and height in both units for reference
        weight_display_kg = profile["weight_kg"]
        weight_display_lbs = kg_to_lbs(profile["weight_kg"])
        height_display_cm = profile["height_cm"]
        height_display_inches = cm_to_inches(profile["height_cm"])
        
        # Display BMI
        st.subheader("📊 Your Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("BMI", f"{bmi:.1f}", delta=bmi_category)
            
            # BMI gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=bmi,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "<b>Body Mass Index</b>"},
                gauge={
                    'axis': {'range': [15, 40]},
                    'bar': {'color': bmi_color},
                    'steps': [
                        {'range': [15, 18.5], 'color': "lightblue"},
                        {'range': [18.5, 25], 'color': "lightgreen"},
                        {'range': [25, 30], 'color': "lightyellow"},
                        {'range': [30, 40], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': bmi
                    }
                }
            ))
            fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("BMR", f"{int(bmr)} cal/day", help="Calories burned at complete rest")
            st.write("")
            # Show weight and height in BOTH units
            st.caption(f"💡 Weight: **{weight_display_kg:.1f} kg** / **{weight_display_lbs:.1f} lbs**")
            st.caption(f"💡 Height: **{height_display_cm:.1f} cm** / **{height_display_inches:.1f} in**")
            st.info(f"**Basal Metabolic Rate:** This is how many calories your body burns just to stay alive (breathing, heart beating, etc.)")
        
        with col3:
            st.metric("TDEE", f"{int(tdee)} cal/day", help="Total calories burned per day")
            st.write("")
            st.write("")
            st.success(f"**Total Daily Energy Expenditure:** This is your total calorie burn including activity")
        
        # Detailed breakdown
        st.divider()
        st.subheader("🔥 Calorie Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**To maintain weight:**")
            st.write(f"- Eat **{int(tdee)}** calories/day")
            st.write("")
            st.write("**To lose weight (0.5 kg/week):**")
            st.write(f"- Eat **{int(tdee - 500)}** calories/day")
            st.write(f"- Creates 500 cal/day deficit")
            st.write("")
            st.write("**To gain weight (0.5 kg/week):**")
            st.write(f"- Eat **{int(tdee + 500)}** calories/day")
            st.write(f"- Creates 500 cal/day surplus")
        
        with col2:
            # Activity contribution
            activity_calories = tdee - bmr
            
            st.write("**Your calorie sources:**")
            st.write(f"- **Base metabolism (BMR):** {int(bmr)} cal")
            st.write(f"- **Activity & movement:** {int(activity_calories)} cal")
            st.write(f"- **Total (TDEE):** {int(tdee)} cal")
            
            # Activity level description
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
                st.info(f"📱 Activity Level: **{level}** ({steps:,} steps/day)")
            elif profile.get("activity_minutes_per_week"):
                mins = profile["activity_minutes_per_week"]
                if mins < 30:
                    level = "Sedentary"
                elif mins < 150:
                    level = "Lightly Active"
                elif mins < 300:
                    level = "Moderately Active"
                elif mins < 420:
                    level = "Very Active"
                else:
                    level = "Extremely Active"
                st.info(f"⏱️ Activity Level: **{level}** ({mins} min/week)")
        
        # Educational section
        with st.expander("ℹ️ Understanding These Metrics"):
            st.write("""
            ### BMI (Body Mass Index)
            A simple calculation using height and weight. Not perfect (doesn't account for muscle mass), but useful as a general guideline.
            - **Underweight:** < 18.5
            - **Normal:** 18.5 - 24.9
            - **Overweight:** 25 - 29.9
            - **Obese:** ≥ 30
            
            ### BMR (Basal Metabolic Rate)
            The calories you'd burn if you stayed in bed all day. Calculated using the **Mifflin-St Jeor equation** - the most accurate formula available.
            
            ### TDEE (Total Daily Energy Expenditure)
            Your actual daily calorie burn including all activity. We calculate this based on your activity level:
            - **Steps method:** More accurate if you track daily steps
            - **Exercise minutes:** Good if you do structured workouts
            
            ### Weight Loss/Gain Math
            - **1 kg of body fat = ~7,700 calories**
            - **500 cal/day deficit = 0.5 kg weight loss per week**
            - **500 cal/day surplus = 0.5 kg weight gain per week**
            
            These are estimates. Individual results vary based on metabolism, genetics, and other factors.
            """)
        
        # Integration with heart data
        st.divider()
        st.subheader("💡 Training Insights")
        
        m = get_metrics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Today's Strain:** {m['strain']:.1f}/21")
            estimated_calories = int(activity_calories * (m['strain'] / 14))  # Normalize to moderate activity
            st.write(f"**Estimated calories burned from activity:** ~{estimated_calories} cal")
        
        with col2:
            st.write(f"**Training Readiness:** {m['readiness']}%")
            if m['readiness'] > 70:
                st.success("✅ Your body is ready for a hard workout! You can maximize calorie burn today.")
            elif m['readiness'] > 40:
                st.warning("⚠️ Light workout recommended. Focus on recovery, not burning maximum calories.")
            else:
                st.error("🛑 Rest day. Don't worry about calories - focus on recovery!")
    else:
        st.info("👆 Fill out the form above to calculate your BMI and metabolic rate!")
