import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io

st.title("🛠️ .xer to Gantt JSON Converter")

uploaded_file = st.file_uploader("📂 Upload your .xer file", type=["xer"])

if uploaded_file:
    lines = uploaded_file.read().decode(errors="ignore").splitlines()

    # Tablo bloklarını ayrıştır
    table_blocks = {}
    current_table = None
    for line in lines:
        if line.startswith("%T\t"):
            current_table = line.strip().split("\t")[1]
            table_blocks[current_table] = []
        elif current_table:
            table_blocks[current_table].append(line.strip())

    def clean_table(raw_rows):
        rows = [row.split("\t") for row in raw_rows]
        header = rows[0]
        data = []
        for row in rows[1:]:
            if len(row) < len(header):
                row += [""] * (len(header) - len(row))
            elif len(row) > len(header):
                row = row[:len(header)]
            data.append(row)
        return pd.DataFrame(data, columns=header)

    df_task = clean_table(table_blocks["TASK"])
    df_pred = clean_table(table_blocks["TASKPRED"])
    
    df_task["early_start_date"] = pd.to_datetime(df_task["early_start_date"], errors="coerce")
    df_task["early_end_date"] = pd.to_datetime(df_task["early_end_date"], errors="coerce")

    tasks_json = []
    for _, row in df_task.iterrows():
        if pd.notna(row["early_start_date"]) and pd.notna(row["early_end_date"]):
            start = row["early_start_date"]
            end = row["early_end_date"]
            duration = max((end - start).days, 1)
            tasks_json.append({
                "id": int(row["task_id"]),
                "text": row["task_name"],
                "start_date": start.strftime("%Y-%m-%d"),
                "duration": duration
            })

    link_type_map = {
        "PR_FS": "0", "PR_SS": "1", "PR_FF": "2", "PR_SF": "3"
    }
    links_json = []
    for i, row in df_pred.iterrows():
        if row["pred_type"] in link_type_map:
            links_json.append({
                "id": i + 1,
                "source": int(row["pred_task_id"]),
                "target": int(row["task_id"]),
                "type": link_type_map[row["pred_type"]]
            })

    gantt_data = {"data": tasks_json, "links": links_json}
    gantt_json_str = json.dumps(gantt_data, indent=2)

    st.download_button("⬇️ Download JSON", gantt_json_str, file_name="gantt_data.json")

    st.code(gantt_json_str, language="json")
