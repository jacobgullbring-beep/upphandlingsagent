import streamlit as st
import requests
import anthropic
import os

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# =========================================
# API KEY
# =========================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades")
    st.stop()

st.success("✅ Anthropic fungerar")

client = anthropic.Anthropic(
    api_key=api_key
)

# =========================================
# MERCELL URL
# =========================================

url = st.text_input(
    "Mercell URL",
    value="https://app.mercell.com/org/goteborgs_stads_upphandlingar"
)

# =========================================
# TEST MERCELL
# =========================================

if st.button("🚀 TESTA MERCELL"):

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        st.write("### Statuskod")
        st.write(response.status_code)

        st.write("### Antal tecken")
        st.write(len(response.text))

        st.write("### Förhandsvisning (första 5000 tecken)")

        st.text_area(
            "",
            response.text[:5000],
            height=400
        )

    except Exception as e:

        st.exception(e)

# =========================================
# TEST CLAUDE
# =========================================

if st.button("🤖 TESTA CLAUDE"):

    try:

        result = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Svara endast HELLO"
                }
            ]
        )

        st.success(result.content[0].text)

    except Exception as e:

        st.exception(e)
