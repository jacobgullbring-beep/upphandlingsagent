import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime
import io
import zipfile
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="GTM Upphandlingsbevakning - Defence & Security", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 260px;
            max-width: 320px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ GTM Säljbevakning – Defence & Security")
st.write("Molnbaserad bevakning och AI-analys för svenska försvars- och säkerhetsmarknaden.")

# --- SIDOMENY MED ALLA DIREKTLÄNKAR & AGGREGATORER ---
st.sidebar.header("🔗 Direktlänkar & Aggregatorer")
st.sidebar.markdown("- [Hitta Upphandlingar (Försvar)](https://www.hittaupphandlingar.se/forsvar)")
st.sidebar.markdown("- [Vunnet.se (Vunna affärer)](https://vunnet.se/upphandlingar?typ=alla)")

# Lista med alla länkar som ska skannas automatiskt under flik 2
all_sidebar_links = [
    {"name": "Hitta Upphandlingar (Försvar)", "url": "https://www.hittaupphandlingar.se/forsvar"},
    {"name": "Göteborgs Stad", "url": "https://app.mercell.com/org/goteborgs_stads_upphandlingar"},
    {"name": "Malmö Stad", "url": "https://app.mercell.com/org/kommersannons.se/malmo/Notice/NoticeList.aspx"},
    {"name": "Uppsala Kommun", "url": "https://app.mercell.com/org/uppsala_kommun/"},
    {"name": "Linköping", "url": "https://www.e-avrop.com/linkoping//e-Upphandling/Default.aspx"},
    {"name": "Västerås", "url": "https://www.vasteras.ses/naringsliv-och-arbete/upphandling-och-inkop/pagaende-upphandlingar.html"},
    {"name": "Örebro Kommun", "url": "https://app.mercell.com/org/orebro_kommuns_upphandlingar"},
    {"name": "Helsingborg", "url": "https://foretagare.helsingborg.se/upphandling/annonserade-upphandlingar-direktupphandlingar-och-planerade-upphandlingar/"},
    {"name": "Jönköpings Kommun", "url": "https://app.mercell.com/org/jonkopings_kommun"},
    {"name": "Norrköping", "url": "https://www.e-avrop.com/norrk/e-Upphandling/Default.aspx"},
    {"name": "Umeå Kommun", "url": "https://www.umea.se/jobbochforetagande/upphandlingochinkop/upphandlingar.4.1c16b00a1742340e02eeac.html"},
    {"name": "Lunds Kommun", "url": "https://app.mercell.com/org/lunds_kommuns_upphandlingar"},
    {"name": "Järfälla Kommun", "url": "https://se.openprocurements.com/buyer/jarfalla-kommun/"},
    {"name": "Tendsign", "url": "https://tendsign.com/public/list_public_procurements.aspx?IndividualID=xUDxnN2SZS/xCpdaCME2fwA="},
    {"name": "Bidmonkey", "url": "https://app.bidmonkey.se/webview?u=ea2e8da8c15d516fa894"},
    {"name": "Mercell (Sverige Sök)", "url": "https://app.mercell.com/search?filter=delivery_place_code%3ASE"}
]

with st.sidebar.expander("Stora städer & Kommuner"):
    for link in all_sidebar_links[1:13]:
        st.markdown(f"- [{link['name']}]({link['url']})")

with st.sidebar.expander("Övriga portaler & system"):
    for link in all_sidebar_links[13:]:
        st.markdown(f"- [{link['name']}]({link['url']})")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# --- HUVUDGRÄNSSNITT MED FLIKAR ---
tab_files, tab_scan = st.tabs(["📂 Filer & ZIP-arkiv", "🌐 Scanna igenom upphandlingar"])

