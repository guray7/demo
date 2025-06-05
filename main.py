import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="📊 Shutdown Delay Analysis Panel (.csv & .xer)", layout="wide")
st.title("🔗 Shutdown Gantt Chart Viewer (.csv & .xer)")

col1, col2 = st.columns(2)

with col1:
    uploaded_file_1 = st.file_uploader("📂 Upload Baseline Schedule (.csv or .xer)", type=["csv", "xer"], key="baseline")
with col2:
    uploaded_file_2 = st.file_uploader("📂 Upload Actual Schedule (.csv or .xer)", type=["csv", "xer"], key="actual")

# Dummy parse_xer fallback for now (since not fully implemented)
def parse_xer(file):
    st.warning("⚠️ XER file support is not yet implemented. Please use CSV for now.")
    return None, None

def read_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        df["End"] = pd.to_datetime(df["End"], errors="coerce")
        df.dropna(subset=["Start", "End"], inplace=True)
        return df, None
    elif filename.endswith(".xer"):
        return parse_xer(uploaded_file)
    else:
        st.error("Unsupported file type.")
        return None, None

def draw_gantt_chart(df):
    df = df.copy()
    df["y_index"] = range(len(df))

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[(row["End"] - row["Start"]).days],
            y=[row["y_index"]],
            base=row["Start"],
            orientation='h',
            name=row["Task"],
            hovertext=f"{row['Task']}: {row['Start'].date()} → {row['End'].date()}",
            marker=dict(color="skyblue")
        ))

    fig.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=df["y_index"],
            ticktext=df["Task"]
        ),
        height=600,
        title="📅 Gantt Chart (Dependencies temporarily disabled for .csv mode)"
    )
    return fig

if uploaded_file_1:
    df1, _ = read_file(uploaded_file_1)
    if df1 is not None:
        with col1:
            st.subheader("📅 Baseline Gantt Chart")
            fig1 = draw_gantt_chart(df1)
            st.plotly_chart(fig1, use_container_width=True)

if uploaded_file_2:
    df2, _ = read_file(uploaded_file_2)
    if df2 is not None:
        with col2:
            st.subheader("📅 Actual Gantt Chart")
            fig2 = draw_gantt_chart(df2)
            st.plotly_chart(fig2, use_container_width=True)

if not uploaded_file_1 and not uploaded_file_2:
    st.info("Please upload at least one .csv or .xer schedule file to begin.")
