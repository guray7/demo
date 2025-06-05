import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

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
    wbs_df = extract_table_safe(lines, "PROJWBS")
    pred_df = extract_table_safe(lines, "TASKPRED")

    task_df = task_df.rename(columns={
        'task_id': 'Task ID',
        'task_name': 'Task',
        'early_start_date': 'Start',
        'early_end_date': 'End',
        'orig_dur_hr_cnt': 'Duration',
        'wbs_id': 'WBS'
    })
    task_df.dropna(subset=["Task ID", "Task"], inplace=True)
    task_df["Task ID"] = task_df["Task ID"].astype(str)
    task_df['Start'] = pd.to_datetime(task_df['Start'], errors='coerce')
    task_df['End'] = pd.to_datetime(task_df['End'], errors='coerce')
    task_df['Duration'] = (task_df['End'] - task_df['Start']).dt.days
    task_df.dropna(subset=["Start", "End"], inplace=True)

    if wbs_df is not None:
        wbs_df = wbs_df.rename(columns={'wbs_id': 'WBS', 'wbs_name': 'WBS Name'})
        task_df = task_df.merge(wbs_df[['WBS', 'WBS Name']], on='WBS', how='left')

    if pred_df is not None:
        if 'Predecessor' not in pred_df.columns:
            pred_df = pred_df.rename(columns={
                'task_id': 'Successor',
                'pred_task_id': 'Predecessor',
                'pred_type': 'Type',
                'lag_hr_cnt': 'Lag'
            })
        pred_df["Predecessor"] = pred_df["Predecessor"].astype(str)
        pred_df["Successor"] = pred_df["Successor"].astype(str)

    return task_df, pred_df

def read_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        df["Start"] = pd.to_datetime(df["Start"])
        df["End"] = df["Start"] + pd.to_timedelta(df["Duration"], unit="D")
        return df, None
    elif filename.endswith(".xer"):
        return parse_xer(uploaded_file)
    else:
        st.error("Unsupported file type")
        return None, None

def draw_dependencies(fig, task_df, pred_df):
    if pred_df is None:
        return fig
    for _, link in pred_df.iterrows():
        pred = task_df[task_df['Task ID'] == link['Predecessor']]
        succ = task_df[task_df['Task ID'] == link['Successor']]
        if not pred.empty and not succ.empty:
            x0 = pred.iloc[0]['End']
            x1 = succ.iloc[0]['Start']
            y0 = pred.iloc[0]['Task']
            y1 = succ.iloc[0]['Task']
            fig.add_annotation(
                x=x1, y=y1,
                ax=x0, ay=y0,
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=1,
                arrowcolor='red',
                opacity=0.8
            )
    return fig

if uploaded_file_1 and uploaded_file_2:
    df1, pred1 = read_file(uploaded_file_1)
    df2, pred2 = read_file(uploaded_file_2)

    if df1 is not None and df2 is not None:
        with col1:
            st.subheader("📅 Baseline Gantt Chart")
            fig1 = px.timeline(df1, x_start="Start", x_end="End", y="Task", color="Equipment" if "Equipment" in df1.columns else "WBS Name")
            fig1.update_yaxes(autorange="reversed")
            fig1 = draw_dependencies(fig1, df1, pred1)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("📅 Actual Gantt Chart")
            fig2 = px.timeline(df2, x_start="Start", x_end="End", y="Task", color="Equipment" if "Equipment" in df2.columns else "WBS Name")
            fig2.update_yaxes(autorange="reversed")
            fig2 = draw_dependencies(fig2, df2, pred2)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("🧠 AI Analysis Data Preparation")
        comparison = df1.merge(df2, on="Task", suffixes=("_baseline", "_actual"))
        comparison["Delay"] = (comparison["Start_actual"] - comparison["Start_baseline"]).dt.days

        # Safe column mapping
        columns = {
            "Task": "Task",
            "Equipment_baseline": "equipment",
            "WBS Name_baseline": "equipment",
            "Duration_baseline": "planned_duration",
            "Duration_actual": "actual_duration",
            "Crew Readiness_baseline": "planned_crew_readiness",
            "Crew Readiness_actual": "actual_crew_readiness",
            "Delay": "Delay",
            "Season_actual": "season",
            "Duration_actual": "season"  # fallback if Season_actual yoksa
        }

        available = [col for col in columns if col in comparison.columns]
        ai_ready_data = comparison[available]
        ai_ready_data.columns = [columns[col] for col in available]

        st.download_button("⬇️ Download for AI", json.dumps(ai_ready_data.to_dict(orient="records"), indent=4), file_name="ai_shutdown_comparison.json")

        if st.button("🧠 Simulate AI Response"):
            for _, row in ai_ready_data.iterrows():
                st.markdown(f"### Task: {row['Task']}")
                st.markdown(f"Delay: {row['Delay']} days")
                st.markdown(f"Planned Duration: {row['planned_duration']} → Actual Duration: {row['actual_duration']}")
                st.markdown(f"Planned Readiness: {row.get('planned_crew_readiness', 'N/A')}% → Actual: {row.get('actual_crew_readiness', 'N/A')}%")
                st.markdown(f"**AI Prompt Preview:**\nWhat factors likely caused a {row['Delay']}-day delay in this shutdown task?\nHow can similar delays be prevented in {row.get('season', 'N/A')}?")
                st.markdown("---")
else:
    st.info("Please upload both baseline and actual shutdown CSV or XER files to begin analysis.")
