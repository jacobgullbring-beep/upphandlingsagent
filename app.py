import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os
import json
from datetime import datetime
import io

st.set_page_config(page_title="GTM Upphandlingsbevakning - PA Consulting", page_icon="🛡️", layout="wide")

st.title("🛡️ PA Consulting GTM-bevakning – Program- & Transformationsledning")
st.write("Skrapar e-Avrop automatiskt och filtrerar ut affärer som matchar PA:s kärnerbjudande inom management, projektledning, programledning och IT-transformation.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

TARGET_URL = "https://www.e-avrop.com/e-Upphandling/Default.aspx"

def scrape_eavrop_all_pages():
    all_tenders = []
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def extract_rows(soup_obj):
        tenders = []
        for table in soup_obj.find_all('table'):
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 5:
                    cols_text = [col.text.strip() for col in cols]
                    title = cols_text[0]
                    
                    if title and "Logga in" not in title and "Bevaka" not in title:
                        if title.isdigit() or (len(cols_text) > 1 and all(c.isdigit() for c in cols_text if c)):
                            continue
                            
                        tenders.append({
                            "Titel": title,
                            "Publicerad": cols_text[1],
                            "Organisation": cols_text[2],
                            "Kontext": cols_text[3],
                            "Deadline": cols_text[4]
                        })
        return tenders

    page = 1
    max_pages = 40
    progress_text = st.empty()
    
    while page <= max_pages:
        progress_text.text(f"Skrapar e-Avrop sida {page}...")
        page_url = TARGET_URL if page == 1 else f"{TARGET_URL}?page={page}"
        
        try:
            res = session.get(page_url, headers=headers, timeout=10)
            if res.status_code != 200:
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = extract_rows(soup)
            if not rows:
                break
                
            all_tenders.extend(rows)
            page += 1
        except Exception as e:
            break
            
    progress_text.empty()
    df = pd.DataFrame(all_tenders).drop_duplicates()
    if not df.empty:
        df = df[~df['Titel'].astype(str).str.match(r'^\d+$')]
    return df

if st.button("🚀 Starta automatisk skanning & PA-filtrering", type="primary", use_container_width=True):
    with st.spinner("Skrapar e-Avrop och filtrerar ut management- och transformationsuppdrag med Claude 3.5 Haiku..."):
        df_raw = scrape_eavrop_all_pages()
        
        if df_raw.empty:
            st.error("Kunde inte hämta data från e-Avrop. Kontrollera nätverksanslutningen.")
        else:
            raw_text_data = df_raw.to_json(orient="records", force_ascii=False)
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            prompt = f"""
            Du är en expert på Business Development och Go-To-Market (GTM) för **PA Consulting** inom Defence & Security samt offentlig sektor i Sverige. 
            Dagens datum är {today_str}. 
            Analyserar följande råa JSON-data över nyligen publicerade upphandlingar från e-Avrop:
            
            {raw_text_data}
            
            PA CONSULTINGS KÄRNERBJUDANDE (DETTA SKA MED):
            - **Managementkonsulttjänster, strategisk rådgivning och verksamhetsutveckling.**
            - **Projektledning, programledning, portföljstyrning och transformationsledning** (särskilt inom stora IT-förändringar, digitalisering eller samhällskritiska system).
            - **Försvar, civilt försvar, krisberedskap, säkerhet och myndighetsstyrning** där det efterfrågas ledning, analys, utredning eller expertstöd.
            - **IT-strategi, arkitekturstyrning och digitaliseringsledning** (ej handgriplig kodning/utveckling, utan styrning och ledarskap).
            
            STRICT NEGATIVE FILTERS (RENSA BORT OMEDELBART):
            - Byggentreprenader, mark, anläggning, gatuarbeten och fysiska fastighetsåtgärder.
            - Rena personalkonsultinnehyrningar utan ledningsansvar (t.ex. vanliga systemutvecklare per timme, enskilda administratörer, lokalvård, städ, livsmedel, skolmaterial).
            - Rena ramavtal för mjukvarulicenser eller hårdvara utan konsultstöd.
            
            Returnera resultatet ENDAST som en giltig JSON-lista. Inga markdown-backticks kring JSON-svaret (börja direkt med [ och sluta med ]). Varje objekt ska ha exakt dessa nycklar:
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Deadline": (Deadline i formatet ÅÅÅÅ-MM-DD, eller "Ej angivet")
            - "Omfattning": (Om det framgår, annars "Ej angivet")
            - "Sammanfattning": (2-3 meningar om varför detta är ett klockrent uppdrag för PA:s management- eller programledare)
            - "Saljvinkel": (Konkret rekommendation för PA-teamet kring hur vi positionerar oss i anbudet)
            - "Källa": "e-Avrop"
            """
            
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=6000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
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
                    parsed_data = json.loads(clean_json)
                    st.session_state['parsed_tenders'] = parsed_data
                    st.success(f"✅ Filtrering klar! Hittade {len(parsed_data)} högpotenta management- och programledningsuppdrag.")
                else:
                    st.warning("AI-analysen gav inga formaterade resultat.")
                    
            except Exception as e:
                st.error(f"Ett fel uppstod vid AI-bearbetningen: {e}")

if 'parsed_tenders' in st.session_state and st.session_state['parsed_tenders']:
    st.markdown("---")
    st.subheader("📊 Granska uppdrag & Sätt Go / No-go")
    
    selected_indices = []
    go_no_go_status = {}
    
    table_data = []
    for item in st.session_state['parsed_tenders']:
        table_data.append({
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Deadline": item.get("Deadline", ""),
            "Omfattning": item.get("Omfattning", ""),
            "Källa": item.get("Källa", "")
        })
    
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    
    st.markdown("### 🗂️ Detaljerad granskning & Exportval")
    
    for idx, item in enumerate(st.session_state['parsed_tenders']):
        with st.container():
            col1, col2, col3 = st.columns([0.05, 0.55, 0.40])
            with col1:
                is_selected = st.checkbox("Välj", key=f"chk_{idx}", label_visibility="collapsed")
                if is_selected:
                    selected_indices.append(idx)
            with col2:
                st.markdown(f"**📌 {item.get('Myndighet', '')} – {item.get('Upphandling', '')}**")
                st.markdown(f"*Deadline:* `{item.get('Deadline', '')}` | *Omfattning:* `{item.get('Omfattning', '')}`")
                st.markdown(f"*Sammanfattning:* {item.get('Sammanfattning', '')}")
                st.markdown(f"*Säljvinkel:* {item.get('Saljvinkel', '')}")
            with col3:
                decision = st.selectbox(
                    "Go / No-go beslut", 
                    ["Ej satt", "Go", "No-go"], 
                    key=f"decision_{idx}"
                )
                go_no_go_status[idx] = decision
            st.divider()

    rows_for_excel = []
    for idx in selected_indices:
        item = st.session_state['parsed_tenders'][idx]
        rows_for_excel.append({
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Sammanfattning": item.get("Sammanfattning", ""),
            "Säljvinkel": item.get("Saljvinkel", ""),
            "Go/No-go": go_no_go_status.get(idx, "Ej satt"),
            "Ansvarig konsult": "",
            "Deadline": item.get("Deadline", ""),
            "Omfattning": item.get("Omfattning", ""),
            "Status": "Arbete pågår"
        })
    
    if rows_for_excel:
        df_master = pd.DataFrame(rows_for_excel)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_master.to_excel(writer, index=False, sheet_name='Utvalda Uppdrag')
        excel_data = output.getvalue()
        
        st.download_button(
            label=f"📥 Ladda ner Master-Excel ({len(rows_for_excel)} markerade uppdrag)",
            data=excel_data,
            file_name=f"PA_Consulting_Upphandlingar_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("💡 Bocka i minst ett uppdrag ovan för att aktivera nerladdning till Excel.")
