import streamlit as st
import pandas as pd
import anthropic
import os
from io import BytesIO

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# =====================================
# CLAUDE
# =====================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# =====================================
# CSV
# =====================================

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.dataframe(df)

    antal = st.slider(
        "Antal upphandlingar",
        1,
        min(len(df), 20),
        min(len(df), 10)
    )

    if st.button("🚀 Analysera"):

        resultat = []

        progress = st.progress(0)

        rows = df.head(antal)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])
            value = str(row["Value"])
        
