import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime

st.set_page_config(page_title="DAS Upphandlingsbevakning", page_icon="⚡", layout="wide")

st.title("⚡ DAS Säljbevakning")
st.write("Extraherar upphandlingar snabbt och kostnadseffektivt.")

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

if st.button("🚀 Extrahera med Haiku 4.5", type="primary", use_container_width=True):
    
    combined_input = f"""
    {text_c1}
    {text_c2}
    {text_e}
    {text_m}
    {text_o}
    """
    
    if not combined_input.strip():
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        chunk_size = 18000
        text_chunks = [combined_input[i:i+chunk_size] for i in range(0, len(combined_input), chunk_size)]
        
        all_parsed_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, chunk in enumerate(text_chunks):
            status_text.text(f"Bearbetar del {idx+1} av {len(text_chunks)}...")
            progress_bar.progress((idx + 1) / len(text_chunks))
            
            prompt = f"""
            Extrahera alla upphandlingar från texten nedan. Svara ENDAST med en giltig JSON-lista utan markdown-backticks.
            Varje objekt i listan måste ha exakt dessa nycklar:
            - "Deadline": Datum (eller "Ej angivet")
            - "Myndighet": Köpare
            - "Upphandling": Titel
            - "Sammanfattning": Kort mening om vad det gäller.

            Text:
            {chunk}
            """
            
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1500,
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
                        chunk_data = json.loads(clean_json)
                        if isinstance(chunk_data, list):
                            all_parsed_data.extend(chunk_data)
            except Exception as e:
                continue
        
        status_text.empty()
        progress_bar.empty()
        
        if all_parsed_data:
            st.success(f"✅ Hittade {len(all_parsed_data)} uppdrag!")
            df_results = pd.DataFrame(all_parsed_data)
            st.dataframe(df_results, use_container_width=True, hide_index=True)
        else:
            st.warning("Kunde inte hitta några uppdrag att extrahera.")