# --- DELAD AI-PROMPT-LOGIK FÖR MANAGEMENT & FÖRSVAR ---
def build_strict_prompt(target_source_name, text_content, today_str):
    return f"""
    Du är en expert på Business Development och GTM inom Management Consulting med inriktning mot Defence & Security på den svenska marknaden (försvar, säkerhet, totalförsvar, civilt försvar, krisberedskap och robusthet) för ett ledande konsultbolag. 
    Dagens datum är {today_str}. 
    Analyserar texten från '{target_source_name}' mycket noggrant.
    
    🔍 **SKARPA REGLER FÖR INKLUDERING (ENBART MANAGEMENT CONSULTING):**
    1. **INKLUDERA ENDAST:** 
       - Uppdrag som rör **Management Consulting, programledning, projektledning, strategisk rådgivning, organisationsutveckling, förändringsledning, risk- och sårbarhetsanalys, säkerhetsskyddsanalys eller informationssäkerhetsstyrning**.
       - Köparen måste vara inom försvarssektorn (FMV, Försvarsmakten, MSB, Säpo etc.) ELLER inom stat/region/kommun men då **exklusivt** inriktat på totalförsvar, civilt försvar, krisberedskap, säkerhetsskydd eller samhällsviktig robusthet där managementkonsulter kan leverera.
    
    ❌ **ABSOLUT REVA / RENSA BORT OMEDELBART:**
       - **Bygg, anläggning, entreprenad, markarbeten, fastighetsförvaltning och VVS.**
       - **El, energi, VA (vatten/avlopp), infrastrukturbyggnation och fysiska installationer.**
       - **IT-drift, systemförvaltning, mjukvarulicenser och hårdvaruinköp** (såvida det inte rör ren strategisk IT-styrning/arkitektur inom säkerhetskänslig verksamhet).
       - **Rena varuinköp, fordon, livsmedel, städning, friskvård eller rent administrativa rutinuppdrag utan koppling till ledning/styrning.**
       - Om en upphandling har en bred titel (t.ex. "Konsulttjänster"), ta **endast** med den om brödtexten tydligt bekräftar att det handlar om management-, styrnings- eller ledningskonsulter inom försvar/säkerhet. Annars uteslut den.
    
    Returnera resultatet ENDAST som en giltig JSON-lista med relevanta objekt. Om inget matchar, returnera en tom lista `[]`. Inga markdown-backticks kring JSON-svaret (börja med [ och sluta med ]). Varje objekt ska ha exakt dessa nycklar:
    - "Myndighet": (Organisation/Köpare i Sverige)
    - "Upphandling": (Titel på upphandlingen)
    - "Deadline": (Sista svarsdag om det framgår, format ÅÅÅÅ-MM-DD, annars "Ej angivet")
    - "Omfattning": (Uppskattad omfattning i timmar, belopp eller tid, annars "Ej angivet")
    - "Sammanfattning": (En fyllig sammanfattning på 2-3 meningar som förklarar varför detta är ett relevant managementuppdrag inom Defence & Security)
    - "Saljvinkel": (Konkret rekommendation på hur konsultteamet inom management bör positionera sig)
    - "Källa": ({target_source_name})

    Text att analysera:
    {text_content[:15000]}
    """

