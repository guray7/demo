import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.cache_data.clear()


st.set_page_config(page_title="Gantt Chart Generator", layout="wide")
st.title("📅 Shutdown Gantt Chart Demo")

uploaded_file = st.file_uploader("Upload your Schedule File (.csv, .xlsx, .xer)", type=["csv", "xlsx", "xer"])

if uploaded_file:
    # 📄 Dosya tipine göre oku
    if uploaded_file.name.endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        df = xls.parse(xls.sheet_names[0])
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.error("❌ .xer dosya işleme özelliği henüz aktif değil.")
        st.stop()

    # 🧹 Başlık satırını düzelt ve duplicate sütunları çöz
    df.columns = df.iloc[0]  # ilk satır başlık gibi
    df = df[1:]
    df.columns = pd.io.parsers.ParserBase({'names': df.columns})._maybe_dedup_names(df.columns)
    df = df.rename(columns={df.columns[0]: "Tie-in Point", df.columns[1]: "Tie-in Type", df.columns[2]: "SD Requirement"})
    df = df.reset_index(drop=True)

    # 📅 Başlangıç ve bitiş günlerini çıkar
    def get_start_end_days(row):
        day_columns = [col for col in df.columns if str(col).strip().isdigit()]
        start_day, end_day = None, None
        for day in day_columns:
            if not pd.isna(row[day]):
                if start_day is None:
                    start_day = int(day)
                end_day = int(day)
        return pd.Series([start_day, end_day])

    df[['Start Day', 'End Day']] = df.apply(get_start_end_days, axis=1)
    df_cleaned = df.dropna(subset=["Start Day"])

    # 🎯 Tarihlere çevir
    base_date = datetime.date.today()
    df_cleaned["Start Date"] = df_cleaned["Start Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))
    df_cleaned["End Date"] = df_cleaned["End Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))

    # 📊
