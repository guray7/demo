
import streamlit as st
import pandas as pd
import plotly.express as px
import json
#import requests  # Uncomment if integrating with real AI API

st.set_page_config(page_title="Shutdown AI Demo", layout="wide")

st.title("📊 Shutdown Delay Analysis Panel")

# File upload
uploaded_file = st.file_uploader("Upload your shutdown task CSV file", type=["csv"])

if uploaded_file:
    # Read CSV
    df = pd.read_csv(uploaded_file)

    # Preprocess for Gantt chart
    df["Start"] = pd.to_datetime(df["Start"])
    df["End"] = df["Start"] + pd.to_timedelta(df["Duration"], unit="D")

    # Show Gantt chart
    st.subheader("Gantt Chart")
    fig = px.timeline(df, x_start="Start", x_end="End", y="Task", color="Equipment")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    # Generate JSON for AI
    st.subheader("🔄 Data to be sent to AI")
    json_data = df[["Task", "Equipment", "Start", "Duration", "Crew Readiness", "Previous Duration", "Season"]]
    json_data = json_data.rename(columns={
        "Crew Readiness": "crew_readiness",
        "Previous Duration": "previous_duration",
        "Season": "season"
    })
    records = json_data.to_dict(orient="records")
    st.json(records)

    # Simulate AI interaction
    st.subheader("🤖 AI Interaction")
    if st.button("Simulate AI Questions"):
        for task in records:
            st.markdown(f"### 🛠 Task: {task['Task']}")
            st.markdown(f"**Q1:** Why is crew readiness only {task['crew_readiness']}%?")
            st.markdown(f"**Q2:** Has this equipment ({task['Equipment']}) experienced delays in {task['season']} previously?")
            st.markdown("---")

    # Optional: Send to real AI API
    # if st.button("Send to AI"):
    #     response = requests.post("https://your-ai-endpoint.com/analyze", json=records)
    #     st.write(response.json())

    # Optional: Download JSON
    st.download_button("⬇️ Download JSON for AI", json.dumps(records, indent=4), file_name="shutdown_data.json")

else:
    st.info("Please upload a CSV file to begin.")
