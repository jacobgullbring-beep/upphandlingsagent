import streamlit as st
import pandas as pd
import anthropic
import os
import json

# ======================================
# Page Setup
# ======================================

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# ======================================
# Claude
# ======================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("❌ ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(
    api_key=api_key
)

st.success("✅ Claude ansluten")

# ======================================
# Upload
# ======================================

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.write("Kolumner hittade:")

    st.write(df.columns.tolist())

    st.dataframe(df)

    antal = st.slider(
        "Antal upphandlingar att analysera",
        min_value=1,
        max_value=min(len(df), 20),
        value=min(len(df), 5)
    )

    if st.button("🚀 Analysera upphandlingar"):

        resultat = []

        progress = st.progress(0)

        rows = df.head(antal)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])
            value = str(row["Value"])
            link = str(row["Link"])

            prompt = f"""
Du arbetar som senior bid manager för
PA Consulting Defence & Security.

Bedöm om denna upphandling är relevant för:

- PMO
- Programledning
- Transformation
- Förändringsledning
- Governance
-
