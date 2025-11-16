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
tab1, tab2, tab3 = st.tabs(["❤️ Heart Data", "😴 Sleep", "📈 History"])


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