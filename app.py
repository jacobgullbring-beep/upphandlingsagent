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

with st.sidebar.expander("Stora städer & Kommuner"):
    st.markdown("- [Göteborgs Stad](https://app.mercell.com/org/goteborgs_stads_upphandlingar)")
    st.markdown("- [Malmö Stad](https://app.mercell.com/org/kommersannons.se/malmo/Notice/NoticeList.aspx)")
    st.markdown("- [Uppsala Kommun](https://app.mercell.com/org/uppsala_kommun/)")
    st.markdown("- [Linköping](https://www.e-avrop.com/linkoping//e-Upphandling/Default.aspx)")
    st.markdown("- [Västerås](https://www.vasteras.ses/naringsliv-och-arbete/upphandling-och-inkop/pagaende-upphandlingar.html)")
    st.markdown("- [Örebro Kommun](https://app.mercell.com/org/orebro_kommuns_upphandlingar)")
    st.markdown("- [Helsingborg](https://foretagare.helsingborg.se/upphandling/annonserade-upphandlingar-direktupphandlingar-och-planerade-upphandlingar/)")
    st.markdown("- [Jönköpings Kommun](https://app.mercell.com/org/jonkopings_kommun)")
    st.markdown("- [Norrköping](https://www.e-avrop.com/norrk/e-Upphandling/Default.aspx)")
    st.markdown("- [Umeå Kommun](https://www.umea.se/jobbochforetagande/upphandlingochinkop/upphandlingar.4.1c16b00a1742340e02eeac.html)")
    st.markdown("- [Lunds Kommun](https://app.mercell.com/org/lunds_kommuns_upphandlingar)")
    st.markdown("- [Järfälla Kommun](https://se.openprocurements.com/buyer/jarfalla-kommun/)")

with st.sidebar.expander("Övriga portaler & system"):
    st.markdown("- [Tendsign](https://tendsign.com/public/list_public_procurements.aspx?IndividualID=xUDxnN2SZS/xCpdaCME2fwA=)")
    st.markdown("- [Bidmonkey](https://app.bidmonkey.se/webview?u=ea2e8da8c15d516fa894)")
    st.markdown("- [Mercell (Sverige Sök)](https://app.mercell.com/search?filter=delivery_place_code%3ASE)")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# --- HUVUDGRÄNSSNITT MED FLIKAR FÖR OLIKA INDATAKÄLLOR ---
tab_files, tab_vunnet = st.tabs(["📂 Filer & ZIP-arkiv", "🌐 Direkt från Vunnet.se"])

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
            if st.button(f"🚀 Kör AI-analys på {len(files_to_process)} filer med Haiku", type="primary", key="btn_files"):
                with st.spinner("Analyserar filer med Claude 3.5 Haiku..."):
                    for file_name, file_content in files_to_process:
                        prompt = f"""
                        Du är en expert på Business Development och GTM inom Defence & Security på den svenska marknaden (försvar, säkerhet, totalförsvar, civilt försvar, krisberedskap och robusthet) för ett ledande konsultbolag. 
                        Dagens datum är {today_str}. 
                        Analysera texten från filen '{file_name}' grundligt.
                        
                        REGLER FÖR FILTRERING & DJUPLÄSNING:
                        1. **INKLUDERA:** 
                           - Alla upphandlingar från den svenska försvarssektorn (FMV, Försvarsmakten, MSB, Säpo etc.).
                           - Upphandlingar från **svenska kommuner, regioner och ramavtal** som rör **civilt försvar, totalförsvar, krisberedskap, säkerhetsskydd, informationssäkerhet, robusthet, skyddsobjekt eller samhällsviktig verksamhet**.
                           - **Dolda uppdrag:** Läs brödtexten! Även om en titel verkar bred (t.ex. "Ledarutveckling", "Organisationsstöd", "Analys"), ta med den om det framgår att det rör krisorganisationer eller säkerhetskänslig verksamhet.
                        2. **RENSA BORT:** Helt vanliga, rent civila upphandlingar utan koppling till säkerhet/beredskap.
                        
                        Returnera resultatet ENDAST som en giltig JSON-lista med relevanta objekt. Om inget matchar i filen, returnera en tom lista `[]`. Inga markdown-backticks kring JSON-svaret (börja med [ och sluta med ]). Varje objekt ska ha exakt dessa nycklar:
                        - "Myndighet": (Organisation/Köpare i Sverige)
                        - "Upphandling": (Titel på upphandlingen)
                        - "Deadline": (Sista svarsdag om det framgår, format ÅÅÅÅ-MM-DD, annars "Ej angivet")
                        - "Omfattning": (Uppskattad omfattning i timmar, belopp eller tid, annars "Ej angivet")
                        - "Sammanfattning": (En fyllig sammanfattning på 2-3 meningar om varför den är relevant för Defence & Security)
                        - "Saljvinkel": (Konkret rekommendation på hur konsultteamet bör positionera sig)
                        - "Källa": (Ange filnamnet: {file_name})

                        Text att analysera:
                        {file_content[:15000]}
                        """
                        
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
                        except Exception as e:
                            continue
                    
                    if all_parsed_data:
                        st.session_state['parsed_tenders'] = all_parsed_data
                        st.success(f"✅ Analys klar! Hittade {len(all_parsed_data)} relevanta uppdrag totalt.")
                    else:
                        st.warning("Hittade inga matchande upphandlingar i de upplupna filerna.")

