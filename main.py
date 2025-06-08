import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="XML-to-Gantt Converter", layout="wide")
st.title("📊 Gantt Chart from Primavera XML")

# File uploader
uploaded_xml = st.file_uploader("Upload Primavera XML file", type=["xml"])

def parse_primavera_xml(xml_file):
    # Parse XML with namespace
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {'p': root.tag.split('}')[0].strip('{')}

    # Extract activities
    activities = []
    for act in root.findall('.//p:Activity', ns):
        obj_id = act.find('p:ObjectId', ns).text
        aid = act.find('p:ActivityId', ns).text
        name = act.find('p:ActivityName', ns).text
        start = act.find('p:StartDate', ns).text
        finish = act.find('p:FinishDate', ns).text
        activities.append({
            'object_id': obj_id,
            'activity_id': aid,
            'name': name,
            'start': pd.to_datetime(start),
            'finish': pd.to_datetime(finish)
        })

    # Extract relationships
    links = []
    for rel in root.findall('.//p:Relationship', ns):
        pred = rel.find('p:PredecessorObjectId', ns).text
        succ = rel.find('p:SuccessorObjectId', ns).text
        links.append({'from': pred, 'to': succ})

    return pd.DataFrame(activities), links

if uploaded_xml:
    df_acts, links = parse_primavera_xml(uploaded_xml)
    st.subheader("Activities Table")
    st.dataframe(df_acts[['activity_id', 'name', 'start', 'finish']])

    # Build Gantt
    fig = go.Figure()
    for idx, row in df_acts.iterrows():
        fig.add_trace(go.Bar(
            x=[(row['finish'] - row['start']).days],
            y=[row['name']],
            base=row['start'],
            orientation='h',
            name=row['activity_id'],
            hovertemplate=f"{row['activity_id']}: {row['name']}<br>Start: {row['start']}<br>Finish: {row['finish']}"
        ))

    # Add dependency arrows
    id_map = {row['object_id']: idx for idx, row in df_acts.iterrows()}
    for link in links:
        if link['from'] in id_map and link['to'] in id_map:
            src = df_acts.loc[id_map[link['from']]]
            dst = df_acts.loc[id_map[link['to']]]
            # Arrow from end of src to start of dst
            fig.add_annotation(
                x=dst['start'],
                y=dst['name'],
                ax=src['finish'],
                ay=src['name'],
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=1
            )

    fig.update_layout(
        barmode='stack',
        xaxis_title='Date',
        yaxis_title='Activity',
        showlegend=False,
        height=600
    )

    st.subheader("Gantt Chart with Dependencies")
    st.plotly_chart(fig, use_container_width=True)
