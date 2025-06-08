import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Primavera Gantt Viewer (.xml + .xer)", layout="wide")
st.title("📊 Primavera Gantt Chart with Dependencies (.xml or .xer)")

uploaded_file = st.file_uploader("📂 Upload Primavera XML or XER File", type=["xml", "xer"])

def parse_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    activities, links = [], []
    uid_to_name = {}

    for task in root.findall(".//{http://schemas.microsoft.com/project}Task"):
        uid_elem = task.find("{http://schemas.microsoft.com/project}UID")
        name_elem = task.find("{http://schemas.microsoft.com/project}Name")
        start_elem = task.find("{http://schemas.microsoft.com/project}Start")
        finish_elem = task.find("{http://schemas.microsoft.com/project}Finish")
        if None in (uid_elem, name_elem, start_elem, finish_elem):
            continue
        try:
            start = datetime.fromisoformat(start_elem.text.replace("Z", ""))
            finish = datetime.fromisoformat(finish_elem.text.replace("Z", ""))
        except:
            continue
        if start == finish:
            finish += timedelta(days=1)
        uid = uid_elem.text
        name = name_elem.text
        uid_to_name[uid] = name
        activities.append({"UID": uid, "ActivityName": name, "Start": start, "Finish": finish})

    for task in root.findall(".//{http://schemas.microsoft.com/project}Task"):
        uid_elem = task.find("{http://schemas.microsoft.com/project}UID")
        if uid_elem is None:
            continue
        uid = uid_elem.text
        for pred in task.findall("{http://schemas.microsoft.com/project}PredecessorLink"):
            pred_uid_elem = pred.find("{http://schemas.microsoft.com/project}PredecessorUID")
            if pred_uid_elem is not None:
                links.append((pred_uid_elem.text, uid))

    return pd.DataFrame(activities), links

def parse_xer(file):
    lines = file.read().decode(errors="ignore").splitlines()
    activities, links = [], []
    obj_to_name, obj_to_start, obj_to_finish = {}, {}, {}

    for line in lines:
        if line.startswith("TASK"):
            parts = line.split("\t")
            if len(parts) > 15:
                aid = parts[1]
                name = parts[4]
                start = parts[6]
                finish = parts[7]
                try:
                    start_dt = datetime.strptime(start, "%d-%b-%Y")
                    finish_dt = datetime.strptime(finish, "%d-%b-%Y")
                    if start_dt == finish_dt:
                        finish_dt += timedelta(days=1)
                    activities.append({"UID": aid, "ActivityName": name, "Start": start_dt, "Finish": finish_dt})
                except:
                    continue
        elif line.startswith("TASKPRED"):
            parts = line.split("\t")
            if len(parts) > 3:
                links.append((parts[1], parts[2]))

    return pd.DataFrame(activities), links

if uploaded_file:
    if uploaded_file.name.endswith(".xml"):
        df, links = parse_xml(uploaded_file)
    elif uploaded_file.name.endswith(".xer"):
        df, links = parse_xer(uploaded_file)
    else:
        st.error("Unsupported file type.")
        st.stop()

    st.success(f"✅ Found {len(df)} activities and {len(links)} dependencies")
    fig = go.Figure()

    for idx, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[(row['Finish'] - row['Start']).days],
            y=[row['ActivityName']],
            base=row['Start'],
            orientation='h',
            name=row['ActivityName'],
            hoverinfo='text',
            marker=dict(color='skyblue')
        ))

    uid_to_row = df.set_index("UID")

    for pred, succ in links:
        if pred in uid_to_row.index and succ in uid_to_row.index:
            pred_row = uid_to_row.loc[pred]
            succ_row = uid_to_row.loc[succ]
            fig.add_annotation(
                x=succ_row['Start'],
                y=succ_row['ActivityName'],
                ax=pred_row['Finish'],
                ay=pred_row['ActivityName'],
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=1,
                opacity=0.6
            )

    fig.update_layout(
        title="Gantt Chart with Dependencies",
        xaxis_title="Date",
        yaxis_title="Activity",
        showlegend=False,
        yaxis=dict(autorange='reversed')
    )
    st.plotly_chart(fig, use_container_width=True)