# --- FLIK 2: DIREKT FRÅN VUNNET.SE ---
with tab_vunnet:
    st.subheader("🌐 Automatisk skrapning och loop av Vunnet.se")
    st.write("Här kan du skanna av Vunnet.se direkt genom att ange hur många sidor du vill loopa igenom (sida för sida).")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        start_page = st.number_input("Starta från sida", min_value=1, value=1, step=1)
    with col_v2:
        max_pages = st.number_input("Antal sidor att loopa igenom", min_value=1, max_value=162, value=5, step=1, help="Max 162 sidor finns tillgängliga på Vunnet.se")
    
    if st.button("🚀 Starta automatisk skrapning från Vunnet.se", type="primary", key="btn_vunnet"):
        vunnet_parsed_data = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        for i in range(max_pages):
            current_page = start_page + i
            progress_pct = (i + 1) / max_pages
            progress_bar.progress(progress_pct)
            status_text.text(f"Skrapar sida {current_page} av {start_page + max_pages - 1}...")
            
            target_url = f"https://vunnet.se/upphandlingar?typ=alla&sida={current_page}"
            
            try:
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    page_text = soup.get_text(separator="\n", strip=True)
                    
                    # Om sidan är i princip tom eller saknar innehåll bryter vi loopen
                    if len(page_text) < 200:
                        status_text.text(f"Nådde slutet vid sida {current_page} (inga fler träffar hittades).")
                        time.sleep(1)
                        break
                    
                    # Skicka till Claude för AI-analys av sidan
                    prompt = f"""
                    Du är en expert på Business Development och GTM inom Defence & Security på den svenska marknaden (försvar, säkerhet, totalförsvar, civilt försvar, krisberedskap och robusthet) för ett ledande konsultbolag. 
                    Dagens datum är {today_str}. 
                    Analysera texten från webbsidan från Vunnet.se (Sida {current_page}, URL: {target_url}) grundligt.
                    
                    REGLER FÖR FILTRERING & DJUPLÄSNING:
                    1. **INKLUDERA:** 
                       - Alla upphandlingar från den svenska försvarssektorn (FMV, Försvarsmakten, MSB, Säpo etc.).
                       - Upphandlingar från **svenska kommuner, regioner och ramavtal** som rör **civilt försvar, totalförsvar, krisberedskap, säkerhetsskydd, informationssäkerhet, robusthet, skyddsobjekt eller samhällsviktig verksamhet**.
                       - **Dolda uppdrag:** Läs brödtexten! Även om en titel verkar bred (t.ex. "Ledarutveckling", "Organisationsstöd", "Analys"), ta med den om det framgår att det rör krisorganisationer eller säkerhetskänslig verksamhet.
                    2. **RENSA BORT:** Helt vanliga, rent civila upphandlingar utan koppling till säkerhet/beredskap.
                    
                    Returnera resultatet ENDAST som en giltig JSON-lista med relevanta objekt. Om inget matchar på sidan, returnera en tom lista `[]`. Inga markdown-backticks kring JSON-svaret (börja med [ och sluta med ]). Varje objekt ska ha exakt dessa nycklar:
                    - "Myndighet": (Organisation/Köpare i Sverige)
                    - "Upphandling": (Titel på upphandlingen)
                    - "Deadline": (Sista svarsdag om det framgår, format ÅÅÅÅ-MM-DD, annars "Ej angivet")
                    - "Omfattning": (Uppskattad omfattning i timmar, belopp eller tid, annars "Ej angivet")
                    - "Sammanfattning": (En fyllig sammanfattning på 2-3 meningar om varför den är relevant för Defence & Security)
                    - "Saljvinkel": (Konkret rekommendation på hur konsultteamet bör positionera sig)
                    - "Källa": (Ange URL: {target_url})

                    Text att analysera från sidan:
                    {page_text[:15000]}
                    """
                    
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
                                vunnet_parsed_data.extend(parsed_data)
                                
            except Exception as e:
                # Om en sida misslyckas hoppar vi över den och fortsätter loopen
                continue
            
            # Kort paus för att inte överbelasta servern
            time.sleep(0.5)
            
        progress_bar.empty()
        status_text.empty()
        
        if vunnet_parsed_data:
            st.session_state['parsed_tenders'] = vunnet_parsed_data
            st.success(f"✅ Vunnet.se-skrapning klar! Hittade {len(vunnet_parsed_data)} relevanta uppdrag totalt.")
        else:
            st.warning("Hittade inga matchande upphandlingar på de skannade sidorna.")

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
            "Nunfattning": item.get("Omfattning", ""),
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
            file_name=f"GTM_Defence_Sverige_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("💡 Bocka i minst ett uppdrag ovan för att aktivera nerladdning till Excel.")
