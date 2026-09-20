import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime
import io

st.set_page_config(page_title="DAS Upphandlingsbevakning - Defence & Security", page_icon="🛡️", layout="wide")

# --- ANPASSAD CSS FÖR SMALARE SIDEBAR ---
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 220px;
            max-width: 260px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ GTM Säljbevakning – Defence & Security")
st.write("Filtret är ställt på Försvar, Säkerhet, Totalförsvar och Civilt försvar (inkl. relevanta kommun/region-uppdrag).")

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
    text_e = st.text_area("Klistra in från e-Avrop:", height=150, key="c2_e")

with tab_mercell:
    text_m = st.text_area("Klistra in från Mercell:", height=150, key="m")

with tab_ovrig:
    text_o = st.text_area("Klistra in från Övrig Källa:", height=150, key="o")

st.markdown("---")

if st.button("🚀 Analysera & Filtrera (Inkl. Civilt Försvar & Kommuner)", type="primary", use_container_width=True):
    
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
            Du är en expert på Business Development och GTM inom Defence & Security (försvar, säkerhet, totalförsvar, civilt försvar och krisberedskap) för ett ledande konsultbolag. 
            Dagens datum är {today_str}. 
            Analysera råtexten nedan (del {idx+1} av {len(text_chunks)}).
            
            REGLER FÖR FILTRERING:
            1. **INKLUDERA:** 
               - Upphandlingar från försvarssektorn (FMV, Försvarsmakten, MSB, Säpo etc.).
               - Upphandlingar från **kommuner och regioner** som har en direkt koppling till **civilt försvar, totalförsvar, krisberedskap, säkerhetsskydd, informationssäkerhet, robusthet eller skyddsobjekt**.
            2. **RENSA BORT:** Allmänna, rent civila kommunala upphandlingar som inte berör säkerhet eller beredskap (t.ex. standard HR-stöd för vanliga förvaltningar, skolutbildning, socialtjänst, vanliga IT-system för administration eller lokal fastighetsskötsel/bygg).
            
            Returnera resultatet ENDAST som en giltig JSON-lista med relevanta objekt. Inga markdown-backticks kring JSON-svaret (returnera rå JSON som börjar med [ och slutar med ]). Varje objekt ska ha exakt dessa nycklar:
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Deadline": (Sista svarsdag om det framgår, annars "Ej angivet")
            - "Omfattning": (Uppskattad omfattning i timmar eller belopp om det nämns, annars "Ej angivet")
            - "Sammanfattning": (En fyllig sammanfattning på 2-3 meningar om vad upphandlingen avser med fokus på säkerhet/försvar/beredskap)
            - "Saljvinkel": (Konkret rekommendation på hur PA Consulting inom Defence & Security bör positionera sig)
            - "Källa": (Vilken plattform det kom från)

            Råtext att analysera:
            {chunk}
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
                        chunk_data = json.loads(clean_json)
                        if isinstance(chunk_data, list):
                            all_parsed_data.extend(chunk_data)
            except Exception as e:
                continue
        
        status_text.empty()
        progress_bar.empty()
        
        if all_parsed_data:
            st.success(f"✅ Hittade {len(all_parsed_data)} relevanta uppdrag inom Defence, Säkerhet & Civilt försvar!")
            
            rows_for_excel = []
            rows_for_ui = []
            
            for item in all_parsed_data:
                rows_for_excel.append({
                    "Myndighet": item.get("Myndighet", ""),
                    "Upphandling": item.get("Upphandling", ""),
                    "Sammanfattning": item.get("Sammanfattning", ""),
                    "Säljvinkel": item.get("Saljvinkel", ""),
                    "Go/No-go": "",
                    "Ansvarig konsult för anbudet": "",
                    "Medverkande konsulter": "",
                    "Deadline": item.get("Deadline", ""),
                    "Deadline internt": "",
                    "Deadline inlämning": "",
                    "Omfattning (i timmar/pengar)": item.get("Omfattning", ""),
                    "Status (Arbete pågår, inlämnad, avbruten)": "Arbete pågår",
                    "Utfall": "",
                    "Källa": item.get("Källa", "")
                })
                
                rows_for_ui.append({
                    "Myndighet": item.get("Myndighet", ""),
                    "Upphandling": item.get("Upphandling", ""),
                    "Deadline": item.get("Deadline", ""),
                    "Omfattning": item.get("Omfattning", ""),
                    "Källa": item.get("Källa", "")
                })
            
            df_ui = pd.DataFrame(rows_for_ui)
            df_master = pd.DataFrame(rows_for_excel)
            
            st.subheader("📊 Filtrerad Översikt (Defence, Säkerhet & Civilt Försvar)")
            st.dataframe(df_ui, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            with st.expander("🔍 Visa detaljerade sammanfattningar & säljvinklar per uppdrag"):
                for item in all_parsed_data:
                    st.markdown(f"**📌 {item.get('Myndighet', '')} – {item.get('Upphandling', '')}**")
                    st.markdown(f"*Sammanfattning:* {item.get('Sammanfattning', '')}")
                    st.markdown(f"*Säljvinkel:* {item.get('Saljvinkel', '')}")
                    st.divider()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_master.to_excel(writer, index=False, sheet_name='Upphandlingar')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Ladda ner Master-Excel",
                data=excel_data,
                file_name=f"GTM_Defence_CiviltForsvar_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("Hittade inga upphandlingar som matchade kriterierna i den inklistrade texten.")
