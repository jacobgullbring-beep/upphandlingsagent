import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsskrapare & Filter", page_icon="🔍", layout="wide")

st.title("🛡️ e-Avrop Live-skrapare & Filtrering")
st.write("Skrapar upphandlingar från e-Avrop med korrigerade kolumner.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

TARGET_URL = "https://www.e-avrop.com/e-Upphandling/Default.aspx"

def scrape_e_avrop(base_url):
    all_tenders = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    with st.spinner("Hämtar data från e-Avrop..."):
        try:
            response = requests.get(base_url, headers=headers, timeout=15)
            if response.status_code != 200:
                st.error(f"Kunde inte nå sidan, statuskod: {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    # Säkerställ att raden har tillräckligt med kolumner för en upphandling
                    if len(cols) >= 5:
                        cols_text = [col.text.strip() for col in cols]
                        
                        # Filtrera bort skräprader (navigering, sidnummer, knappar)
                        if cols_text[0] and "Logga in" not in cols_text[0] and "Bevaka" not in cols_text[0] and not cols_text[0].isdigit():
                            all_tenders.append({
                                "Titel": cols_text[0],
                                "Publicerad": cols_text[1],
                                "Organisation": cols_text[2],
                                "Kontext / CPV": cols_text[3],
                                "Deadline": cols_text[4]
                            })
                            
        except Exception as e:
            st.warning(f"Ett fel uppstod vid skrapning: {e}")

    return pd.DataFrame(all_tenders).drop_duplicates()

if st.button("🚀 Starta skrapning", type="primary"):
    df_result = scrape_e_avrop(TARGET_URL)
    
    if not df_result.empty:
        st.session_state['tender_df'] = df_result
        st.success(f"Klart! Hittade {len(df_result)} giltiga upphandlingar.")
    else:
        st.error("Ingen data hittades.")

if 'tender_df' in st.session_state and not st.session_state['tender_df'].empty:
    st.markdown("---")
    st.subheader("🔍 Filtrera och Sök i Upphandlingar")
    
    search_query = st.text_input("Sök i tabellen (t.ex. Region, IT, säkerhet):")
    df_to_show = st.session_state['tender_df']
    
    if search_query:
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
        
    st.info(f"Visar {len(df_to_show)} rader")
    st.dataframe(df_to_show, use_container_width=True)
