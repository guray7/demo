import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="📊 Shutdown Gantt with Arrows", layout="wide")
st.title("🔗 Gantt Chart with Dependencies (.csv or .xer)")

uploaded_file = st.file_uploader("📂 Upload a schedule (.csv only for now)", type=["csv"])

def draw_gantt_with_arrows(df_tasks, df_pred):
    df_tasks = df_tasks.copy()
    df_tasks["Start"] = pd.to_datetime(df_tasks["Start"])
    df_tasks["End"] = pd.to_datetime(df_tasks["End"])
    df_tasks["y_index"] = range(len(df_tasks))

    fig = go.Figure()
    for _, row in df_tasks.iterrows():
        fig.add_trace(go.Bar(
            x=[(row["End"] - row["Start"]).days],
            y=[row["y_index"]],
            base=row["Start"],
            orientation='h',
            name=row["Task"],
            hovertext=f"{row['Task']}: {row['Start'].date()} → {row['End'].date()}",
            marker=dict(color="skyblue")
        ))

    if df_pred is not None:
        for _, link in df_pred.iterrows():
            pred = df_tasks[df_tasks["Task ID"] == link["Predecessor"]]
            succ = df_tasks[df_tasks["Task ID"] == link["Successor"]]
            if not pred.empty and not succ.empty:
                fig.add_annotation(
                    x=succ.iloc[0]["Start"], y=succ.iloc[0]["y_index"],
                    ax=pred.iloc[0]["End"], ay=pred.iloc[0]["y_index"],
                    showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2,
                    arrowcolor="red"
                )

    fig.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=df_tasks["y_index"],
            ticktext=df_tasks["Task"]
        ),
        height=600,
        title="🗂 Gantt Chart with Dependencies"
    )
    return fig

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        required_cols = {"Task ID", "Task", "Start", "End"}
        if not required_cols.issubset(set(df.columns)):
            st.error("CSV must contain: Task ID, Task, Start, End")
        else:
            df_pred = None
            if {"Predecessor", "Successor"}.issubset(set(df.columns)):
                df_pred = df[["Predecessor", "Successor"]]

            st.success("File uploaded successfully!")
            chart = draw_gantt_with_arrows(df, df_pred)
            st.plotly_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a .csv file to begin.")
