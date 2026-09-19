import streamlit as st
import pandas as pd
import anthropic
import os
import json

st.set_page_config(page_title="GTM Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ GTM Säljbevakning – Interaktiv Tabell")
st.write("Klistra in råtexten från portaler nedan. Svaret struktureras i en filtreringsbar tabell med fokus på deadlines.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Flikar för portalerna
tab_kommers, tab_eavrop, tab_mercell, tab_fmv, tab_ovrig = st.tabs([
    "Kommers Annons", 
    "e-Avrop", 
    "Mercell", 
    "FMV / Direkt", 
    "Övrig Källa"
])

with tab_kommers:
    text_kommers = st.text_area("Kommers Annons:", height=150, key="kommers")

with tab_eavrop:
    text_eavrop = st.text_area("e-Avrop:", height=150, key="eavrop")

with tab_mercell:
    text_mercell = st.text_area("Mercell:", height=150, key="mercell")

with tab_fmv:
    text_fmv = st.text_area("FMV / Direkt:", height=150, key="fmv")

with tab_ovrig:
    text_ovrig = st.text_area("Övrig Källa:", height=150, key="ovrig")

st.markdown("---")

if st.button("🚀 Generera säljtabell med deadlines", type="primary", use_container_width=True):
    
    combined_input = f"""
    ### [KÄLLA: KOMMERS ANNONS]
    {text_kommers if text_kommers.strip() else "Ej data."}
    ### [KÄLLA: E-AVROP]
    {text_eavrop if text_eavrop.strip() else "Ej data."}
    ### [KÄLLA: MERCELL]
    {text_mercell if text_mercell.strip() else "Ej data."}
    ### [KÄLLA: FMV / DIREKT]
    {text_fmv if text_fmv.strip() else "Ej data."}
    ### [KÄLLA: ÖVRIG]
    {text_ovrig if text_ovrig.strip() else "Ej data."}
    """
    
    if not any([text_kommers.strip(), text_eavrop.strip(), text_mercell.strip(), text_fmv.strip(), text_ovrig.strip()]):
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        with st.spinner("Analyserar datum, deadlines och strukturerar tabellen..."):
            
            prompt = f"""
            Du är en expert på Business Development / GTM för konsultbolag. Analysera råtexten nedan från upphandlingsportaler.
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt. Ingen inledande text, ingen markdown-kodblock runt om om det inte behövs, men helst ren JSON eller en JSON-array. Varje objekt i listan ska ha följande exakta nycklar:
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD om det finns, annars "Ej angivet")
            - "Kategori": (T.ex. Försvar & Säkerhet, IT & Digitalisering, Vård & Omsorg, Infrastruktur, Övrigt)
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Källa": (Vilken plattform det kom från)
            - "Säljvinkel": (Kort rekommendation för GTM-teamet / hur man agerar)

            Råtext att analysera:
            {combined_input}
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
                
                # Försök städa bort eventuell markdown-formatering runt JSON om modellen la till det
                clean_json = raw_output.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                
                data = json.loads(clean_json)
                df = pd.DataFrame(data)
                
                if not df.empty:
                    st.success(f"✅ Hittade {len(df)} upphandlingar!")
                    
                    # Sortera efter deadline om kolumnen finns
                    if "Deadline" in df.columns:
                        df = df.sort_values(by="Deadline", ascending=True)
                    
                    st.markdown("### 📊 Interaktiv Sälj- och Deadline-tabell")
                    st.write("Klicka på kolumnrubrikerna för att sortera. Du kan söka i tabellen via sökikonen uppe till höger i tabellvyn.")
                    
                    # Visa interaktiv tabell
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Hittade inga strukturerade upphandlingar i texten.")
                    
            except Exception as e:
                st.error(f"Kunde inte tolka datat till tabell. Här är det råa svaret från modellen om det strulade:\n\n{raw_output}")
