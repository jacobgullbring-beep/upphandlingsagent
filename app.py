import streamlit as st
import pandas as pd
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsbevakning - Kategorisering", page_icon="🛡️", layout="wide")

st.title("🛡️ GTM Säljbevakning – Veckans Kategoriserade Överblick")
st.write("Klistra in råtexten från upphandlingsportalen så strukturerar och kategoriserar Claude alla ärenden utan att sålla bort något.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Textruta för att klistra in urklipp
raw_clipboard = st.text_area(
    "📋 Klistra in texten här (Ctrl+A -> Ctrl+C från webbsidan):",
    height=250,
    placeholder="Klistra in allt innehåll från sidan här..."
)

if st.button("🚀 Kategorisera alla upphandlingar", type="primary"):
    if not raw_clipboard.strip():
        st.warning("Vänligen klistra in lite text i rutan först!")
    else:
        with st.spinner("Claude går igenom och kategoriserar samtliga upphandlingar..."):
            prompt = f"""
            Du är en expert på Business Development / Go-To-Market (GTM) för konsultbolag inom offentlig sektor.
            
            Här är råtext kopierad direkt från en upphandlingsportal:
            ---
            {raw_clipboard}
            ---
            
            Uppgift:
            1. Gå igenom texten och fånga upp **samtliga** separata upphandlingar, avtal eller tilldelningar som nämns. Du får inte sålla bort någonting.
            2. Kategorisera varje upphandling i någon av följande grupper baserat på dess innehåll:
               - 🛡️ **Försvar & Säkerhet**
               - 💻 **IT & Digitalisering / Säkerhet**
               - 🏛️ **Kommun & Region**
               - 🏗️ **Infrastruktur, Entreprenad & Övrigt**
            3. För varje träff, presentera informationen överskådligt under respektive kategori med:
               - **Organisation / Myndighet:**
               - **Titel / Upphandling:**
               - **Kort sammanfattning / Affärsmöjlighet:**
               - **Potentiell säljvinkel:**
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 📊 Kategoriserad Sammanställning")
                st.markdown(response.content[0].text)
                
            except Exception as e:
                st.error(f"Ett fel uppstod vid anropet till Claude: {e}")
