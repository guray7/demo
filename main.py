import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="XML to Gantt Viewer", layout="wide")
st.title("📊 Primavera XML to Gantt Chart (Stable)")

uploaded_file = st.file_uploader("📂 Upload Primavera XML File", type=["xml"])

if uploaded_file:
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    activities = []
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

        if start == finish:
            finish = finish + pd.Timedelta(days=1)

        activities.append({
            "ActivityId": uid_elem.text,
            "ActivityName": name_elem.text,
            "StartDate": start,
            "FinishDate": finish
        })

    if activities:
        df = pd.DataFrame(activities)
        st.success(f"✅ Found {len(df)} activities")
        st.dataframe(df[['ActivityId', 'ActivityName', 'StartDate', 'FinishDate']])

        fig = px.timeline(
            df,
            x_start="StartDate",
            x_end="FinishDate",
            y="ActivityName",
            title="Primavera Gantt Chart",
            labels={"ActivityName": "Activity"}
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=600, xaxis_title="Date", yaxis_title="Activity")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid activities found in the uploaded XML file.")
