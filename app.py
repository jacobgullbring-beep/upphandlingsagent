import streamlit as st
import pandas as pd
import anthropic
import os
import json

st.set_page_config(page_title="DAS Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ DAS Upphandlingsbevakning)
st.write("Extraherar och visar enbart rena konsult-, rådgivnings- och digitaliseringsaffärer.")

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
    "Övrigt"
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
    text_o = st.text_area("Klistra in från Övrig Källa:", height=150, key="o")

st.markdown("---")

if st.button("🚀 Extrahera och rensa bort allt ointressant", type="primary", use_container_width=True):
    
    combined_parts = []
    if text_c1.strip(): combined_parts.append(f"--- KOMMERS NOTICES ---\n{text_c1}")
    if text_c2.strip(): combined_parts.append(f"--- KOMMERS ELITE ---\n{text_c2}")
    if text_e.strip(): combined_parts.append(f"--- E-AVROP ---\n{text_e}")
    if text_m.strip(): combined_parts.append(f"--- MERCELL ---\n{text_m}")
    if text_o.strip(): combined_parts.append(f"--- ÖVRIGT ---\n{text_o}")
    
    combined_input = "\n\n".join(combined_parts)
    
    if not combined_input.strip():
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        all_parsed_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Filtrerar bort allt skräp och tar bort icke-relevanta uppdrag...")
        progress_bar.progress(50)
        
        prompt = f"""
        Du är en affärsutvecklare för ett management- och konsultbolag. 
        Läs igenom texten nedan och utför följande strikta filtrering:
        
        1. TA BORT HELT: Allt som rör byggentreprenader, fastighetsskötsel, fysiska varor, larm, utrustning, livsmedel, isrinkar/idrottsanläggningar, städ eller andra fysiska entreprenader. Dessa ska INTE finnas med i listan överhuvudtaget.
        2. BEHÅLL ENDAST: Klara uppdrag inom konsulttjänster, rådgivning, IT, systemutveckling, projektledning, programledarskap, förändringsledning, säkerhetsanalys eller strategiskt stöd.
        
        Svara ENDAST med en giltig JSON-lista utan markdown-backticks (ska börja med [ och sluta med ]). Om inga relevanta uppdrag hittas, returnera en helt tom lista ([]).
        Varje objekt i listan måste ha exakt dessa nycklar:
        - "Deadline": Datum (eller "Ej angivet")
        - "Myndighet": Köpare / organisation
        - "Upphandling": Titel på upphandlingen
        - "Relevans/Affärsmöjlighet": Varför detta är intressant för konsultbolaget.

        Text att analysera:
        {combined_input}
        """
        
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
            
            if raw_output.strip():
                clean_json = raw_output.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1]
                if "```" in clean_json:
                    clean_json = clean_json.split("```")[0]
                clean_json = clean_json.strip()
                
                start_idx = clean_json.find("[")
                end_idx = clean_json.rfind("]")
                
                if start_idx != -1 and end_idx != -1:
                    clean_json = clean_json[start_idx:end_idx+1]
                    all_parsed_data = json.loads(clean_json)
        except Exception as e:
            st.error(f"Ett fel uppstod vid tolkningen: {e}")
        
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()
        
        if all_parsed_data and isinstance(all_parsed_data, list):
            st.success(f"✅ Rensningen klar! Visar {len(all_parsed_data)} relevanta uppdrag.")
            df_results = pd.DataFrame(all_parsed_data)
            st.dataframe(df_results, use_container_width=True, hide_index=True)
        else:
            st.warning("Inga uppdrag klarade filtret. Allt icke-relevant har rensats bort.")
