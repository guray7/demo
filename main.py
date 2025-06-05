import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.cache_data.clear()


st.set_page_config(page_title="Gantt Chart Generator", layout="wide")
st.title("📅 Shutdown Gantt Chart Demo")

uploaded_file = st.file_uploader("Upload your Schedule File (.csv, .xlsx, .xer)", type=["csv", "xlsx", "xer"])

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        df = xls.parse(xls.sheet_names[0])
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.error("❌ .xer dosyası henüz desteklenmiyor.")
        st.stop()

    # İlk satırı başlık yap ve eski başlıkları at
    df.columns = df.iloc[0]
    df = df[1:].copy()

    # Sütun adlarını string yap ve benzersiz hale getir
    df.columns = [str(col) for col in df.columns]
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

    # İlk 3 sütunu yeniden adlandır
    df = df.rename(columns={df.columns[0]: "Tie-in Point", df.columns[1]: "Tie-in Type", df.columns[2]: "SD Requirement"})
    df = df.reset_index(drop=True)

    # Başlangıç ve bitiş günü çıkar
    def get_start_end_days(row):
        day_columns = [col for col in df.columns if col.strip().isdigit()]
        start_day, end_day = None, None
        for day in day_columns:
            if not pd.isna(row[day]):
                if start_day is None:
                    start_day = int(day)
                end_day = int(day)
        return pd.Series([start_day, end_day])

    df[['Start Day', 'End Day']] = df.apply(get_start_end_days, axis=1)
    df_cleaned = df.dropna(subset=["Start Day"])

    # Günleri tarihe çevir
    base_date = datetime.date.today()
    df_cleaned["Start Date"] = df_cleaned["Start Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))
    df_cleaned["End Date"] = df_cleaned["End Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))

    # Gantt grafiğini çiz
    fig = px.timeline(
        df_cleaned,
        x_start="Start Date",
        x_end="End Date",
        y="Tie-in Point",
        color="SD Requirement",
        title="Shutdown Gantt Chart",
        labels={"Tie-in Point": "Task"},
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
