import streamlit as st
import anthropic
import os

st.set_page_config(
    page_title="PA Test",
    page_icon="🛡️"
)

st.title("🛡️ PA Defence & Security Test")

# =====================
# API KEY
# =====================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("❌ Ingen Anthropic API-nyckel hittades")
    st.stop()

st.success("✅ API-nyckel hittad")

# =====================
# CLIENT
# =====================

client = anthropic.Anthropic(
    api_key=api_key
)

# =====================
# TEST BUTTON
# =====================

if st.button("TEST CLAUDE"):

    try:

        with st.spinner("Testing Claude..."):

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": "Svara endast HELLO"
                    }
                ]
            )

        st.success("✅ Claude fungerar")

        st.write(response.content[0].text)

    except Exception as e:

        st.error("❌ Claude fel")

        st.exception(e)
