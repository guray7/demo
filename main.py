import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.cache_data.clear()

st.set_page_config(page_title="Gantt Chart Generator", layout="wide")
st.title("📅 Shutdown Gantt Chart from Colored Excel Cells")

uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    df = xls.parse(xls.sheet_names[0])
    df.columns = df.iloc[0]
    df = df[1:].copy()
    df.columns = [str(c) for c in df.columns]

    # Benzersiz sütun isimleri oluştur
    used = {}
    new_cols = []
    for col in df.columns:
        if col in used:
            used[col] += 1
            new_cols.append(f"{col}_{used[col]}")
        else:
            used[col] = 0
            new_cols.append(col)
    df.columns = new_cols

    # Önemli başlıkları adlandır
    df = df.rename(columns={df.columns[0]: "Tie-in Point", df.columns[1]: "Tie-in Type", df.columns[2]: "SD Requirement"})

    # Gün kolonlarını bul
    day_columns = [col for col in df.columns if "day" in col or "night" in col]

    # Başlangıç ve bitiş gününü hesapla
    def detect_start_end(row):
        start, end = None, None
        for col in day_columns:
            val = str(row[col]).strip().lower()
            if val not in ["", "nan", "none"]:
                day_num = ''.join(filter(str.isdigit, col))
                if day_num == "":
                    day_num = "1"
                day = int(day_num)
                if start is None:
                    start = day
                end = day
        return pd.Series([start, end])

    df[['Start Day', 'End Day']] = df.apply(detect_start_end, axis=1)
    df_cleaned = df.dropna(subset=["Start Day"])

    # Tarihe çevir
    base_date = datetime.date.today()
    df_cleaned["Start Date"] = df_cleaned["Start Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x) - 1))
    df_cleaned["End Date"] = df_cleaned["End Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x) - 1))

    # Gantt grafiği oluştur
    fig = px.timeline(
        df_cleaned,
        x_start="Start Date",
        x_end="End Date",
        y="Tie-in Point",
        color="SD Requirement",
        title="📊 Shutdown Gantt Chart",
        labels={"Tie-in Point": "Task"}
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
