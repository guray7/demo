import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Shutdown Delay Comparator (.csv & .xer)", layout="wide")

st.title("📊 Shutdown Delay Analysis Panel (.csv & .xer)")

col1, col2 = st.columns(2)

with col1:
    uploaded_file_1 = st.file_uploader("📂 Upload Baseline Schedule (.csv or .xer)", type=["csv", "xer"], key="baseline_file")
with col2:
    uploaded_file_2 = st.file_uploader("📂 Upload Actual Schedule (.csv or .xer)", type=["csv", "xer"], key="actual_file")

def extract_table_safe(lines, table_name):
    table_rows = []
    capturing = False
    headers = []

    for line in lines:
        if line.startswith("%T") and table_name in line:
            capturing = True
        elif capturing and line.startswith("%F"):
            headers = line.strip().split("\t")[1:]
        elif capturing and line.startswith("%R"):
            row = line.strip().split("\t")[1:]
            if len(row) < len(headers):
                row += [None] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[:len(headers)]
            table_rows.append(row)
        elif capturing and not line.startswith("%R") and not line.startswith("%F"):
            break

    return pd.DataFrame(table_rows, columns=headers) if table_rows else None

def parse_xer(file):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    task_df = extract_table_safe(lines, "TASK")
    if task_df is not None:
        task_df = task_df.rename(columns={
            'task_name': 'Task',
            'early_start_date': 'Start',
            'early_end_date': 'End',
            'orig_dur_hr_cnt': 'Duration',
            'wbs_id': 'Equipment'
        })
        task_df = task_df[["Task", "Start", "End", "Duration", "Equipment"]].dropna()
        task_df["Start"] = pd.to_datetime(task_df["Start"], errors='coerce')
        task_df["End"] = pd.to_datetime(task_df["End"], errors='coerce')
        task_df["Duration"] = (task_df["End"] - task_df["Start"]).dt.days
        task_df = task_df.dropna(subset=["Start", "End"])
        task_df["Crew Readiness"] = 80
        task_df["Season"] = task_df["Start"].dt.month.map(lambda m: "Winter" if m in [12,1,2] else "Summer")
    return task_df

def read_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        df["Start"] = pd.to_datetime(df["Start"])
        df["End"] = df["Start"] + pd.to_timedelta(df["Duration"], unit="D")
    elif filename.endswith(".xer"):
        df = parse_xer(uploaded_file)
    else:
        st.error("Unsupported file type")
        return None
    return df

if uploaded_file_1 and uploaded_file_2:
    df1 = read_file(uploaded_file_1)
    df2 = read_file(uploaded_file_2)

    if df1 is not None and df2 is not None:
        with col1:
            st.subheader("📅 Baseline Gantt Chart")
            st.plotly_chart(px.timeline(df1, x_start="Start", x_end="End", y="Task", color="Equipment").update_yaxes(autorange="reversed"), use_container_width=True, key="baseline_chart")

        with col2:
            st.subheader("📅 Actual Gantt Chart")
            st.plotly_chart(px.timeline(df2, x_start="Start", x_end="End", y="Task", color="Equipment").update_yaxes(autorange="reversed"), use_container_width=True, key="actual_chart")

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
    st.info("Please upload both baseline and actual shutdown CSV or XER files to begin analysis.")
