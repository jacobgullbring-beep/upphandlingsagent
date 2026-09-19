import streamlit as st
import pandas as pd
import anthropic
import os
import json

st.set_page_config(page_title="PA DAS Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ PA DAS Upphandlingsbevakning")
st.write("Använd snabblänkarna i sidomenyn för att hämta rådata, klistra in och generera tabellen med säljvinkeln tidigt.")

# --- SIDOMENY MED SNABBLÄNKAR ---
st.sidebar.header("🔗 Källor & Snabblänkar")
st.sidebar.markdown("- [e-Avrop](https://www.e-avrop.com/e-Upphandling/Default.aspx)")
st.sidebar.markdown("- [Kommers Annons (Notices)](https://www.kommersannons.se/Notices/TenderNotices)")
st.sidebar.markdown("- [Kommers Annons (eLite)](https://www.kommersannons.se/eLite/Notice/NoticeList.aspx)")
st.sidebar.markdown("- [Mercell (Sverige)](https://app.mercell.com/search?filter=delivery_place_code%3ASE)")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

tab_kommers_1, tab_kommers_2, tab_eavrop, tab_mercell, tab_ovrig = st.tabs([
    "Kommers Annons (Notices)", 
    "Kommers Annons (eLite)", 
    "e-Avrop", 
    "Mercell", 
    "Övrigt / FMV"
])

with tab_kommers_1:
    text_c1 = st.text_area("Klistra in från Kommers Annons (Notices):", height=150, key="c1")

with tab_kommers_2:
    text_c2 = st.text_area("Klistra in från Kommers Annons (eLite):", height=150, key="c2")

with tab_eavrop:
    text_e = st.text_area("Klistra in från e-Avrop:", height=150, key="e")

with tab_mercell:
    text_m = st.text_area("Klistra in från Mercell:", height=150, key="m")

with tab_ovrig:
    text_o = st.text_area("Klistra in från Övrig Källa / FMV:", height=150, key="o")

st.markdown("---")

if st.button("🚀 Generera filtrerad säljtabell", type="primary", use_container_width=True):
    
    combined_input = f"""
    ### [KÄLLA: Kommers Annons (Notices) - https://www.kommersannons.se/Notices/TenderNotices]
    {text_c1 if text_c1.strip() else "Ej data."}
    ### [KÄLLA: Kommers Annons (eLite) - https://www.kommersannons.se/eLite/Notice/NoticeList.aspx]
    {text_c2 if text_c2.strip() else "Ej data."}
    ### [KÄLLA: e-Avrop - https://www.e-avrop.com/e-Upphandling/Default.aspx]
    {text_e if text_e.strip() else "Ej data."}
    ### [KÄLLA: Mercell - https://app.mercell.com/search?filter=delivery_place_code%3ASE]
    {text_m if text_m.strip() else "Ej data."}
    ### [KÄLLA: Övrigt / FMV]
    {text_o if text_o.strip() else "Ej data."}
    """
    
    if not any([text_c1.strip(), text_c2.strip(), text_e.strip(), text_m.strip(), text_o.strip()]):
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        with st.spinner("Analyserar data, filtrerar bort bygg/anläggning och bygger tabell..."):
            
            prompt = f"""
            Du är en expert på Business Development / GTM för PA Consulting inom Defence & Security och management. Analysera råtexten nedan från upphandlingsportaler.
            
            VIKTIG REGLER FÖR FILtrERING:
            - TA BORT ALLA upphandlingar som rör byggnation, anläggning, renovering av fastigheter, gatuarbeten, VVS, elinstallationer i byggnader eller traditionell entreprenad.
            - Behåll ENDAST upphandlingar som rör: Försvar & Säkerhet, IT & Digitalisering, Managementkonsulttjänster, Strategi, Utbildning, Rådgivning, Systemutveckling eller analys.
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt för de relevanta upphandlingarna. Ingen inledande text, ingen markdown runt om. Varje objekt ska ha följande exakta nycklar (i denna ordning):
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD om det finns, annars "Ej angivet")
            - "Kategori": (T.ex. Försvar & Säkerhet, IT & Digitalisering, Management & Strategi)
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Säljvinkel": (Kort rekommendation för PA Consulting-teamet)
            - "Källa": (Vilken plattform det kom från, t.ex. e-Avrop, Mercell, Kommers Annons)
            - "Käll-länk": (URL till respektive plattform som angavs i källhuvudet ovan)

            Råtext att analysera:
            {combined_input}
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
                
                clean_json = raw_output.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                
                if not clean_json.endswith("]") and clean_json.startswith("["):
                    last_brace = clean_json.rfind("}")
                    if last_brace != -1:
                        clean_json = clean_json[:last_brace+1] + "\n]"
                
                data = json.loads(clean_json)
                df = pd.DataFrame(data)
                
                if not df.empty:
                    st.success(f"✅ Hittade {len(df)} relevanta upphandlingar!")
                    
                    if "Deadline" in df.columns:
                        df = df.sort_values(by="Deadline", ascending=True)
                    
                    st.markdown("### 📊 Interaktiv Sälj- och Deadline-tabell")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Hittade inga relevanta upphandlingar efter filtrering.")
                    
            except Exception as e:
                st.error(f"Kunde inte tolka datat till tabell. Här är det råa svaret:\n\n{raw_output}")
