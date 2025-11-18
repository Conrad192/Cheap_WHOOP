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

# Page setup
st.set_page_config(page_title="Cheap WHOOP", layout="centered")
st.title("💪 Cheap WHOOP 1")
st.caption("No $30/month. Just $75 hardware + your code.")

# Tabs with icons
tab1, tab2, tab3, tab4 = st.tabs(["❤️ Heart Data", "😴 Sleep", "📈 History", "BMI"])


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

            # Build new history row with NEW metrics
            history_path = "data/history.csv"
            history_df = pd.DataFrame({
                "date": [datetime.now().strftime("%Y-%m-%d")],
                "recovery": [m["recovery"]],
                "strain": [m["strain"]],
                "rhr": [m["rhr"]],
                "hrv": [m["hrv"]],
                "stress": [m["stress"]],
                "readiness": [m["readiness"]]
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

        # Metric selection - NOW WITH NEW METRICS
        metric = st.selectbox(
            "Select Metric to View",
            ["recovery", "strain", "rhr", "hrv", "stress", "readiness"],
            index=0
        )

        # Convert date to string to avoid Plotly timestamp autoscaling
        daily["date_str"] = daily["date"].astype(str)

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["date_str"],
            y=daily[metric],
            mode="lines+markers",
            name=metric.capitalize()
        ))

        fig.update_layout(
            title=f"{metric.capitalize()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric.capitalize(),
            xaxis=dict(type="category")
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("No history yet. Refresh in the Heart tab to start tracking.")


# ----------------------------
# TAB 4 – BODY COMPOSITION
# ----------------------------
with tab4:
    import os
    
    # File to store body composition data
    BODY_DATA_FILE = "data/body_composition.csv"

    def load_body_data():
        """Load body composition history"""
        if os.path.exists(BODY_DATA_FILE):
            df = pd.read_csv(BODY_DATA_FILE)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            return df
        return pd.DataFrame(columns=["date", "weight_lbs", "bodyfat_pct", "bmi"])

    def save_body_data(df):
        """Save body composition data"""
        os.makedirs("data", exist_ok=True)
        df.to_csv(BODY_DATA_FILE, index=False)

    def calculate_bmi(weight_lbs, height_inches):
        """Calculate BMI from weight (lbs) and height (inches)"""
        return (weight_lbs / (height_inches ** 2)) * 703

    def get_bmi_category(bmi):
        """Get BMI category and color"""
        if bmi < 18.5:
            return "Underweight", "blue"
        elif bmi < 25:
            return "Normal", "green"
        elif bmi < 30:
            return "Overweight", "orange"
        else:
            return "Obese", "red"

    # Load existing data
    body_df = load_body_data()

    # Create sub-tabs
    subtab1, subtab2 = st.tabs(["📝 Log Entry", "📈 History & Trends"])

    # SUB-TAB 1: Log new entry
    with subtab1:
        st.subheader("Log Today's Measurements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Height (only need to enter once, but allow updates)
            if 'height' not in st.session_state:
                st.session_state.height = 70  # Default 5'10"
            
            height_ft = st.number_input("Height (feet)", min_value=4, max_value=7, value=5, key="height_ft")
            height_in = st.number_input("Height (inches)", min_value=0, max_value=11, value=10, key="height_in")
            total_height = (height_ft * 12) + height_in
            st.session_state.height = total_height
            
            st.caption(f"Total: {total_height} inches ({height_ft}'{height_in}\")")
        
        with col2:
            # Weight entry
            weight = st.number_input(
                "Body Weight (lbs)", 
                min_value=50.0, 
                max_value=500.0, 
                value=170.0,
                step=0.1,
                key="weight_input"
            )
        
        st.divider()
        
        # Body fat percentage selector with visual guide
        st.subheader("Body Fat Percentage Estimate")
        st.caption("Select the image that most closely matches your current physique")
        
        # Create three columns for body fat examples
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🟢 15%")
            st.markdown("""
            **Lean/Athletic**
            - Visible abs
            - Veins visible
            - Muscle definition clear
            """)
            btn1 = st.button("Select 15%", use_container_width=True, key="bf15")
        
        with col2:
            st.markdown("### 🟡 20%")
            st.markdown("""
            **Fit**
            - Some ab definition
            - Healthy appearance
            - Light muscle tone
            """)
            btn2 = st.button("Select 20%", use_container_width=True, key="bf20")
        
        with col3:
            st.markdown("### 🟠 25%")
            st.markdown("""
            **Average**
            - Soft appearance
            - No visible abs
            - Some body softness
            """)
            btn3 = st.button("Select 25%", use_container_width=True, key="bf25")
        
        # Initialize bodyfat in session state
        if 'bodyfat' not in st.session_state:
            st.session_state.bodyfat = 20.0
        
        # Update bodyfat based on button clicks
        if btn1:
            st.session_state.bodyfat = 15.0
        elif btn2:
            st.session_state.bodyfat = 20.0
        elif btn3:
            st.session_state.bodyfat = 25.0
        
        # Allow custom input too
        bodyfat = st.slider(
            "Or enter custom body fat %", 
            min_value=5.0, 
            max_value=50.0, 
            value=st.session_state.bodyfat,
            step=0.5,
            help="Drag to fine-tune your body fat percentage",
            key="bf_slider"
        )
        
        st.session_state.bodyfat = bodyfat
        
        st.divider()
        
        # Calculate BMI
        bmi = calculate_bmi(weight, total_height)
        bmi_cat, bmi_color = get_bmi_category(bmi)
        
        # Show preview
        st.subheader("Today's Metrics Preview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Weight", f"{weight} lbs")
        with col2:
            st.metric("Body Fat", f"{bodyfat}%")
        with col3:
            st.metric("BMI", f"{bmi:.1f}")
        with col4:
            st.metric("Category", bmi_cat)
        
        # Calculate lean mass
        lean_mass = weight * (1 - bodyfat/100)
        fat_mass = weight - lean_mass
        
        st.caption(f"💪 Lean Mass: {lean_mass:.1f} lbs | 🔥 Fat Mass: {fat_mass:.1f} lbs")
        
        # Save button
        if st.button("💾 Save Entry", type="primary", use_container_width=True, key="save_body"):
            from datetime import datetime
            new_entry = pd.DataFrame({
                "date": [datetime.now().date()],
                "weight_lbs": [weight],
                "bodyfat_pct": [bodyfat],
                "bmi": [bmi],
                "height_inches": [total_height]
            })
            
            # Remove today's entry if it exists, then add new one
            body_df = body_df[body_df["date"] != datetime.now().date()]
            body_df = pd.concat([body_df, new_entry], ignore_index=True)
            body_df = body_df.sort_values("date")
            
            save_body_data(body_df)
            st.success("✅ Entry saved!")
            st.rerun()

    # SUB-TAB 2: History and trends
    with subtab2:
        st.subheader("Body Composition History")
        
        body_df = load_body_data()
        
        if body_df.empty:
            st.info("📝 No data yet. Log your first entry in the 'Log Entry' tab!")
        else:
            # Calculate derived metrics
            body_df["lean_mass"] = body_df["weight_lbs"] * (1 - body_df["bodyfat_pct"]/100)
            body_df["fat_mass"] = body_df["weight_lbs"] - body_df["lean_mass"]
            
            # Time range filter
            col1, col2 = st.columns([3, 1])
            with col1:
                time_range = st.selectbox(
                    "Time Range",
                    ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
                    index=1,
                    key="body_time_range"
                )
            
            # Filter data
            from datetime import datetime
            filtered_df = body_df.copy()
            if time_range != "All Time":
                days = int(time_range.split()[1])
                cutoff = datetime.now().date() - pd.Timedelta(days=days)
                filtered_df = filtered_df[filtered_df["date"] >= cutoff]
            
            if filtered_df.empty:
                st.warning(f"No data in the selected time range. Try 'All Time'")
            else:
                # Current vs. Starting stats
                st.subheader("📊 Progress Summary")
                
                current = filtered_df.iloc[-1]
                start = filtered_df.iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    weight_change = current["weight_lbs"] - start["weight_lbs"]
                    st.metric(
                        "Weight", 
                        f"{current['weight_lbs']:.1f} lbs",
                        f"{weight_change:+.1f} lbs"
                    )
                
                with col2:
                    bf_change = current["bodyfat_pct"] - start["bodyfat_pct"]
                    st.metric(
                        "Body Fat", 
                        f"{current['bodyfat_pct']:.1f}%",
                        f"{bf_change:+.1f}%",
                        delta_color="inverse"
                    )
                
                with col3:
                    lean_change = current["lean_mass"] - start["lean_mass"]
                    st.metric(
                        "Lean Mass", 
                        f"{current['lean_mass']:.1f} lbs",
                        f"{lean_change:+.1f} lbs"
                    )
                
                with col4:
                    bmi_change = current["bmi"] - start["bmi"]
                    st.metric(
                        "BMI", 
                        f"{current['bmi']:.1f}",
                        f"{bmi_change:+.1f}"
                    )
                
                st.divider()
                
                # Charts
                st.subheader("📈 Trends")
                
                # Metric selector
                metric = st.selectbox(
                    "Select Metric",
                    ["Weight", "Body Fat %", "BMI", "Lean Mass", "Fat Mass"],
                    index=0,
                    key="body_metric_select"
                )
                
                # Map selection to column
                metric_map = {
                    "Weight": "weight_lbs",
                    "Body Fat %": "bodyfat_pct",
                    "BMI": "bmi",
                    "Lean Mass": "lean_mass",
                    "Fat Mass": "fat_mass"
                }
                
                col_name = metric_map[metric]
                
                # Create chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=filtered_df["date"].astype(str),
                    y=filtered_df[col_name],
                    mode="lines+markers",
                    name=metric,
                    line=dict(color="#FF6B6B", width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title=f"{metric} Over Time",
                    xaxis_title="Date",
                    yaxis_title=metric,
                    height=400,
                    hovermode="x unified",
                    xaxis=dict(type="category")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 View All Entries"):
                    display_df = filtered_df[["date", "weight_lbs", "bodyfat_pct", "bmi", "lean_mass", "fat_mass"]].copy()
                    display_df.columns = ["Date", "Weight (lbs)", "Body Fat %", "BMI", "Lean Mass", "Fat Mass"]
                    display_df = display_df.sort_values("Date", ascending=False)
                    
                    # Format numbers
                    for col in ["Weight (lbs)", "Body Fat %", "BMI", "Lean Mass", "Fat Mass"]:
                        display_df[col] = display_df[col].round(1)
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)