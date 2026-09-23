import streamlit as st
import pandas as pd
import anthropic
import json
import os

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")
st.write("BUILD: CSV TEST V1")

# ===============================
# CLAUDE
# ===============================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# ===============================
# UPPLADDNING
# ===============================

uploaded_file = st.file_uploader(
    "Ladda upp Excel eller CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📋 Förhandsvisning")

    st.
