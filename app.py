import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsbevakning - Defence & Security / IT", page_icon="🛡️", layout="wide")

st.title("🛡️ GTM Säljbevakning – Försvar, IT-säkerhet & Offentlig Sektor")
st.write("Skrapar e-Avrop och filtrerar automatiskt fram relevanta affärer för försvar, IT och kommun/region med hjälp av Claude.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets eller miljövariabler.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

TARGET_URL = "https://www.e-avrop.com/e-Upphandling/Default.aspx"

def scrape_recent_tenders():
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
                        if title.isdigit():
                            continue
                        if len(cols_text) > 1 and all(c.isdigit() for c in cols_text if c):
                            continue
                            
                        tenders.append({
                            "Titel": title,
                            "Publicerad": cols_text[1],
                            "Organisation": cols_text[2],
                            "Kontext / CPV": cols_text[3],
                            "Deadline": cols_text[4]
                        })
        return tenders

    with st.spinner("Hämtar de senaste upphandlingarna från e-Avrop (sida 1–10)..."):
        try:
            response = session.get(TARGET_URL, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                all_tenders.extend(extract_rows(soup))

            for page in range(2, 11):
                page_url = f"{TARGET_URL}?page={page}"
                res = session.get(page_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    page_soup = BeautifulSoup(res.text, 'html.parser')
                    rows = extract_rows(page_soup)
                    if not rows:
                        break
                    all_tenders.extend(rows)
        except Exception as e:
            st.warning(f"Ett fel uppstod vid skrapning: {e}")

    df = pd.DataFrame(all_tenders).drop_duplicates()
    if not df.empty:
        df = df[~df['Titel'].astype(str).str.match(r'^\d+$')]
        
    return df

if st.button("🚀 Hämta de senaste upphandlingarna (Sida 1–10)", type="primary"):
    df_result = scrape_recent_tenders()
    
    if not df_result.empty:
        st.session_state['tender_df'] = df_result
        st.success(f"Klart! Hittade {len(df_result)} unika upphandlingar.")
    else:
        st.error("Ingen data hittades.")

if 'tender_df' in st.session_state and not st.session_state['tender_df'].empty:
    st.markdown("---")
    st.subheader("🔍 Filtrering efter avdelningens fokusområden")
    
    # Snabbfilter-knappar /selectbox för avdelningens kärnområden
    fokus_val = st.selectbox(
        "Välj fokusområde för filtrering:",
        [
            "Alla hämtade upphandlingar", 
            "🛡️ Försvar & Säkerhet (försvar, fmv, msb, skydd, beredskap)", 
            "💻 IT & Digitalisering (it, digital, system, moln, säkerhet)", 
            "🏛️ Kommun & Region (kommun, region, förvaltning)"
        ]
    )
    
    df_to_show = st.session_state['tender_df'].copy()
    
    # Applicera filter baserat på val
    if "Försvar & Säkerhet" in fokus_val:
        keywords = ["försvar", "fmv", "msb", "säkerhet", "skydd", "beredskap", "kris", "militär"]
        pattern = '|'.join(keywords)
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(pattern, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
    elif "IT & Digitalisering" in fokus_val:
        keywords = ["it", "digital", "system", "moln", "mjukvara", "data", "cyber", "programvara"]
        pattern = '|'.join(keywords)
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(pattern, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
    elif "Kommun & Region" in fokus_val:
        keywords = ["kommun", "region", "stad", "förvaltning", "kommunal"]
        pattern = '|'.join(keywords)
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(pattern, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]

    # Fritextsökning utöver snabbfiltret
    search_query = st.text_input("Eller sök fritt på specifik nyckelord/organisation:")
    if search_query:
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
        
    st.info(f"Visar {len(df_to_show)} matchande upphandlingar")
    
    columns_to_display = ["Titel", "Publicerad", "Organisation", "Deadline"]
    st.dataframe(df_to_show[columns_to_display], use_container_width=True)

    with st.expander("📂 Visa råkontext & CPV-koder för träffarna"):
        for idx, row in df_to_show.iterrows():
            st.markdown(f"**{row['Organisation']} – {row['Titel']}**")
            st.caption(f"Kontext / CPV: {row['Kontext / CPV']}")
            st.markdown("---")

    if st.button("💡 Kör skräddarsydd GTM-analys med Claude"):
        with st.spinner("Genererar strategiska säljinsikter för avdelningen..."):
            analysis_results = []
            subset = df_to_show.head(10)
            for idx, row in subset.iterrows():
                prompt = f"""
                Du är en expert på Business Development / Go-To-Market (GTM) för ledande konsultbolag inom Defence & Security, management och IT-säkerhet.
                
                Analysera följande upphandling med fokus på hur vi bäst kan positionera oss:
                Organisation: {row['Organisation']}
                Titel: {row['Titel']}
                Kontext: {row['Kontext / CPV']}
                Deadline: {row['Deadline']}
                
                Ge korta, vassa och strategiska punkter för säljteamet:
                1. **Affärsmöjlighet & Relevans:** Varför är detta intressant för en avdelning inriktad på försvar, säkerhet eller komplexa samhällsaktörer?
                2. **GTM-Strategi / Säljvinkel:** Bör vi gå in direkt som huvudleverantör, erbjuda specialistkompetens (t.ex. inom IT-säkerhet/programledning), eller söka partner/underleverantörsskap?
                """
                
                try:
                    response = client.messages.create(
                        model="claude-3-5-sonnet-latest",
                        max_tokens=400,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analysis_results.append({
                        "Organisation": row['Organisation'],
                        "Titel": row['Titel'],
                        "GTM-Analys": response.content[0].text
                    })
                except Exception as e:
                    continue

            st.markdown("### 📊 Strategiska GTM- och Säljinsikter")
            for item in analysis_results:
                with st.expander(f"📌 {item['Organisation']} – {item['Titel']}"):
                    st.markdown(item["GTM-Analys"])
