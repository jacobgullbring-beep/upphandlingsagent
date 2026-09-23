import streamlit as st
import pandas as pd
import anthropic
import os
import json
from io import BytesIO

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# ===================================================
# CLAUDE
# ===================================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

st.markdown("""
Ladda upp:

- Excel (.xlsx)
- CSV (.csv)

AI bedömer:

✅ PMO

✅ Programledning

✅ Transformation

✅ Förändringsledning

✅ Verksamhetsutveckling

✅ Beredskap

✅ Risk

✅ Resiliens

✅ Säkerhetsskydd

✅ Informationssäkerhet

✅ Cybersäkerhet

✅ Totalförsvar

✅ Governance

✅ Operating Model
""")

# ===================================================
# UPPLADDNING
# ===================================================

uploaded_file = st.file_uploader(
    "Ladda upp Excel eller CSV",
    type=["xlsx", "csv"]
)

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Förhandsvisning")

    st.dataframe(
        df.head(),
        use_container_width=True
    )

    # ===================================================
    # KOLUMNER
    # ===================================================

    st.subheader("Mappa kolumner")

    title_col = st.selectbox(
        "Titel-kolumn",
        df.columns
    )

    org_col = st.selectbox(
        "Organisation-kolumn",
        df.columns
    )

    description_col = st.selectbox(
        "Beskrivning/Upphandlingstext",
        df.columns
    )

    value_col = st.selectbox(
        "Värde-kolumn",
        df.columns
    )

    link_col = st.selectbox(
        "Länk-kolumn",
        df.columns
    )

    max_rows = st.slider(
        "Antal rader att analysera",
        min_value=1,
        max_value=min(50, len(df)),
        value=min(10, len(df))
    )

    # ===================================================
    # ANALYS
    # ===================================================

    if st.button("🚀 Analysera upphandlingar"):

        results = []

        rows = df.head(max_rows)

        progress = st.progress(0)

        for i, (_, row) in enumerate(rows.iterrows()):

            title = str(row[title_col])
            organisation = str(row[org_col])
            description = str(row[description_col])
            value = str(row[value_col])
            link = str(row[link_col])

            prompt = f"""
Du arbetar som 
