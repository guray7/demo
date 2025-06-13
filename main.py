import streamlit as st
import json
import tempfile
from datetime import datetime
from xer_to_gantt import XerParser, GanttConverter  # Bu senin yukarıdaki kodun .py dosyasına kaydedilmeli

st.cache_resource.clear()

st.set_page_config(page_title="🛠️ XER to Gantt JSON Converter", layout="centered")
st.title("📄 Primavera .xer → 📊 DHTMLX Gantt JSON")

uploaded_file = st.file_uploader("📂 Lütfen .xer dosyanızı yükleyin", type=["xer"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    try:
        with st.spinner("⏳ Dosya işleniyor..."):
            parser = XerParser(tmp_path)
            tables = parser.parse()
            converter = GanttConverter(tables)
            gantt_data = converter.convert()

        st.success("✅ Başarıyla dönüştürüldü!")

        st.download_button(
            label="📥 JSON çıktısını indir",
            data=json.dumps(gantt_data, indent=2),
            file_name="gantt_output.json",
            mime="application/json"
        )

        if st.checkbox("📋 JSON çıktısını TAMAMEN göster"):
            json_str = json.dumps(gantt_data, indent=2, ensure_ascii=False)
            st.text_area("📄 JSON Çıktısı (Tamamı)", json_str, height=600)


    except Exception as e:
        st.error(f"❌ Hata: {e}")
