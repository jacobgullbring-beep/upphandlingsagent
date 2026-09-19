import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime

st.set_page_config(page_title="GTM Upphandlingsbevakning", page_icon="🏛️", layout="wide")

st.title("🏛️ GTM Säljbevakning – Kommuner & Regioner")
st.write("Klistra in all din råtext på en gång. Appen delar upp stora mängder automatiskt, rensar bort bygg och skapar en gemensam tabell.")

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

if st.button("🚀 Generera tabell för Kommun & Region (Alla sidor)", type="primary", use_container_width=True):
    
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
        # Dela upp texten i bitar om ca 12 000 tecken för att undvika att krascha AI:n
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
            Du är en expert på Business Development / GTM med fokus på den offentliga sektorn (kommuner och regioner) för konsultbolag. 
            Dagens datum är {today_str}. 
            Analysera råtexten nedan (detta är del {idx+1} av {len(text_chunks)}).
            
            VIKTIGA REGLER FÖR FILTRERING:
            1. **Prioritera Kommuner & Regioner:** Behåll i första hand upphandlingar där köparen är en kommun, kommunalt bolag, region eller kommunalförbund.
            2. **Rensa bort bygg & anläggning:** TA BORT ALLA upphandlingar som rör byggnation, entreprenad, gatuarbeten, renoveringar, fastighetsskötsel, VVS eller elinstallationer i byggnader.
            3. **Inriktning för konsulttjänster:** Fokusera på ramavtal och upphandlingar som rör managementkonsulttjänster, organisationsutveckling, digitaliseringsstöd, HR-stöd, utredningar, analys, utbildning eller allmänna konsulttjänster riktade till kommun/region.
            
            REGLER FÖR DEADLINE:
            - Leta efter texter som "Deadline", "X days left", "Tomorrow", eller rena datum (t.ex. ÅÅÅÅ-MM-DD eller DD/MM).
            - Om det står "X days left" eller "Tomorrow", räkna ut det faktiska datumet baserat på att dagsdatum är {today_str} och skriv om det till formatet ÅÅÅÅ-MM-DD.
            - Om det helt saknas datum/deadline, sätt "Ej angivet".
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt för de relevanta upphandlingarna i denna textdel. Ingen inledande text, ingen markdown runt om. Varje objekt ska ha följande exakta nycklar:
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD, eller "Ej angivet")
            - "Kategori": (T.ex. Management & Strategi, Digitalisering, HR & Utveckling, Analys & Utredning)
            - "Myndighet": (Organisation/Kommun/Region)
            - "Upphandling": (Titel på upphandlingen)
            - "Säljvinkel": (Kort säljrekommendation anpassad för kommun-/regionförsäljning)
            - "Källa": (Vilken plattform det kom från)
            - "Käll-länk": (URL till respektive plattform)

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
        
        df = pd.DataFrame(all_parsed_data)
        
        if not df.empty:
            # Ta bort eventuella dubbletter om samma upphandling kom med i skarven
            df = df.drop_duplicates(subset=["Myndighet", "Upphandling"])
            
            if "Deadline" in df.columns:
                df = df.sort_values(by="Deadline", ascending=True)
                
            st.success(f"✅ Klart! Hittade totalt {len(df)} unika relevanta kommun- och regionupphandlingar från alla dina sidor.")
            st.markdown("### 📊 Interaktiv Sälj- och Deadline-tabell")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Hittade inga relevanta upphandlingar efter filtrering av den inskickade texten.")
