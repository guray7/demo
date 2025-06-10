import pandas as pd
import json
from datetime import datetime
import os

# 1. .xer dosyasÄ±nÄ±n yolu
file_path = "3e8bd7ba-deeb-4166-9d38-2c426496c4f1.xer"

# 2. DosyayÄ± oku
with open(file_path, encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# 3. Tablo bloklarÄ±nÄ± ayÄ±r
table_blocks = {}
current_table = None
for line in lines:
    if line.startswith("%T\t"):
        current_table = line.strip().split("\t")[1]
        table_blocks[current_table] = []
    elif current_table:
        table_blocks[current_table].append(line.strip())

# 4. Temiz tablo dÃ¶nÃ¼ÅŸtÃ¼rÃ¼cÃ¼
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

# 5. TASK ve TASKPRED tablolarÄ±nÄ± al
df_task = clean_table(table_blocks["TASK"])
df_pred = clean_table(table_blocks["TASKPRED"])

# 6. Tarih dÃ¶nÃ¼ÅŸÃ¼mleri
df_task["early_start_date"] = pd.to_datetime(df_task["early_start_date"], errors="coerce")
df_task["early_end_date"] = pd.to_datetime(df_task["early_end_date"], errors="coerce")

# 7. Gantt gÃ¶rev verisi hazÄ±rla
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

# 8. BaÄŸÄ±mlÄ±lÄ±k (link) verisi hazÄ±rla
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

# 9. Gantt JSON verisini HTML iÃ§ine gÃ¶m
gantt_data = {"data": tasks_json, "links": links_json}
html_output = os.path.join(os.path.dirname(file_path), "gantt_output_embedded.html")

with open(html_output, "w", encoding="utf-8") as f:
    f.write(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gantt Output</title>
  <link rel="stylesheet" href="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.css">
  <script src="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.js"></script>
</head>
<body>
  <div id="gantt_here" style="width:100%; height:800px;"></div>
  <script>
    gantt.config.date_format = "%Y-%m-%d";
    gantt.init("gantt_here");
    var data = {json.dumps(gantt_data)};
    gantt.parse(data);
  </script>
</body>
</html>
""")

print("âœ… Gantt HTML baÅŸarÄ±yla oluÅŸturuldu!")
print(f"ðŸ“„ AÃ§mak iÃ§in: {html_output}")
