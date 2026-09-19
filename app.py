import streamlit as st
import pandas as pd
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ GTM Säljbevakning – Multi-portal")
st.write("Klistra in råtexten från respektive upphandlingsportal i sina respektive rutor nedanför. Klicka sedan på knappen för att få en samlad, kategoriserad överblick!")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Skapa flikar för portalerna
tab_kommers, tab_eavrop, tab_mercell, tab_fmv, tab_ovrig = st.tabs([
    "Kommers Annons", 
    "e-Avrop", 
    "Mercell", 
    "FMV / Direkt", 
    "Övrig Källa"
])

with tab_kommers:
    st.subheader("Kommers Annons")
    text_kommers = st.text_area("Klistra in urklipp från Kommers Annons:", height=200, key="kommers")

with tab_eavrop:
    st.subheader("e-Avrop")
    text_eavrop = st.text_area("Klistra in urklipp från e-Avrop:", height=200, key="eavrop")

with tab_mercell:
    st.subheader("Mercell")
    text_mercell = st.text_area("Klistra in urklipp från Mercell:", height=200, key="mercell")

with tab_fmv:
    st.subheader("FMV / Direkt")
    text_fmv = st.text_area("Klistra in urklipp från FMV eller annan sajt:", height=200, key="fmv")

with tab_ovrig:
    st.subheader("Övrig Källa")
    text_ovrig = st.text_area("Klistra in ev. extra urklipp här:", height=200, key="ovrig")

st.markdown("---")

if st.button("🚀 Analysera och kategorisera alla källor", type="primary", use_container_width=True):
    # Samla ihop allt som har fyllts i
    combined_input = f"""
    ### [KÄLLA: KOMMERS ANNONS]
    {text_kommers if text_kommers.strip() else "Ingen data inmatad."}

    ### [KÄLLA: E-AVROP]
    {text_eavrop if text_eavrop.strip() else "Ingen data inmatad."}

    ### [KÄLLA: MERCELL]
    {text_mercell if text_mercell.strip() else "Ingen data inmatad."}

    ### [KÄLLA: FMV / DIREKT]
    {text_fmv if text_fmv.strip() else "Ingen data inmatad."}

    ### [KÄLLA: ÖVRIG]
    {text_ovrig if text_ovrig.strip() else "Ingen data inmatad."}
    """
    
    if not any([text_kommers.strip(), text_eavrop.strip(), text_mercell.strip(), text_fmv.strip(), text_ovrig.strip()]):
        st.warning("Du behöver klistra in text i minst en av textrutorna först!")
    else:
        with st.spinner("Claude sammanställer, rensar bort skräp och kategoriserar samtliga upphandlingar..."):
            prompt = f"""
            Du är en expert på Business Development / Go-To-Market (GTM) för konsultbolag inom offentlig sektor.
            
            Här är råtext kopierad från olika upphandlingsportaler:
            ---
            {combined_input}
            ---
            
            Uppgift:
            1. Gå igenom samtliga källor ovan och fånga upp **alla** separata upphandlingar, avtal eller tilldelningar. Du får absolut inte sålla bort någonting.
            2. Kategorisera varje upphandling i någon av följande huvudgrupper:
               - 🛡️ **Försvar, Säkerhet & Beredskap**
               - 💻 **IT, Digitalisering & Analysverktyg**
               - 🏥 **Vård, Omsorg & Livsmedel**
               - 🏗️ **Infrastruktur, Miljö, Fastighet & Entreprenad**
               - 🏛️ **Övrigt / Allmän förvaltning**
            3. För varje träff, ange vilken källa den kom från (t.ex. Kommers Annons, e-Avrop eller Mercell) och presentera den snyggt med:
               - **Organisation / Myndighet:**
               - **Titel / Upphandling:**
               - **Källa:** 
               - **Kort sammanfattning / Affärsmöjlighet:**
               - **Potentiell säljvinkel:**
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                answer_text = "".join([block.text for block in response.content if hasattr(block, "text")])
                
                st.markdown("### 📊 Samlad Kategoriserad Överblick")
                st.markdown(answer_text)
                
            except Exception as e:
                st.error(f"Ett fel uppstod vid anropet till Claude: {e}")
