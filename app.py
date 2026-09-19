import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime

st.set_page_config(page_title="GTM Upphandlingsbevakning", page_icon="🏛️", layout="wide")

st.title("🏛️ GTM Säljbevakning & Sammanfattningar")
st.write("Samlar in alla upphandlingar och presenterar dem med en tydlig sammanfattning och säljvinkel.")

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

if st.button("🚀 Analysera & Sammanfatta alla uppdrag", type="primary", use_container_width=True):
    
    combined_input = f"""
    ### [KÄLLA: Kommers Annons (Notices)]
    {text_c1 if text_c1.strip() else "Ej data."}
    ### [KÄLLA: Kommers Annons (eLite)]
    {text_c2 if text_c2.strip() else "Ej data."}
    ### [KÄLLA: e-Avrop]
    {text_e if text_e.strip() else "Ej data."}
    ### [KÄLLA: Mercell]
    {text_m if text_m.strip() else "Ej data."}
    ### [KÄLLA: Övrigt]
    {text_o if text_o.strip() else "Ej data."}
    """
    
    if not any([text_c1.strip(), text_c2.strip(), text_e.strip(), text_m.strip(), text_o.strip()]):
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        chunk_size = 12000
        text_chunks = [combined_input[i:i+chunk_size] for i in range(0, len(combined_input), chunk_size)]
        
        all_parsed_data = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, chunk in enumerate(text_chunks):
            status_text.text(f"Bearbetar del {idx+1} av {len(text_chunks)}...")
            progress_bar.progress((idx + 1) / len(text_chunks))
            
            prompt = f"""
            Du är en expert på Business Development / GTM för konsultbolag inom offentlig sektor. 
            Dagens datum är {today_str}. 
            Analysera råtexten nedan (del {idx+1} av {len(text_chunks)}). 
            
            Extrahera ALLA upphandlingar eller tilldelningsmeddelanden som finns i texten utan att begränsa antalet.
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt. Inga markdown-backticks kring JSON-svaret (returnera rå JSON som börjar med [ och slutar med ]). Varje objekt ska ha exakt dessa nycklar:
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD, eller "Ej angivet")
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen eller tilldelningen)
            - "Sammanfattning": (En kort, kärnfull sammanfattning på 1-2 meningar om vad uppdraget avser)
            - "Saljvinkel": (Kort säljrekommendation / vinkel för konsultteamet)

            Råtext att analysera:
            {chunk}
            """
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-5",
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
                        chunk_data = json.loads(clean_json)
                        if isinstance(chunk_data, list):
                            all_parsed_data.extend(chunk_data)
            except Exception as e:
                continue
        
        status_text.empty()
        progress_bar.empty()
        
        if all_parsed_data:
            st.success(f"✅ Hittade totalt {len(all_parsed_data)} uppdrag!")
            
            # Konvertera till DataFrame för snygg tabellvisning med sammanfattningskolumn efter Myndighet
            df_results = pd.DataFrame(all_parsed_data)
            
            # Säkerställ att kolumnerna ligger i rätt ordning om de finns
            desired_columns = ["Deadline", "Myndighet", "Sammanfattning", "Upphandling", "Saljvinkel"]
            existing_cols = [col for col in desired_columns if col in df_results.columns]
            df_results = df_results[existing_cols]
            
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            # Alternativt en detaljerad vy nedanför om man vill läsa mer
            st.markdown("### 📌 Detaljerad vy per uppdrag")
            for item in all_parsed_data:
                with st.expander(f"{item.get('Myndighet', 'Okänd')} – {item.get('Upphandling', 'Ingen titel')}"):
                    st.write(f"**Deadline:** {item.get('Deadline', 'Ej angivet')}")
                    st.write(f"**Sammanfattning:** {item.get('Sammanfattning', 'Ingen sammanfattning')}")
                    st.write(f"**GTM-vinkel:** {item.get('Saljvinkel', 'Ingen vinkel angiven')}")
        else:
            st.warning("Kunde inte hitta några uppdrag att extrahera från den inlistade texten.")
