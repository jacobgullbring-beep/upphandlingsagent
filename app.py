import streamlit as st
import pandas as pd
import anthropic
import os
import re
from io import BytesIO

# =====================================
# PAGE
# =====================================

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
# FILE UPLOAD
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
        min(20, len(df)),
        min(10, len(df))
    )

    if st.button("🚀 Analysera"):

        resultat = []

        rows = df.head(antal)

        progress = st.progress(0)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])
            value = str(row["Value"])
            link = str(row["Link"])

            prompt = (
                "Du arbetar för PA Consulting Defence & Security.\n\n"

                "Bedöm INTE om kunden är militär.\n"

                "Bedöm om PA kan sälja:\n"
                "- PMO\n"
                "- Programledning\n"
                "- Transformation\n"
                "- Förändringsledning\n"
                "- Governance\n"
                "- Operating Model\n"
                "- Risk\n"
                "- Resiliens\n"
                "- Beredskap\n"
                "- Säkerhetsskydd\n"
                "- Informationssäkerhet\n"
                "- Cybersäkerhet\n"
                "- Verksamhetsutveckling\n"
                "- Ledningsstöd\n\n"

                "Returnera exakt:\n\n"

                "SCORE: X\n"
                "CATEGORY: Y\n"
                "REASON: Z\n\n"

                f"Organisation: {organisation}\n"
                f"Titel: {title}\n"
                f"Beskrivning: {description}\n"
                f"Värde: {value}"
            )

            try:

       