# --- FLIK 1: FILER & ZIP ---
with tab_files:
    st.subheader("📥 Dra och droppa mailen (ZIP eller enskilda filer)")
    st.write("Skapa en ZIP-fil med dina nedladdade mail eller upphandlingsfiler och dra in den här nedanför!")

    uploaded_zip = st.file_uploader("Släpp din ZIP-fil här (eller välj filer)", type=["zip", "eml", "txt"], key="file_upload_widget")

    if uploaded_zip is not None:
        all_parsed_data = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        files_to_process = []
        
        if uploaded_zip.name.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(uploaded_zip.read())) as z:
                    for filename in z.namelist():
                        if filename.endswith(('.txt', '.eml', '.html', '.md')) and not filename.startswith('__MACOSX'):
                            with z.open(filename) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                files_to_process.append((filename, content))
            except Exception as e:
                st.error(f"Kunde inte läsa ZIP-filen: {e}")
        else:
            content = uploaded_zip.read().decode('utf-8', errors='ignore')
            files_to_process.append((uploaded_zip.name, content))

        if files_to_process:
            if st.button(f"🚀 Kör strikt management-analys på {len(files_to_process)} filer", type="primary", key="btn_files"):
                with st.spinner("Analyserar filer med strikt management-filter..."):
                    for file_name, file_content in files_to_process:
                        prompt = build_strict_prompt(file_name, file_content, today_str)
                        
                        try:
                            response = client.messages.create(
                                model="claude-3-5-haiku-20241022",
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
                                    parsed_data = json.loads(clean_json)
                                    if isinstance(parsed_data, list):
                                        all_parsed_data.extend(parsed_data)
                        except Exception:
                            continue
                    
                    if all_parsed_data:
                        st.session_state['parsed_tenders'] = all_parsed_data
                        st.success(f"✅ Analys klar! Hittade {len(all_parsed_data)} relevanta management-uppdrag.")
                    else:
                        st.warning("Hittade inga matchande management-upphandlingar i filerna (bygg, el, VA m.m. har rensats bort).")

# --- FLIK 2: SCANNA ALLT (VUNNET SIDOR + LÄNKAR) ---
with tab_scan:
    st.subheader("🌐 Automatisk skrapning och genomgång av Vunnet.se & alla direktlänkar")
    st.write("Med ett enda klick skannas det valda antalet sidor på Vunnet.se samt samtliga lagrade direktlänkar i sidomenyn, strikt filtrerat för Management inom Defence & Security.")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        start_page = st.number_input("Starta från Vunnet-sida", min_value=1, value=1, step=1)
    with col_v2:
        max_pages = st.number_input("Antal sidor att loopa igenom på Vunnet.se", min_value=1, max_value=162, value=3, step=1, help="Max 162 sidor finns tillgängliga på Vunnet.se")
    
    if st.button("🚀 Starta strikt helhetskanning (Management + Försvar)", type="primary", key="btn_scan_all"):
        master_parsed_data = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        total_steps = max_pages + len(all_sidebar_links)
        current_step = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. Skrapa Vunnet.se sidor
        for i in range(max_pages):
            current_page = start_page + i
            current_step += 1
            progress_pct = current_step / total_steps
            progress_bar.progress(min(progress_pct, 1.0))
            status_text.text(f"Skrapar Vunnet.se sida {current_page} (strikt management-filter)...")
            
            target_url = f"https://vunnet.se/upphandlingar?typ=alla&sida={current_page}"
            
            try:
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    page_text = soup.get_text(separator="\n", strip=True)
                    
                    if len(page_text) < 200:
                        break
                    
                    prompt = build_strict_prompt(f"Vunnet.se (Sida {current_page}, URL: {target_url})", page_text, today_str)
                    
                    response_ai = client.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=4000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    raw_output = "".join([block.text for block in response_ai.content if hasattr(block, "text")])
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
                            parsed_data = json.loads(clean_json)
                            if isinstance(parsed_data, list):
                                master_parsed_data.extend(parsed_data)
            except Exception:
                pass
            time.sleep(0.3)

        # 2. Skrapa alla direktlänkar i sidomenyn
        for link_info in all_sidebar_links:
            current_step += 1
            progress_pct = current_step / total_steps
            progress_bar.progress(min(progress_pct, 1.0))
            status_text.text(f"Skrapar portal: {link_info['name']}...")
            
            try:
                req = urllib.request.Request(link_info['url'], headers=headers)
                with urllib.request.urlopen(req, timeout=8) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    page_text = soup.get_text(separator="\n", strip=True)
                    
                    if len(page_text) < 150:
                        continue
                    
                    prompt = build_strict_prompt(link_info['name'], page_text, today_str)
                    
                    response_ai = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=4000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    raw_output = "".join([block.text for block in response_ai.content if hasattr(block, "text")])
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
                            parsed_data = json.loads(clean_json)
                            if isinstance(parsed_data, list):
                                master_parsed_data.extend(parsed_data)
            except Exception:
                pass
            time.sleep(0.3)

        progress_bar.empty()
        status_text.empty()
        
        if master_parsed_data:
            st.session_state['parsed_tenders'] = master_parsed_data
            st.success(f"✅ Helhetskanning klar! Hittade totalt {len(master_parsed_data)} relevanta management-uppdrag.")
        else:
            st.warning("Hittade inga matchande management-uppdrag (bygg, el, VA, entreprenad har filtrerats bort).")

# --- GEMENSAMT RESULTAT & EXPORT (FÖR BÅDA KÄLLORNA) ---
if 'parsed_tenders' in st.session_state and st.session_state['parsed_tenders']:
    st.markdown("---")
    st.subheader("📊 Granska uppdrag & Välj för Excel-export")
    
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
    
    st.markdown("### 🗂️ Detaljerad granskning")
    
    selected_indices = []
    for idx, item in enumerate(st.session_state['parsed_tenders']):
        with st.container():
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                if st.checkbox("Välj", key=f"chk_{idx}", label_visibility="collapsed"):
                    selected_indices.append(idx)
            with col2:
                st.markdown(f"**📌 {item.get('Myndighet', '')} – {item.get('Upphandling', '')}**")
                st.markdown(f"*Deadline:* `{item.get('Deadline', '')}` | *Omfattning:* `{item.get('Omfattning', '')}` | *Källa:* `{item.get('Källa', '')}`")
                st.markdown(f"*Sammanfattning:* {item.get('Sammanfattning', '')}")
                st.markdown(f"*Säljvinkel:* {item.get('Saljvinkel', '')}")
            st.divider()

    rows_for_excel = []
    for idx in selected_indices:
        item = st.session_state['parsed_tenders'][idx]
        rows_for_excel.append({
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Sammanfattning": item.get("Sammanfattning", ""),
            "Säljvinkel": item.get("Saljvinkel", ""),
            "Go/No-go": "",
            "Ansvarig konsult": "",
            "Deadline": item.get("Deadline", ""),
            "Omfattning": item.get("Omfattning", ""),
            "Källa": item.get("Källa", "")
        })
    
    rows_for_excel = []
    for idx in selected_indices:
        item = st.session_state['parsed_tenders'][idx]
        rows_for_excel.append({
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Sammanfattning": item.get("Sammanfattning", ""),
            "Säljvinkel": item.get("Saljvinkel", ""),
            "Go/No-go": "",
            "Ansvarig konsult": "",
            "Deadline": item.get("Deadline", ""),
            "Omfattning": item.get("Omfattning", ""),
            "Källa": item.get("Källa", "")
        })
    
    if rows_for_excel:
        df_master = pd.DataFrame(rows_for_excel)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_master.to_excel(writer, index=False, sheet_name='Upphandlingar')
        
        st.download_button(
            label=f"📥 Ladda ner Master-Excel ({len(rows_for_excel)} markerade uppdrag)",
            data=output.getvalue(),
            file_name=f"GTM_Management_Defence_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("💡 Bocka i minst ett uppdrag ovan för att aktivera nerladdning till Excel.")
