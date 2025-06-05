import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="🗓️ Real Gantt Viewer", layout="wide")
st.title("🧩 Excel to Gantt Chart Converter")

uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]

        # Görev isimlerini area ile birleştir
        area_col = df.columns[0]
        task_col = df.columns[1]

        df[area_col].ffill(inplace=True)  # Kategorileri doldur
        df["Task"] = df[area_col].astype(str).str.strip() + " - " + df[task_col].astype(str).str.strip()

        time_cols = df.columns[2:]  # Tarih sütunları
        df_melt = df.melt(id_vars=["Task"], value_vars=time_cols, var_name="Date", value_name="Val")
        df_melt = df_melt[df_melt["Val"].notna() & (df_melt["Val"].astype(str).str.strip() != "")]

        df_melt["Start"] = pd.to_datetime(df_melt["Date"], errors="coerce")
        df_melt["Duration"] = pd.to_numeric(df_melt["Val"], errors="coerce").fillna(1).astype(int)
        df_melt["End"] = df_melt["Start"] + pd.to_timedelta(df_melt["Duration"], unit="D")

        df_gantt = df_melt[["Task", "Start", "End"]].copy()
        df_gantt.dropna(subset=["Start", "End"], inplace=True)

        st.subheader("📊 Gantt Chart")
        fig = px.timeline(df_gantt, x_start="Start", x_end="End", y="Task", title="Gantt Chart")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("Please upload an Excel file.")
