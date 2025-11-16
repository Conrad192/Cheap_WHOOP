# Import tools
import streamlit as st
import plotly.graph_objects as go
from metrics import get_metrics
import os
from datetime import datetime
import pandas as pd

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
    if st.button("🔄 Refresh Data"):
        os.system("python pull_xiaomi.py")
        os.system("python pull_coospo.py")
        os.system("python merge.py")

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
        st.success("Data updated and added to history!")

    # Fetch metrics to show
    m = get_metrics()

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
# TAB 3 – HISTORY TRENDS (FIXED)
# ----------------------------
# ----------------------------
# TAB 3 – HISTORY TRENDS (CLEAN X-AXIS + DATE FILTERING)
# ----------------------------
with tab3:
    st.subheader("History Trends")
    history_path = "data/history.csv"

    if os.path.exists(history_path):
        history_df = pd.read_csv(history_path)

        # Convert to date (no timestamps)
        history_df["date"] = pd.to_datetime(history_df["date"]).dt.date

        # Group by date
        daily = history_df.groupby("date", as_index=False).mean()

        # Time-range filter
        filter_range = st.selectbox(
            "Time Range",
            ["Today","Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
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
            x=daily["date_str"],      # <- STRINGS = clean axis labels
            y=daily[metric],
            mode="lines+markers",
            name=metric.capitalize()
        ))

        fig.update_layout(
            title=f"{metric.capitalize()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric.capitalize(),
            xaxis=dict(type="category")   # <- forces clean dates only
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("No history yet. Refresh in the Heart tab to start tracking.")
