import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Shutdown Delay Comparator", layout="wide")

st.title("📊 Side-by-Side Gantt Chart for Shutdown Projects")

col1, col2 = st.columns(2)

with col1:
    uploaded_file_1 = st.file_uploader("📂 Upload Baseline Schedule", type=["csv"], key="baseline_file")
with col2:
    uploaded_file_2 = st.file_uploader("📂 Upload Actual Schedule", type=["csv"], key="actual_file")

if uploaded_file_1 and uploaded_file_2:
    df1 = pd.read_csv(uploaded_file_1)
    df2 = pd.read_csv(uploaded_file_2)

    df1["Start"] = pd.to_datetime(df1["Start"])
    df1["End"] = df1["Start"] + pd.to_timedelta(df1["Duration"], unit="D")
    df2["Start"] = pd.to_datetime(df2["Start"])
    df2["End"] = df2["Start"] + pd.to_timedelta(df2["Duration"], unit="D")

    col1.subheader("📅 Baseline Gantt Chart")
    fig1 = px.timeline(df1, x_start="Start", x_end="End", y="Task", color="Equipment")
    fig1.update_yaxes(autorange="reversed")
    col1.plotly_chart(fig1, use_container_width=True)

    col2.subheader("📅 Actual Gantt Chart")
    fig2 = px.timeline(df2, x_start="Start", x_end="End", y="Task", color="Equipment")
    fig2.update_yaxes(autorange="reversed")
    col2.plotly_chart(fig2, use_container_width=True)

    st.subheader("🧠 AI Analysis Data Preparation")
    comparison = df1.merge(df2, on="Task", suffixes=("_baseline", "_actual"))
    comparison["Delay"] = (comparison["Start_actual"] - comparison["Start_baseline"]).dt.days

    ai_ready_data = comparison[[
        "Task",
        "Equipment_baseline",
        "Duration_baseline",
        "Duration_actual",
        "Crew Readiness_baseline",
        "Crew Readiness_actual",
        "Delay",
        "Season_actual"
    ]].rename(columns={
        "Equipment_baseline": "equipment",
        "Duration_baseline": "planned_duration",
        "Duration_actual": "actual_duration",
        "Crew Readiness_baseline": "planned_crew_readiness",
        "Crew Readiness_actual": "actual_crew_readiness",
        "Season_actual": "season"
    })

    st.download_button("⬇️ Download for AI", json.dumps(ai_ready_data.to_dict(orient="records"), indent=4), file_name="ai_shutdown_comparison.json")

    if st.button("🧠 Simulate AI Response"):
        for _, row in ai_ready_data.iterrows():
            st.markdown(f"### Task: {row['Task']}")
            st.markdown(f"Delay: {row['Delay']} days")
            st.markdown(f"Planned Duration: {row['planned_duration']} → Actual Duration: {row['actual_duration']}")
            st.markdown(f"Planned Readiness: {row['planned_crew_readiness']}% → Actual: {row['actual_crew_readiness']}%")
            st.markdown(f"**AI Prompt Preview:**\nWhat factors likely caused a {row['Delay']}-day delay in this shutdown task?\nHow can similar delays be prevented in {row['season']}?")
            st.markdown("---")
else:
    st.info("Please upload both baseline and actual shutdown CSV files to begin analysis.")
