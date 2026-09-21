import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os
import json
from datetime import datetime
import io

st.set_page_config(page_title="GTM Upphandlingsbevakning - Multi-Portal", page_icon="🛡️", layout="wide")

st.title("🛡️ PA Consulting GTM-bevakning – Multi-Portal Skrapning")
st.write("Skrapar automatiskt flera sidor från både e-Avrop och Kommers Annons, och sållar fram tunga management-, program- och transformationsuppdrag.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

def scrape_eavrop():
    all_tenders = []
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    page = 1
    while page <= 25: # Säkerhetsgräns per källa
        url = "https://www.e-avrop.com/e-Upphandling/Default.aspx" if page == 1 else f"https://www.e-avrop.com/e-Upphandling/Default.aspx?page={page}"
        try:
            res = session.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, 'html.parser')
            rows_found = 0
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        cols_text = [col.text.strip() for col in cols]
                        title = cols_text[0]
                        if title and "Logga in" not in title and "Bevaka" not in title:
                            if title.isdigit() or all(c.isdigit() for c in cols_text if c):
                                continue
                            all_tenders.append({
                                "Källa": "e-Avrop",
                                "Titel": title,
                                "Publicerad": cols_text[1],
                                "Organisation": cols_text[2],
                                "Deadline": cols_text[4]
                            })
                            rows_found += 1
            if rows_found == 0:
                break
            page += 1
        except Exception:
            break
    return all_tenders

def scrape_kommers():
    all_tenders = []
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    # Exempel på publika listan i Kommers eLite
    base_url = "https://www.kommersannons.se/eLite/Notice/NoticeList.aspx"
    
    page = 1
    while page <= 15:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        try:
            res = session.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, 'html.parser')
            rows_found = 0
            
            # Letar efter tabellrader som innehåller upphandlingar i Kommers struktur
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 3:
                    text_data = [c.text.strip() for c in cols if c.text.strip()]
                    if text_data:
                        all_tenders.append({
                            "Källa": "Kommers Annons",
                            "Titel": text_data[0] if len(text_data) > 0 else "Ej angivet",
                            "Publicerad": "",
                            "Organisation": "",
                            "Deadline": text_data[-1] if len(text_data) > 1 else "Ej angivet"
                        })
                        rows_found += 1
            if rows_found == 0:
                break
            page += 1
        except Exception:
            break
    return all_tenders

if st.button("🚀 Starta automatisk multi-portal skanning", type="primary", use_container_width=True):
    with st.spinner("Skrapar e-Avrop och Kommers Annons över flera sidor..."):
        tenders_eavrop = scrape_eavrop()
        tenders_kommers = scrape_kommers()
        
        combined_data = tenders_eavrop + tenders_kommers
        df_raw = pd.DataFrame(combined_data).drop_duplicates(subset=["Titel"])
        
        if df_raw.empty:
            st.error("Kunde inte hämta data från portarna automatiskt. Kontrollera nätverksanslutningen.")
        else:
            raw_text_data = df_raw.to_json(orient="records", force_ascii=False)
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            prompt = f"""
            Du är en expert på Business Development och GTM för **PA Consulting** inom Defence & Security samt offentlig sektor i Sverige. 
            Dagens datum är {today_str}. 
            Analyserar följande råa JSON-data över nyligen publicerade upphandlingar från svenska portaler:
            
            {raw_text_data}
            
            PA CONSULTINGS KÄRNERBJUDANDE (DETTA SKA MED):
            - **Managementkonsulttjänster, strategisk rådgivning och verksamhetsutveckling.**
            - **Projektledning, programledning, portföljstyrning och transformationsledning** (särskilt stora IT-förändringar, digitalisering eller samhällskritiska system).
            - **Försvar, civilt försvar, krisberedskap, säkerhet och myndighetsstyrning** med fokus på ledning, analys, utredning eller expertstöd.
            - **IT-strategi, arkitekturstyrning och digitaliseringsledning** (ej handgriplig kodning).
            
            STRICT NEGATIVE FILTERS (RENSA BORT OMEDELBART):
            - Byggentreprenader, mark, anläggning, gatuarbeten och fysiska fastighetsåtgärder.
            - Rena personalkonsultinnehyrningar utan ledningsansvar (t.ex. vanliga systemutvecklare per timme, enskilda administratörer, städ, livsmedel, skolmaterial).
            
            Returnera resultatet ENDAST som en giltig JSON-lista. Inga markdown-backticks kring JSON-svaret (börja direkt med [ och sluta med ]). Varje objekt ska ha exakt dessa nycklar:
            - "Myndighet": (Organisation/Köpare om det finns, annars "Ej angivet")
            - "Upphandling": (Titel på upphandlingen)
            - "Deadline": (Deadline i formatet ÅÅÅÅ-MM-DD, eller "Ej angivet")
            - "Omfattning": (Om det framgår, annars "Ej angivet")
            - "Sammanfattning": (2-3 meningar om varför detta passar PA:s management- eller programledare)
            - "Saljvinkel": (Konkret rekommendation för PA-teamet)
            - "Källa": (Ange källan från datan, t.ex. "e-Avrop" eller "Kommers Annons")
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
                    st.success(f"✅ Skrapning klar! Hittade {len(parsed_data)} högpotenta management- och programledningsuppdrag.")
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
            "Källa": item.get("Källa", ""),
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Deadline": item.get("Deadline", ""),
            "Omfattning": item.get("Omfattning", "")
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
                st.markdown(f"**📌 [{item.get('Källa', '')}] {item.get('Myndighet', '')} – {item.get('Upphandling', '')}**")
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
            "Källa": item.get("Källa", ""),
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
