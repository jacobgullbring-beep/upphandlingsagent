import streamlit as st
import pandas as pd
import anthropic
import os
import json

st.set_page_config(page_title="PA Consulting DAS Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ PA Consulting DAS Säljbevakning – Stabil Tabellgenerering")
st.write("Använd snabblänkarna i sidomenyn för att hämta rådata, klistra in och generera tabellen.")

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

if st.button("🚀 Generera säljtabell med deadlines", type="primary", use_container_width=True):
    
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
        with st.spinner("Analyserar data och bygger tabell..."):
            
            prompt = f"""
            Du är en expert på Business Development / GTM för konsultbolag. Analysera råtexten nedan från upphandlingsportaler. Varje källrubrik innehåller en URL.
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt. Ingen inledande text, ingen markdown runt om. Varje objekt ska ha följande exakta nycklar:
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD om det finns, annars "Ej angivet")
            - "Kategori": (T.ex. Försvar & Säkerhet, IT & Digitalisering, Vård & Omsorg, Infrastruktur, Övrigt)
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Källa": (Vilken plattform det kom från, t.ex. e-Avrop, Mercell, Kommers Annons)
            - "Käll-länk": (URL till respektive plattform som angavs i källhuvudet ovan)
            - "Säljvinkel": (Kort rekommendation för GTM-teamet)

            Råtext att analysera:
            {combined_input}
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=8000, # Ökat till 8000 för att rymma mer text utan att klipper
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
                
                # Säkerhetsåtgärd om JSON-strängen kapas i slutet
                if not clean_json.endswith("]") and clean_json.startswith("["):
                    # Hitta sista kompletta objektet genom att leta efter sista avslutande klammern
                    last_brace = clean_json.rfind("}")
                    if last_brace != -1:
                        clean_json = clean_json[:last_brace+1] + "\n]"
                
                data = json.loads(clean_json)
                df = pd.DataFrame(data)
                
                if not df.empty:
                    st.success(f"✅ Hittade {len(df)} upphandlingar!")
                    
                    if "Deadline" in df.columns:
                        df = df.sort_values(by="Deadline", ascending=True)
                    
                    st.markdown("### 📊 Interaktiv Sälj- och Deadline-tabell")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Hittade inga strukturerade upphandlingar i texten.")
                    
            except Exception as e:
                st.error(f"Kunde inte tolka datat till tabell. Här är det råa svaret:\n\n{raw_output}")
