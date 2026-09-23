import streamlit as st
import pandas as pd
import anthropic
import requests
import json
import os

st.set_page_config(
    page_title="PA D&S Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

MERCELL_ORGS = {
    "Göteborg":
        "https://app.mercell.com/org/goteborgs_stads_upphandlingar",

    "Lund":
        "https://app.mercell.com/org/lunds_kommuns_upphandlingar",

    "Haninge":
        "https://app.mercell.com/org/haninge_kommun",

    "Jönköping":
        "https://app.mercell.com/org/jonkopings_kommun"
}

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(
    api_key=api_key
)

def get_pages(base_url, max_pages):

    urls = []

    for p in range(1, max_pages + 1):

        if p == 1:
            urls.append(base_url)

        else:
            urls.append(
                f"{base_url}?page={p}"
            )

    return urls

def fetch_page(url):

    try:

        r = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        return r.text

    except Exception:

        return ""

def analyse_with_claude(text):

    prompt = f"""
Du arbetar för PA Consulting Defence & Security.

Analysera innehållet.

Identifiera:

1. Upphandlingar
2. Programledning
3. PMO
4. Transformation
5. Beredskap
6. Säkerhet
7. Management Consulting

Returnera JSON:

[
 {{
   "title":"",
   "organisation":"",
   "score":0,
   "category":"",
   "reason":""
 }}
]

Text:

{text}
"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return msg.content[0].text

col1, col2 = st.columns(2)

with col1:

    max_pages = st.slider(
        "Antal sidor att läsa",
        1,
        20,
        5
    )

with col2:

    selected_orgs = st.multiselect(
        "Kommuner",
        list(MERCELL_ORGS.keys()),
        default=list(MERCELL_ORGS.keys())
    )

if st.button("🚀 Scan Opportunities"):

    raw_text = ""

    progress = st.progress(0)

    total = len(selected_orgs)

    counter = 0

    for org in selected_orgs:

        base_url = MERCELL_ORGS[org]

        pages = get_pages(
            base_url,
            max_pages=max_pages
        )

        for page in pages:

            html = fetch_page(page)

            raw_text += html[:20000]

        counter += 1

        progress.progress(counter / total)

    st.success("Insamling klar")

    with st.spinner("Claude analyserar..."):

        result = analyse_with_claude(
            raw_text[:150000]
        )

    st.subheader("Claude Resultat")

    st.code(result)
