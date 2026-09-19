import streamlit as st
from google import genai
import os

st.title("Test av Gemini API")

# Hämta nyckeln
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Ingen API-nyckel hittades i Secrets.")
    st.stop()

# Skapa klienten enligt nya SDK:n
client = genai.Client(api_key=api_key)

if st.button("Kör enkel test-fråga"):
    try:
        # Enkel fråga som inte kräver webbsökning eller externa hemsidor
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Svara bara med ett ord: Fungerar det?",
        )
        st.success(f"Svar från Gemini: {response.text}")
    except Exception as e:
        st.error(f"Ett fel uppstod: {e}")
