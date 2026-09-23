import streamlit as st
import pandas as pd
import anthropic
import requests
import os
import json

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# =========================
# KÄLLOR
# =========================

MERCELL_SOURCES = {
    "Göteborg":
        "https://app.mercell.com/org/goteborgs_stads_upphandlingar",

    "Haninge":
        "https://app.mercell.com/org/haninge_kommun",

    "Lund":
        "https://app.mercell.com/org/lunds_kommuns_upphandlingar",

    "Jönköping":
        "https://app.mercell.com/org/jonkopings_kommun"
}

# =========================
# ANTHROPIC
# =========================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(
    api_key=api_key
)

# =========================
# HJÄLPFUNKTIONER
# =========================

def generate_pages(base_url, max_pages):

    urls = []

    for page in range(1, max_pages + 1):

        if page == 1:
            urls.append(base_url)
        else:
            urls.append(f"{base_url}?page={page}")

    return urls


def fetch_page(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        return response.text

    except Exception as e:

        return f"ERROR: {str(e)}"


def analyse_with_claude(text):

    prompt = f"""
Du arbetar för PA Consulting Defence & Security.

Analysera innehållet.

Identifiera om texten innehåller:

- Programledning
- PMO
- Transformation
- Förändringsledning
- Beredskap
- Säkerhet
- Management Consulting

Returnera ENDAST giltig JSON.

Format:

[
  {{
    "organisation": "",
    "title": "",
    "score": 0,
    "category": "",
    "reason": ""
  }}
]

Text:

{text}
"""

    try:

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    except Exception as e:

        st.error("Claude fel")

        st.exception(e)

        return "[]"


# =========================
# UI
# =========================

col1, col2 = st.columns(2)

with col1:

    max_pages = st.slider(
        "Antal sidor",
        1,
        10,
        3
    )

with col2:

    selected_sources = st.multiselect(
        "Kommuner",
        list(MERCELL_SOURCES.keys()),
        default=["Göteborg"]
    )

if st.button("🚀 Scan Opportunities"):

    all_text = ""

    progress = st.progress(0)

    total = len(selected_sources)

    current = 0

    for source in selected_sources:

        base_url = MERCELL_SOURCES[source]

        urls = generate_pages(
            base_url,
            max_pages
        )

        for url in urls:

            page_text = fetch_page(url)

            all_text += page_text[:10000]

        current += 1

        progress.progress(current / total)

    st.success("Insamling klar")

    st.subheader("Debug")

    st.write(
        f"Totalt antal tecken hämtade: {len(all_text)}"
    )

    st.text_area(
        "Förhandsvisning",
        all_text[:5000],
        height=250
    )

    if len(all_text) < 500:

        st.warning(
            "Mercell returnerade nästan ingen data. Då måste vi använda Playwright."
        )

    with st.spinner("Claude analyserar...")
