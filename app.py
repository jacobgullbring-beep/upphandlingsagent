import streamlit as st
import pandas as pd
import zipfile
import io
import re
import json
from email import message_from_bytes
import requests
from bs4 import BeautifulSoup

# --- SIDKONFIGURATION ---
st.set_page_config(
    page_title="PA Consulting - Intelligent Upphandlingsskrapa",
    page_icon="🛡️",
    layout="wide"
)

# --- ANTHROPIC / AI HJÄLPFUNKTIONER ---
def analyze_with_claude(text_content, detail_content="", api_key=""):
    """
    Analyserar upphandlingen med Claude API (eller simulerar om API-nyckel saknas).
    Går igenom både översiktstext och fördjupad detaljtext för att finna Pris/Omfattning.
    """
    if not api_key:
        # Fallback / Simulerad analys för demonstration
        is_construction = any(w in text_content.lower() for w in ["bygg", "entreprenad", "asfaltering", "målning", "rörledningar"])
        
        # Försök hitta pris/omfattning i detaljtexten via regex/nyckelord
        value_match = re.search(r'(\d+[\d\s\.]*\s*(?:SEK|kr|msek|miljoner))', detail_content, re.IGNORECASE)
        estimated_value = value_match.group(1) if value_match else "Ej angivet i sammandrag (Se underlag)"
        
        return {
            "kund": "Försvarsmakten / MSB (Identifierad)",
            "titel": "Konsultstöd & Strategisk Rådgivning",
            "cpv": "79417000-8 / 72220000",
            "omfattning": "2-4 konsultresurser under 24 månader med option på 12 mån." if detail_content else "Kräver djupdykning i underlag",
            "uppskattat_varde": estimated_value if detail_content else "1.5 - 3.0 MSEK (Uppskattat)",
            "matchning": "Låg (Bygg/Entreprenad)" if is_construction else "Hög",
            "saljvinkel": "Bortfiltrerad: Ej relevanta tjänster" if is_construction else "Lyft fram PA:s erfarenhet av totalförsvar och krisberedskap.",
            "deadline": "2026-10-30",
            "status": "Rensad (Bygg)" if is_construction else "Ny"
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""
        Du är en senior säljanalytiker på PA Consulting (Defence & Security).
        Granska följande upphandlingsnotis samt djupinformationen från detaljsidan:

        ÖVERSIKTSTEXT:
        {text_content}

        DETALJSIDA (DJUPGRANSKNING):
        {detail_content}

        Agera som ett strikt filter:
        1. Identifiera om detta är Bygg/Entreprenad/Hårdvara (Markera som Matchning: Låg, Status: Rensad).
        2. Om det är Management, IT/Cyber, Försvar, Säkerhet, Krishantering eller Rådgivning: Sätt Matchning: Hög eller Medium.
        3. Leta SÄRSKILT efter:
           - Uppskattat värde / Budget / Prisram (SEK)
           - Omfattning / Volym / Avtalslängd
           - Rekommenderad säljvinkel för PA Consulting.

        Svara ENBART i JSON-format med följande nycklar:
        {{"kund": "", "titel": "", "cpv": "", "omfattning": "", "uppskattat_varde": "", "matchning": "Hög/Medium/Låg", "saljvinkel": "", "deadline": "", "status": "Ny/Rensad"}}
        """

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        res_text = response.content[0].text
        # Extrahera JSON ur svaret
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return json.loads(res_text)
    except Exception as e:
        st.error(f"Fel vid AI-analys: {e}")
        return None

def fetch_deep_details(url):
    """
    Går in på den enskilda upphandlingens länk och hämtar detaljtexten
    för att komma åt omfattning och prisuppgifter.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Rensa bort skript och menyer, spara huvudsaklig brödtext
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            text = soup.get_text(separator=' ')
            # Rensa överflödiga blanksteg
            clean_text = ' '.join(text.split())
            return clean_text[:4000] # Ta med de första 4000 tecknen av detaljsidan
    except Exception:
        pass
    return "Kunde inte hämta detaljsida automatiskt (Länk kräver inloggning eller är blockerad)."


# --- SIDPANEL (INSTÄLLNINGAR & API) ---
st.sidebar.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400", use_container_width=True)
st.sidebar.title("PA Consulting 🛡️")
st.sidebar.subheader("Upphandlingsmotor")

api_key = st.sidebar.text_input("Claude API Key (Valfritt):", type="password", help="Ange din Anthropic API-nyckel för skarpa AI-analyser.")

fokus_områden = st.sidebar.multiselect(
    "Aktiva fokusområden:",
    ["Defence & Security", "Krisberedskap & Totalförsvar", "Cyber & IT-Säkerhet", "Management & Styrning"],
    default=["Defence & Security", "Krisberedskap & Totalförsvar"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Inställningar för Djupgranskning:**")
enable_deep_scrape = st.sidebar.checkbox("Klicka in på länkar (Hämta Pris/Omfattning)", value=True)
st.sidebar.caption("När denna är i bockad besöker appen respektive direktlänk för att hitta dolt pris och omfattning.")


# --- HUVUDLAYOUT & FLIKAR ---
st.title("🛡️ Upphandlingsportal & Säljmatchning")
st.markdown("Automatiserad insamling, djuplänks-analys och filtrering för **PA Consulting Defence & Security**.")

tab_input, tab_results, tab_history, tab_config = st.tabs([
    "📥 1. Datainsamling & Djupanalys", 
    "📊 2. Säljrapport & Excel-export", 
    "📜 3. Historik & Dubbletter",
    "⚙️ 4. Konfiguration"
])

# INITIALISERA SESSION STATE
if 'results_data' not in st.session_state:
    st.session_state['results_data'] = []

# --- FLIK 1: DATAINSAMLING ---
with tab_input:
    st.subheader("Välj inmatningskälla")
    
    source_choice = st.radio(
        "Hur vill du läsa in veckans upphandlingar?",
        ["📁 1. Ladda upp ZIP-fil (Mejl/Filer)", "✏️ 2. Klistra in text / Mejl manuellt", "🌐 3. Live-Sökning via Portallänkar"],
        horizontal=True
    )
    
    st.markdown("---")
    
    raw_entries = []
    
    # 1. ZIP-UPPLADDNING
    if "ZIP" in source_choice:
        uploaded_zip = st.file_uploader("Ladda upp ZIP-fil innehållande mejl (.eml, .txt, .msg):", type=["zip"])
        if uploaded_zip:
            with zipfile.ZipFile(uploaded_zip, 'r') as z:
                for filename in z.namelist():
                    if filename.endswith(('.eml', '.txt')):
                        file_bytes = z.read(filename)
                        if filename.endswith('.eml'):
                            msg = message_from_bytes(file_bytes)
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            else:
                                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            raw_entries.append({"source": filename, "text": body, "url": ""})
                        else:
                            raw_entries.append({"source": filename, "text": file_bytes.decode('utf-8', errors='ignore'), "url": ""})
            st.success(f"Läste in {len(raw_entries)} filer från ZIP-arkivet.")

    # 2. MANUELL INMATNING
    elif "Klistra in" in source_choice:
        manual_text = st.text_area(
            "Klistra in texten från bevakningsmail eller upphandlingslistor här:",
            height=250,
            placeholder="Klistra in hela mailet från e-Avrop, Mercell eller Kommers Annons..."
        )
        if manual_text.strip():
            # Dela upp i stycken per upphandling om möjligt
            snippets = manual_text.split("\n\n")
            for idx, snip in enumerate(snippets):
                if len(snip.strip()) > 30:
                    # Leta efter eventuell URL i texten
                    url_match = re.search(r'https?://[^\s]+', snip)
                    found_url = url_match.group(0) if url_match else ""
                    raw_entries.append({"source": f"Inklistrad text del {idx+1}", "text": snip, "url": found_url})

    # 3. LIVE WEBSÖKNING VIA LÄNKAR
    elif "Live-Sökning" in source_choice:
        st.markdown("##### Ange portallänkar att söka igenom:")
        target_urls = st.text_area(
            "Ange URL:er (en per rad):",
            value="https://www.e-avrop.com/notices/search.aspx\nhttps://www.kommersannons.se/valdemarsvik/Notice/Notice.aspx",
            height=100
        )
        
        col_pages, col_depth = st.columns(2)
        with col_pages:
            max_pages = st.slider("Antal sidor att loopa igenom per länk:", min_value=1, max_value=10, value=3)
        with col_depth:
            st.info(f"Appen kommer att söka igenom upp till {max_pages} sidor och klicka sig in på enskilda upphandlingar för detaljdata.")
            
        if st.button("🔍 Starta Live-skrapning av Länkar"):
            st.warning("Live-skrapning pågår. Hämtar listvyer och djuplänkar...")
            # Mockad/Simulerad skrapningsloop för illustration
            raw_entries = [
                {"source": "e-Avrop Sida 1", "text": "Upphandling av Säkerhetsskyddad IT-infrastruktur, Myndighet för Totalförsvar. Länk: https://e-avrop.com/item/101", "url": "https://e-avrop.com/item/101"},
                {"source": "Kommers Sida 1", "text": "Ramavtal Organisationsutveckling och Krishantering, Region Stockholm. Länk: https://kommers.se/item/202", "url": "https://kommers.se/item/202"},
                {"source": "Mercell Sida 2", "text": "Ombyggnad av spåranläggning och asfaltering i Malmö hamn. Länk: https://mercell.se/item/303", "url": "https://mercell.se/item/303"}
            ]

    # KÖRA ANALYSEN
    st.markdown("---")
    if raw_entries:
        if st.button("🚀 Kör Djupanalys & Generera Säljrapport", type="primary"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, entry in enumerate(raw_entries):
                status_text.text(f"Bearbetar post {i+1} av {len(raw_entries)}: {entry['source']}...")
                
                detail_text = ""
                # Om djuplänkning är aktiverat och URL finns, klicka in!
                if enable_deep_scrape and entry.get("url"):
                    status_text.text(f"Klickar in på detaljsida: {entry['url']}...")
                    detail_text = fetch_deep_details(entry["url"])
                
                # Kör AI-analysen
                ai_res = analyze_with_claude(entry["text"], detail_content=detail_text, api_key=api_key)
                
                if ai_res:
                    ai_res["kalla"] = entry["source"]
                    ai_res["lank"] = entry.get("url", "Ej angiven")
                    results.append(ai_res)
                
                progress_bar.progress((i + 1) / len(raw_entries))
            
            st.session_state['results_data'] = results
            status_text.text("Analys klar!")
            st.success(f"Analyserat {len(results)} upphandlingar med djupgranskning!")


# --- FLIK 2: SÄLJRAPPORT & RESULTAT ---
with tab_results:
    st.subheader("📊 Säljrapport - Identifierade Möjligheter")
    
    if st.session_state['results_data']:
        df = pd.DataFrame(st.session_state['results_data'])
        
        # Sortera och filtrera
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            visa_rensade = st.checkbox("Visa även rensade upphandlingar (Bygg/Entreprenad)", value=False)
        with col_f2:
            min_match = st.selectbox("Filtrera på matchningsgrad:", ["Alla", "Endast Hög", "Hög & Medium"])
        
        # Applicera filter
        df_filtered = df.copy()
        if not visa_rensade:
            df_filtered = df_filtered[df_filtered["status"] != "Rensad (Bygg)"]
        if min_match == "Endast Hög":
            df_filtered = df_filtered[df_filtered["matchning"] == "Hög"]
        elif min_match == "Hög & Medium":
            df_filtered = df_filtered[df_filtered["matchning"].isin(["Hög", "Medium"])]
            
        # Snygga till kolumnnamn för tabellen
        display_columns = {
            "kund": "Kund / Myndighet",
            "titel": "Upphandling & Titel",
            "uppskattat_varde": "Uppskattat Värde / Pris",
            "omfattning": "Omfattning / Volym",
            "matchning": "Matchning",
            "saljvinkel": "Rekommenderad Säljvinkel (PA)",
            "deadline": "Deadline",
            "lank": "Länk"
        }
        
        df_display = df_filtered.rename(columns=display_columns)
        
        st.markdown(f"**Visar {len(df_filtered)} relevanta upphandlingar:**")
        st.dataframe(df_display, use_container_width=True)
        
        # EXCEL EXPORT
        st.markdown("### 📥 Exportera till Säljteamet")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Veckans Upphandlingar')
        excel_bytes = output.getvalue()
        
        st.download_button(
            label="📊 Ladda ner formaterad Excel-rapport (.xlsx)",
            data=excel_bytes,
            file_name="PA_Consulting_Upphandlingsrapport.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Inga resultat ännu. Gå till fliken 'Datainsamling' och kör en analys först.")


# --- FLIK 3: HISTORIK & DUBBLETTER ---
with tab_history:
    st.subheader("📜 Historik & Dubblettkontroll")
    st.markdown("Här hålls koll på tidigare analyserade uppdrag för att undvika att skicka samma möjligheter två gånger till säljarna.")
    
    # Mockad historik
    hist_data = [
        {"Datum": "2026-09-20", "Kund": "FMV", "Titel": "Systemstöd Säkerhetsskydd", "Status": "Skickad till säljare", "Mottagare": "Stockholm Defence Team"},
        {"Datum": "2026-09-18", "Kund": "Polismyndigheten", "Titel": "Ledarskapsutveckling", "Status": "Skickad till säljare", "Mottagare": "Management Team"}
    ]
    st.dataframe(pd.DataFrame(hist_data), use_container_width=True)


# --- FLIK 4: KONFIGURATION ---
with tab_config:
    st.subheader("⚙️ Systeminställningar & Promptar")
    st.markdown("""
    **Sök- och filterkriterier för PA Consulting:**
    - **Inkluderas:** Defence, Säkerhetsskydd, Totalförsvar, Krishantering, Cyber, IT-strategi, Management, Beredskap.
    - **Exkluderas (Rensas bort):** Bygg, Entreprenad, Hårdvaruinköp, Väg & Banarbeten, Fastighetsskötsel, Städning.
    """)
