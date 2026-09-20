import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="DAS Upphandlingsbevakning", page_icon="🏛️", layout="wide")

st.title("🏛️ DAS Upphandlingsbevakning – Kommuner & Regioner")
st.write("Klistra in råtext från portalerna. Appen filtrerar bort bygg, mark och anläggning, skapar länkar och låter dig exportera dina valda favoriter till Excel.")

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

if st.button("🚀 Generera skärpt tabell", type="primary", use_container_width=True):
    
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
        with st.spinner("Analyserar och filtrerar bort bygg/mark, samt skapar direktlänkar..."):
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            prompt = f"""
            Du är en expert på Business Development / GTM för konsultbolag inom den offentliga sektorn (kommuner och regioner). 
            Dagens datum är {today_str}. 
            Analysera råtexten nedan.
            
            STRICT NEGATIVE FILTERS (TA BORT OMEDELBART):
            - Inga byggnationer, entreprenader, gatuarbeten, renoveringar eller fastighetsskötsel.
            - Inga geotekniska undersökningar, markundersökningar, miljötekniska markprover, bergteknik eller dagvattenutredningar kopplade till mark/anläggning.
            - Inga fysiska materialinköp, livsmedel, städmaterial eller VVS/el-installationer.
            
            POSITIVA KRITERIER (FOKUSERA PÅ):
            - Managementkonsulttjänster, organisationsutveckling, digitaliseringsstöd, IT-arkitektur, HR-stöd, strategiska utredningar, analys, utbildning eller allmänna konsulttjänster riktade till kommun/region.
            
            REGLER FÖR LÄNKAR ("Käll-länk"):
            - Om det finns en URL i texten för upphandlingen, använd den.
            - Om ingen direkt URL finns, skapa en smart Google-söklänk baserat på myndigheten och upphandlingens titel på formatet: `https://www.google.com/search?q=MYNDIGHET+UPPHANDLING`
            
            REGLER FÖR DEADLINE:
            - Leta efter datum. Om inget datum finns, sätt "Ej angivet".
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt. Ingen inledande text, ingen markdown runt om. Varje objekt ska ha följande nycklar:
            - "Deadline": (ÅÅÅÅ-MM-DD eller "Ej angivet")
            - "Kategori": (T.ex. Management & Strategi, Digitalisering, HR & Utveckling, Analys & Utredning)
            - "Myndighet": (Organisation/Kommun/Region)
            - "Upphandling": (Titel)
            - "Säljvinkel": (Kort säljrekommendation)
            - "Källa": (Plattform)
            - "Käll-länk": (URL)

            Råtext att analysera:
            {combined_input}
            """
            
            raw_output = ""
            
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Säkert sätt att plocka ut texten från Anthropic-svaret
                raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
                
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
                
                data = json.loads(clean_json)
                df = pd.DataFrame(data)
                
                if not df.empty:
                    st.session_state["df_results"] = df
                    st.success(f"✅ Hittade {len(df)} relevanta uppdrag!")
                else:
                    st.warning("Hittade inga relevanta upphandlingar efter det skärpta filtret.")
                    st.session_state["df_results"] = pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Kunde inte tolka datat. Felmeddelande: {e}\n\nRått svar:\n\n{raw_output}")

# --- VISA RESULTAT OCH HANTERA KRYSSRUTOR / EXPORT OM DATA FINNS ---
if "df_results" in st.session_state and not st.session_state["df_results"].empty:
    df = st.session_state["df_results"]
    
    if "Deadline" in df.columns:
        df = df.sort_values(by="Deadline", ascending=True)
    
    st.markdown("### 📊 Raffinerad Sälj- och Deadline-tabell")
    st.write("Kryssa för de uppdrag du vill ta med dig till mötet och ladda ner som Excel:")
    
    # Lägg till kolumn för markering (kryssrutor)
    df_editable = df.copy()
    df_editable.insert(0, "Välj", True)
    
    # Visa interaktiv tabell med kryssrutor
    edited_df = st.data_editor(df_editable, use_container_width=True, hide_index=True)
    
    # Filtrera ut de rader som är ikryssade
    selected_rows = edited_df[edited_df["Välj"] == True].drop(columns=["Välj"])
    
    if not selected_rows.empty:
        file_name = f"Utvalda_Upphandlingar_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            selected_rows.to_excel(writer, index=False, sheet_name='Utvalda Uppdrag')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Ladda ner markerade uppdrag till Excel (.xlsx)",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("Inga rader är markerade. Kryssa för minst ett uppdrag ovan för att aktivera nerladdningen.")
