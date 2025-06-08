import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Primavera Gantt Tool", layout="wide")
st.title("📊 Primavera XML/XER to Gantt Chart with Dependencies")

uploaded_file = st.file_uploader("📂 Upload Primavera XML or XER File", type=["xml", "xer"])

def parse_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    activities = []
    links = []
    for task in root.findall(".//{http://schemas.microsoft.com/project}Task"):
        uid = task.findtext("{http://schemas.microsoft.com/project}UID")
        name = task.findtext("{http://schemas.microsoft.com/project}Name")
        start = task.findtext("{http://schemas.microsoft.com/project}Start")
        finish = task.findtext("{http://schemas.microsoft.com/project}Finish")
        if None in (uid, name, start, finish):
            continue
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", ""))
            finish_dt = datetime.fromisoformat(finish.replace("Z", ""))
            if start_dt == finish_dt:
                finish_dt += pd.Timedelta(days=1)
            activities.append({"UID": uid, "ActivityName": name, "Start": start_dt, "Finish": finish_dt})
        except:
            continue
        for pred in task.findall("{http://schemas.microsoft.com/project}PredecessorLink"):
            pred_uid = pred.findtext("{http://schemas.microsoft.com/project}PredecessorUID")
            if pred_uid:
                links.append((pred_uid, uid))
    return pd.DataFrame(activities), links

def parse_xer(file):
    lines = file.read().decode("utf-8").splitlines()
    tasks, preds = [], []
    for line in lines:
        if line.startswith("TASK"):
            parts = line.split("\t")
            try:
                uid = parts[1]
                name = parts[10]
                start = datetime.strptime(parts[15], "%d-%b-%Y")
                finish = datetime.strptime(parts[16], "%d-%b-%Y")
                if start == finish:
                    finish += pd.Timedelta(days=1)
                tasks.append({"UID": uid, "ActivityName": name, "Start": start, "Finish": finish})
            except:
                continue
        elif line.startswith("TASKPRED"):
            parts = line.split("\t")
            if len(parts) >= 3:
                preds.append((parts[1], parts[2]))
    return pd.DataFrame(tasks), preds

if uploaded_file:
    if uploaded_file.name.endswith(".xml"):
        df, links = parse_xml(uploaded_file)
    else:
        df, links = parse_xer(uploaded_file)

    if not df.empty:
        st.success(f"✅ Found {len(df)} activities and {len(links)} dependencies")
        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                x=[(row['Finish'] - row['Start']).days],
                y=[row['ActivityName']],
                base=row['Start'],
                orientation='h',
                marker=dict(color='skyblue'),
                showlegend=False
            ))

        name_map = df.set_index("UID")["ActivityName"].to_dict()
        uid_time = df.set_index("UID")["Start"].to_dict()
        uid_end = df.set_index("UID")["Finish"].to_dict()

        for pred, succ in links:
            if pred in name_map and succ in name_map:
                fig.add_annotation(
                    x=uid_time[succ],
                    y=name_map[succ],
                    ax=uid_end[pred],
                    ay=name_map[pred],
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1,
                    arrowwidth=1,
                    opacity=0.6
                )

        fig.update_layout(
            title="Primavera Gantt Chart with Dependencies",
            xaxis_title="Date",
            yaxis_title="Activity",
            yaxis=dict(autorange="reversed"),
            height=800
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No valid activities found.")
