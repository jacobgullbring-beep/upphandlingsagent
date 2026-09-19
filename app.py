import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsskrapare & Filter", page_icon="🔍", layout="wide")

st.title("🛡️ e-Avrop Live-skrapare & Filtrering")
st.write("Skrapar automatiskt alla sidor från e-Avrop, samlar allt i en tabell och låter dig filtrera direkt.")

# Hämta API-nyckel
api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades. Lägg till ANTHROPIC_API_KEY i dina Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

TARGET_URL = "https://www.e-avrop.com/e-Upphandling/Default.aspx"

def scrape_all_pages(base_url):
    all_tenders = []
    page = 1
    max_pages = 20  - # Säkerhetsspärr så loppen inte fastnar i oändlighet
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    with st.spinner("Skrapar e-Avrop sida för sida..."):
        while page <= max_pages:
            # Bygg URL (e-Avrops pagineringsstruktur kan variera, vi hanterar standard query-parametrar eller stannar av om sidan är tom)
            if page == 1:
                current_url = base_url
            else:
                # Exempel på pagineringsparameter, justeras beroende på hur sajtens länkstruktur ser ut
                separator = "&" if "?" in base_url else "?"
                current_url = f"{base_url}{separator}page={page}"

            try:
                response = requests.get(current_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Leta efter tabellrader i sökresultatet
                rows = soup.find_all('tr')
                found_on_page = 0
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        cols_text = [col.text.strip() for col in cols]
                        all_tenders.append({
                            "Sida": page,
                            "Titel / Detalj": cols_text[0] if len(cols_text) > 0 else "",
                            "Organisation": cols_text[1] if len(cols_text) > 1 else "",
                            "Sista anbudsdag / Info": cols_text[2] if len(cols_text) > 2 else ""
                        })
                        found_on_page += 1
                
                # Om inga tabellrader hittades på denna sida har vi nått slutet
                if found_on_page == 0 and page > 1:
                    break
                    
                page += 1
            except Exception as e:
                st.warning(f"Kunde inte läsa sida {page}: {e}")
                break

    # Om skrapningen inte hittar tabellen (pga hård struktur eller skydd), skickar vi med en indikation
    if not all_tenders:
        return pd.DataFrame()
        
    return pd.DataFrame(all_tenders)

if st.button("🚀 Starta skrapning av alla sidor", type="primary"):
    df_result = scrape_all_pages(TARGET_URL)
    
    if not df_result.empty:
        st.session_state['tender_df'] = df_result
        st.success(f"Klart! Skrapade totalt {len(df_result)} rader.")
    else:
        st.error("Kunde inte extrahera tabeller automatiskt från den länkade sidan. Kontrollera om sidan kräver inloggning eller JavaScript-rendering.")

# Om data finns i session state, visa filtrering och sök
if 'tender_df' in st.session_state and not st.session_state['tender_df'].empty:
    st.markdown("---")
    st.subheader("🔍 Filtrera och Sök i Alla Upphandlingar")
    
    # Sökfält
    search_query = st.text_input("Sök i tabellen (t.ex. kommun, IT, säkerhet, datum):")
    
    df_to_show = st.session_state['tender_df']
    
    if search_query:
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
        
    st.info(𝐠 Visar {len(df_to_show)} av {len(st.session_state['tender_df'])} totala rader)
    st.dataframe(df_to_show, use_container_width=True)
    
    # Valfritt: Analysera med Claude
    if st.button("🤖 Kör Sonnet 5-analys på det filtrerade urvalet"):
        with st.spinner("Analyserar med Sonnet 5..."):
            summary_data = df_to_show.head(30).to_string() # Skickar max 30 rader för att hålla token-gränser
            prompt = f"Här är ett urval av skrapade upphandlingar:\n\n{summary_data}\n\nGe en kort GTM- och säljsynpunkt på dessa för ett konsultbolag inom Defence & Security / Management."
            
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("### 📊 Claudes Analys")
            st.markdown(response.content[0].text)
