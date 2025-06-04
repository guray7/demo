import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Primavera Gantt Viewer (.csv & .xer)", layout="wide")

st.title("📊 Primavera Shutdown Project Viewer (.xer & .csv)")

uploaded_file = st.file_uploader("📂 Upload Primavera .xer or CSV file", type=["xer", "csv"])

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
        elif capturing and not line.startswith("%R"):
            break

    return pd.DataFrame(table_rows, columns=headers) if table_rows else None

def parse_xer(file):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    task_df = extract_table_safe(lines, "TASK")
    wbs_df = extract_table_safe(lines, "PROJWBS")

    if task_df is None or wbs_df is None:
        st.error("TASK or PROJWBS table missing in .xer file.")
        return None

    task_df = task_df.rename(columns={
        'task_name': 'Task',
        'early_start_date': 'Start',
        'early_end_date': 'End',
        'orig_dur_hr_cnt': 'Duration',
        'wbs_id': 'WBS_ID'
    })

    wbs_df = wbs_df.rename(columns={
        'wbs_id': 'WBS_ID',
        'wbs_name': 'WBS_Name',
        'proj_short_name': 'Project'
    })

    df = task_df.merge(wbs_df, on='WBS_ID', how='left')
    df = df[["Project", "WBS_Name", "Task", "Start", "End", "Duration"]]
    df.dropna(subset=["Start", "End"], inplace=True)
    df["Start"] = pd.to_datetime(df["Start"], errors='coerce')
    df["End"] = pd.to_datetime(df["End"], errors='coerce')
    df["Duration"] = (df["End"] - df["Start"]).dt.days
    df = df.dropna(subset=["Start", "End", "Task"])
    df["WBS"] = df["Project"] + " → " + df["WBS_Name"]
    return df

def parse_csv(file):
    df = pd.read_csv(file)
    df["Start"] = pd.to_datetime(df["Start"])
    df["End"] = df["Start"] + pd.to_timedelta(df["Duration"], unit="D")
    df["WBS"] = df["WBS"] if "WBS" in df.columns else "General"
    return df

if uploaded_file:
    filename = uploaded_file.name.lower()
    if filename.endswith(".xer"):
        df = parse_xer(uploaded_file)
    elif filename.endswith(".csv"):
        df = parse_csv(uploaded_file)
    else:
        st.error("Unsupported file type.")
        df = None

    if df is not None and not df.empty:
        st.success(f"Successfully loaded {len(df)} tasks.")

        fig = px.timeline(
            df,
            x_start="Start",
            x_end="End",
            y="Task",
            color="WBS",
            title="📆 Gantt Chart with WBS View",
            hover_data=["Project", "WBS"]
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please upload a Primavera .xer or Gantt-style .csv file to begin.")
