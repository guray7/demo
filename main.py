import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Primavera Gantt with Links", layout="wide")
st.title("📊 Primavera Gantt Chart with Dependencies")

uploaded_file = st.file_uploader("Upload Primavera .xer file with TASK, PROJWBS, TASKPRED", type="xer")

def extract_table(lines, table_name):
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
            row += [None] * (len(headers) - len(row))
            table_rows.append(row)
        elif capturing and not line.startswith("%R") and not line.startswith("%F"):
            break

    return pd.DataFrame(table_rows, columns=headers) if table_rows else None

def parse_xer(file):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    task_df = extract_table(lines, "TASK")
    wbs_df = extract_table(lines, "PROJWBS")
    pred_df = extract_table(lines, "TASKPRED")

    task_df = task_df.rename(columns={
        'task_id': 'Task ID',
        'task_name': 'Task',
        'early_start_date': 'Start',
        'early_end_date': 'End',
        'orig_dur_hr_cnt': 'Duration',
        'wbs_id': 'WBS'
    })
    task_df['Start'] = pd.to_datetime(task_df['Start'], errors='coerce')
    task_df['End'] = pd.to_datetime(task_df['End'], errors='coerce')
    task_df['Duration'] = (task_df['End'] - task_df['Start']).dt.days
    task_df.dropna(subset=["Start", "End"], inplace=True)

    wbs_df = wbs_df.rename(columns={'wbs_id': 'WBS', 'wbs_name': 'WBS Name'})
    task_df = task_df.merge(wbs_df[['WBS', 'WBS Name']], on='WBS', how='left')

    pred_df = pred_df.rename(columns={
        'task_id': 'Successor',
        'pred_task_id': 'Predecessor',
        'pred_type': 'Type',
        'lag_hr_cnt': 'Lag'
    })
    return task_df, pred_df

def plot_gantt_with_dependencies(tasks, preds):
    fig = go.Figure()

    for i, row in tasks.iterrows():
        fig.add_trace(go.Bar(
            x=[(row['End'] - row['Start']).days],
            y=[row['Task']],
            base=row['Start'],
            orientation='h',
            name=row['Task'],
            marker=dict(color='royalblue'),
            hovertext=f"{row['WBS Name']} ({row['Task']})"
        ))

    for _, link in preds.iterrows():
        pred = tasks[tasks['Task ID'] == link['Predecessor']]
        succ = tasks[tasks['Task ID'] == link['Successor']]
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

    fig.update_layout(
        title="Gantt Chart with Dependencies",
        barmode='stack',
        xaxis=dict(type='date', title='Date'),
        yaxis=dict(autorange='reversed', title='Tasks'),
        height=800,
    )
    return fig

if uploaded_file:
    task_df, pred_df = parse_xer(uploaded_file)
    fig = plot_gantt_with_dependencies(task_df, pred_df)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please upload a valid .xer file containing TASK, PROJWBS and TASKPRED tables.")
