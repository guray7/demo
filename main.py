import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
from datetime import datetime
st.cache_resource.clear()


st.set_page_config(page_title="XML to Gantta Viewer", layout="wide")
st.title("📊 Primavera XML to Gantt Chart")

uploaded_file = st.file_uploader("📂 Upload Primavera XML File", type=["xml"])

if uploaded_file:
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    ns = {'ns': 'http://schemas.microsoft.com/project'}

    activities = []
    for task in root.findall(".//ns:Task", ns):
        if task.find("ns:UID", ns) is None or task.find("ns:Name", ns) is None:
            continue

        uid = task.find("ns:UID", ns).text
        name = task.find("ns:Name", ns).text
        start_elem = task.find("ns:Start", ns)
        finish_elem = task.find("ns:Finish", ns)

        if start_elem is None or finish_elem is None:
            continue

        try:
            start = datetime.fromisoformat(start_elem.text.replace("Z", ""))
            finish = datetime.fromisoformat(finish_elem.text.replace("Z", ""))
        except Exception:
            continue

        activities.append({
            "ActivityId": uid,
            "ActivityName": name,
            "StartDate": start,
            "FinishDate": finish
        })

    if activities:
        df_acts = pd.DataFrame(activities)
        st.dataframe(df_acts[['ActivityId', 'ActivityName', 'StartDate', 'FinishDate']])
        fig = px.timeline(df_acts, x_start="StartDate", x_end="FinishDate", y="ActivityName")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid activities found in the uploaded XML file.")
