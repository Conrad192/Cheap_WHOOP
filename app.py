# Import tools
import streamlit as st
import plotly.graph_objects as go
from metrics import get_metrics
import os
from datetime import datetime
import pandas as pd
from pull_xiaomi import generate_xiaomi_data
from pull_coospo import generate_coospo_data
from merge import merge_data
from calibration import calibrate_wrist_to_chest, get_calibration_status
import json

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

# Tabs with icons - NOW WITH CALIBRATION
tab1, tab2, tab3, tab4 = st.tabs(["❤️ Heart Data", "😴 Sleep", "📈 History", "⚙️ Calibrate"])


# ----------------------------
# TAB 1 – HEART DATA + REFRESH
# ----------------------------
with tab1:
    # Get metrics first
    m = get_metrics()
    
    # NEW: Status banner
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

            # Build new history row
            history_path = "data/history.csv"
            history_df = pd.DataFrame({
                "date": [datetime.now().strftime("%Y-%m-%d")],
                "recovery": [m["recovery"]],
                "strain": [m["strain"]],
                "rhr": [m["rhr"]],
                "hrv": [m["hrv"]]
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
            st.write("Strain (0–21): Measures total cardiovascular load for the day.")

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
            st.write("Recovery is based on HRV and Resting HR. Green = ready to train.")

    col_hrv, col_rhr = st.columns(2)
    with col_hrv:
        st.metric("HRV", f"{m['hrv']} ms", help="Higher HRV = better recovery.")

    with col_rhr:
        st.metric("Resting HR", f"{m['rhr']} BPM", help="Lower RHR = better fitness.")
    
    # NEW: Compare to baseline
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

        # Metric selection
        metric = st.selectbox(
            "Select Metric to View",
            ["recovery", "strain", "rhr", "hrv"],
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
# TAB 4 – CALIBRATION MODE
# ----------------------------
with tab4:
    st.subheader("🎯 Calibration Mode")
    st.write("Make your wrist data as accurate as your chest strap!")
    
    # Instructions
    st.info("""
    **How to calibrate:**
    1. Wear BOTH your Xiaomi band AND Coospo chest strap
    2. Do a 20+ minute workout (run, bike, etc.)
    3. Click 'Run Calibration' below
    4. Your wrist data will be corrected to match chest strap accuracy
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Steps")
        st.markdown("✅ Step 1: Wear both devices")
        st.markdown("✅ Step 2: Exercise for 20+ min")
        st.markdown("✅ Step 3: Run calibration")
        st.markdown("✅ Step 4: Profit!")
    
    with col2:
        # Show current calibration status
        cal_status = get_calibration_status()
        
        if cal_status:
            st.markdown("### ✅ Current Calibration")
            cal_date = cal_status["date"][:10]
            st.success(f"Last calibrated: {cal_date}")
            st.metric("Data Points Used", cal_status["samples"])
            st.metric("Avg Error Before", f"{cal_status['avg_error_before']:.1f} BPM")
            
            # Show correction factors
            with st.expander("📊 Correction Details"):
                st.write(f"**BPM:** {cal_status['bpm_slope']:.3f}x + {cal_status['bpm_intercept']:.1f}")
                st.write(f"**RR:** {cal_status['rr_slope']:.3f}x + {cal_status['rr_intercept']:.1f}")
        else:
            st.markdown("### ⚠️ Not Calibrated")
            st.warning("No calibration found. Your data may be less accurate.")
    
    st.divider()
    
    # Calibration buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔬 Run Calibration", type="primary"):
            with st.spinner("Analyzing workout data..."):
                result = calibrate_wrist_to_chest(
                    "data/raw/xiaomi_today.csv",
                    "data/raw/coospo_workout.csv"
                )
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                    st.info(f"Only found {result['samples']} matching data points. Need 30+")
                else:
                    st.success(f"✅ Calibration complete! Used {result['samples']} data points")
                    st.balloons()
                    
                    # Show improvement
                    st.metric(
                        "Average Error Before", 
                        f"{result['avg_error_before']:.1f} BPM",
                        help="How far off your wrist was from chest strap"
                    )
                    
                    # Clear cache to use new calibration
                    st.cache_data.clear()
                    st.rerun()
    
    with col_btn2:
        if cal_status and st.button("🗑️ Remove Calibration"):
            os.remove("data/calibration.json")
            st.success("Calibration removed. Using raw data now.")
            st.cache_data.clear()
            st.rerun()
    
    # Explanation
    with st.expander("❓ Why calibrate?"):
        st.write("""
        **Wrist-based heart rate monitors are less accurate than chest straps** because:
        - Movement causes noise in optical sensors
        - Blood flow varies at the wrist
        - Skin tone and tattoos affect readings
        
        **Calibration fixes this** by:
        - Comparing your wrist to chest strap during exercise
        - Creating a correction formula specific to YOU
        - Applying it to all future wrist readings
        
        **Result:** Wrist data becomes nearly as accurate as chest strap! 📈
        """)