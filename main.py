import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gantt Chart Viewer", layout="wide")
st.title("📊 Simple Gantt Chart Viewer (.xlsx with Matrix Format)")

uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]

        # Task sütunu kontrol
        task_col = next((col for col in df.columns if "task" in col.lower() or "tie-in" in col.lower()), None)
        if not task_col:
            df.insert(0, "Task", [f"Task {i+1}" for i in range(len(df))])
        else:
            df.rename(columns={task_col: "Task"}, inplace=True)

        static_cols = ["Task"]
        other_static = [col for col in df.columns if col not in static_cols and not re.match(r"\\d+", col)]
        static_cols += other_static
        time_columns = [col for col in df.columns if col not in static_cols]

        df_long = df.melt(id_vars=static_cols, value_vars=time_columns, var_name="Slot", value_name="Value")
        df_long = df_long[df_long["Value"].notna() & (df_long["Value"].astype(str).str.strip() != "")]

        def slot_to_datetime(slot):
            match = re.match(r"(\\d+)\\s*(day|night)?", slot.lower())
            if match:
                day = int(match.group(1))
                shift = match.group(2)
                base = pd.to_datetime("2022-01-01")  # Başlangıç tarihi
                hour_offset = 8 if shift == "day" else 20 if shift == "night" else 0
                start = base + pd.Timedelta(days=day - 1, hours=hour_offset)
                end = start + pd.Timedelta(hours=8)
                return start, end
            return None, None

        df_long[["Start", "End"]] = df_long["Slot"].apply(lambda x: pd.Series(slot_to_datetime(x)))
        df_result = df_long[["Task", "Start", "End"]].dropna()
        df_result["Duration"] = (df_result["End"] - df_result["Start"]).dt.total_seconds() / 3600

        st.subheader("📅 Gantt Chart")
        fig = px.timeline(df_result, x_start="Start", x_end="End", y="Task")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("Please upload an Excel file in matrix format.")
