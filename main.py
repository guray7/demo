import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="XML to Gantt Viewer", layout="wide")
st.title("📊 Primavera XML to Gantt Chart with Dependencies")

uploaded_file = st.file_uploader("📂 Upload Primavera XML File", type=["xml"])

if uploaded_file:
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    activities = []
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
        except Exception:
            continue

        uid = uid_elem.text
        name = name_elem.text
        uid_to_name[uid] = name

        activities.append({
            "UID": uid,
            "ActivityName": name,
            "Start": start,
            "Finish": finish
        })

    links = []
    for task in root.findall(".//{http://schemas.microsoft.com/project}Task"):
        uid_elem = task.find("{http://schemas.microsoft.com/project}UID")
        if uid_elem is None:
            continue
        uid = uid_elem.text
        for pred in task.findall("{http://schemas.microsoft.com/project}PredecessorLink"):
            pred_uid_elem = pred.find("{http://schemas.microsoft.com/project}PredecessorUID")
            if pred_uid_elem is not None:
                links.append((pred_uid_elem.text, uid))

    if activities:
        df = pd.DataFrame(activities)
        st.write("✅ Found", len(df), "activities and", len(links), "dependencies")

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

        for pred, succ in links:
            if pred in uid_to_name and succ in uid_to_name:
                pred_row = df[df['UID'] == pred]
                succ_row = df[df['UID'] == succ]
                if not pred_row.empty and not succ_row.empty:
                    x0 = pred_row.iloc[0]['Finish']
                    y0 = pred_row.iloc[0]['ActivityName']
                    x1 = succ_row.iloc[0]['Start']
                    y1 = succ_row.iloc[0]['ActivityName']
                    fig.add_annotation(
                        x=x1,
                        y=y1,
                        ax=x0,
                        ay=y0,
                        xref='x',
                        yref='y',
                        axref='x',
                        ayref='y',
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
    else:
        st.warning("No valid activities found in the uploaded XML file.")
