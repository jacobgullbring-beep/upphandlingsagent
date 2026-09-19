import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ e-Avrop Säljbevakning (Senaste upphandlingarna)")
st.write("Skrapar de senaste sidorna (1–10) från e-Avrop och genererar vassa GTM-säljinsikter med Claude.")

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
                    if cols_text[0] and "Logga in" not in cols_text[0] and "Bevaka" not in cols_text[0] and not cols_text[0].isdigit():
                        tenders.append({
                            "Titel": cols_text[0],
                            "Publicerad": cols_text[1],
                            "Organisation": cols_text[2],
                            "Kontext / CPV": cols_text[3],
                            "Deadline": cols_text[4]
                        })
        return tenders

    with st.spinner("Hämtar de senaste upphandlingarna från e-Avrop (sida 1–10)..."):
        try:
            # Hämta sida 1
            response = session.get(TARGET_URL, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                all_tenders.extend(extract_rows(soup))

            # Hämta sidor 2 till 10 för det dagsaktuella flödet
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

    return pd.DataFrame(all_tenders).drop_duplicates()

if st.button("🚀 Hämta de senaste upphandlingarna (Sida 1–10)", type="primary"):
    df_result = scrape_recent_tenders()
    
    if not df_result.empty:
        st.session_state['tender_df'] = df_result
        st.success(f"Klart! Hittade {len(df_result)} unika upphandlingar.")
    else:
        st.error("Ingen data hittades.")

if 'tender_df' in st.session_state and not st.session_state['tender_df'].empty:
    st.markdown("---")
    st.subheader("🔍 Sök och Analysera med Claude")
    
    search_query = st.text_input("Filtrera tabellen (t.ex. IT, säkerhet, ramavtal, region):")
    df_to_show = st.session_state['tender_df']
    
    if search_query:
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
        
    st.info(f"Visar {len(df_to_show)} upphandlingar")
    
    # Dölj "Kontext / CPV"-kolumnen i själva tabellen genom att visa utvalda kolumner
    columns_to_display = ["Titel", "Publicerad", "Organisation", "Deadline"]
    st.dataframe(df_to_show[columns_to_display], use_container_width=True)

    # Dold/expandering för kontext om man vill kika närmare
    with st.expander("📂 Visa råkontext & CPV-koder för träffarna"):
        for idx, row in df_to_show.iterrows():
            st.markdown(f"**{row['Organisation']} – {row['Titel']}**")
            st.caption(f"Kontext / CPV: {row['Kontext / CPV']}")
            st.markdown("---")

    if st.button("💡 Kör GTM-analys på filtrerade upphandlingar"):
        with st.spinner("Genererar säljinsikter med Claude..."):
            analysis_results = []
            # Analyserar upp till de 10 översta i den filtrerade listan
            subset = df_to_show.head(10)
            for idx, row in subset.iterrows():
                prompt = f"""
                Du är en expert på Business Development / Go-To-Market (GTM) för konsultbolag inom offentlig sektor, management och IT/säkerhet.
                
                Analysera följande upphandling:
                Organisation: {row['Organisation']}
                Titel: {row['Titel']}
                Kontext: {row['Kontext / CPV']}
                Deadline: {row['Deadline']}
                
                Ge korta och vassa punkter för säljteamet:
                1. **Affärsmöjlighet:** Vad är värdet/potentialen?
                2. **Säljvinkel / GTM-strategi:** Hur bör vi angripa detta (direkt till myndigheten eller som partner/underleverantör till vinnaren)?
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

            st.markdown("### 📊 GTM- och Säljinsikter")
            for item in analysis_results:
                with st.expander(f"📌 {item['Organisation']} – {item['Titel']}"):
                    st.markdown(item["GTM-Analys"])
