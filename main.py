import streamlit as st
import pandas as pd
import plotly.express as px
import datetime


st.cache_data.clear()

st.set_page_config(page_title="Gantt Chart Generator", layout="wide")
st.title("📅 Shutdown Gantt Chaaaaaaaart Demo")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    df = xls.parse(xls.sheet_names[0])  # Assume first sheet

    # Fix headers
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.rename(columns={df.columns[0]: "Tie-in Point", df.columns[1]: "Tie-in Type", df.columns[2]: "SD Requirement"})
    df = df.reset_index(drop=True)

    # Extract start and end days
    def get_start_end_days(row):
        day_columns = [col for col in df.columns if isinstance(col, (int, float)) or (isinstance(col, str) and col.strip().isdigit())]
        start_day, end_day = None, None
        for day in day_columns:
            if not pd.isna(row[day]):
                if start_day is None:
                    start_day = int(day)
                end_day = int(day)
        return pd.Series([start_day, end_day])

    df[['Start Day', 'End Day']] = df.apply(get_start_end_days, axis=1)
    df_cleaned = df.dropna(subset=["Start Day"])

    # Assume Day 1 = today
    base_date = datetime.date.today()
    df_cleaned["Start Date"] = df_cleaned["Start Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))
    df_cleaned["End Date"] = df_cleaned["End Day"].apply(lambda x: base_date + datetime.timedelta(days=int(x)-1))

    # Draw Gantt
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
