import streamlit as st
import pandas as pd
import anthropic
import json
import os
from io import BytesIO

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# ==================================================
# API KEY
# ==================================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Ladda upp Excel eller CSV",
    type=["xlsx", "csv"]
)

if uploaded_file:

    # Läs fil
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Förhandsvisning")

    st.dataframe(
        df.head(),
        use_container_width=True
    )

    # ==================================================
    # COLUMN MAPPING
    # ==============
