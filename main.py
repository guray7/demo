import streamlit as st
import pandas as pd
import plotly.express as px

st.cache_data.clear()
st.set_page_config(page_title="📅 5-Month Lookahead Gantt", layout="wide")
st.title("📊 Gantt Chart from 5-Month Lookahead Excel")

uploaded_file = st.file_uploader("Upload your .xlsx file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Başlık satırını düzelt
    df.columns = df.iloc[0]
    df = df[1:].copy()

    # İlgili sütunları adlandır
    df = df.rename(columns={df.columns[0]: "Area", df.columns[1]: "Activity"})

    # Tarih sütunlarını belirle (3. sütundan sonrası)
    date_cols = df.columns[2:]

    # Başlangıç ve bitiş tarihini bul
    def find_start_end(row):
        start, end = None, None
        for col in date_cols:
            val = str(row[col]).strip()
            if val == "1":
                if start is None:
                    start = col
                end = col
        return pd.Series([start, end])

    df[["Start", "End"]] = df.apply(find_start_end, axis=1)
    df_cleaned = df.dropna(subset=["Start", "End"])

    # Gantt çizimi
    fig = px.timeline(
        df_cleaned,
        x_start="Start",
        x_end="End",
        y="Activity",
        color="Area",
        title="🗓 5-Month Lookahead Gantt Chart",
        labels={"Activity": "Task"},
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
