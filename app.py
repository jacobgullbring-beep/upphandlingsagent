import streamlit as st
import anthropic
import requests
import os
from bs4 import BeautifulSoup
import json

st.set_page_config(
    page_title="PA D&S Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.markdown("""
### Syfte

Klistra in:

- En upphandlingslänk
- Eller upphandlingstext

AI bedömer:

- Relevans för PA Defence & Security
- PMO
- Programledning
- Transformation
- Beredskap
- Säkerhetsskydd
- Värdeuppskattning
""")

url = st.text_input(
    "Mercell eller annan upphandlingslänk"
)

manual_text = st.text_area(
    "Eller klistra in upphandlingstext",
    height=250
)

def fetch_url(url):

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return soup.get_text(
            separator=" ",
            strip=True
        )

    except Exception as e:

        return f"ERROR: {e}"

if st.button("🚀 Analysera upphandling"):

    source_text = ""

    if url:

        with st.spinner("Hämtar sida..."):

            source_text = fetch_url(url)

    elif manual_text:

        source_text = manual_text

    else:

        st.warning(
            "Klistra in en länk eller text"
        )

        st.stop()

    with st.spinner("Claude analyserar..."):

        prompt = f"""
Du är bid manager för PA Consulting Defence & Security.

Bedöm om denna upphandling är relevant.

Fokusera på:

- Transformation
- Programledning
- PMO
- Förändringsledning
- Verksamhetsutveckling
- Beredskap
- Säkerhetsskydd
- Totalförsvar

Returnera endast JSON.

Format:

{{
 "score": 0,
 "recommendation": "",
 "category": "",
 "estimated_value": "",
 "summary": "",
 "reason": ""
}}

Text:

{source_text[:30000]}
"""

        try:

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[
                    {
                        "role":"user",
                        "content":prompt
                    }
                ]
            )

            result = response.content[0].text

            st.subheader("🎯 AI-bedömning")

            st.code(
                result,
                language="json"
            )

        except Exception as e:

            st.exception(e)
