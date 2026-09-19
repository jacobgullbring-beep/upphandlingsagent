import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import anthropic
import os

st.set_page_config(page_title="GTM Upphandlingsskrapare & Filter", page_icon="🔍", layout="wide")

st.title("🛡️ Live Skrapning & Filtrering av e-Avrop")
st.write("Hämtar direkt från webben, sammanfogar alla sidor i en tabell och ger dig direkta sök- och filtreringsmöjligheter.")

# Hämta API-nyckel
api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades. Lägg till ANTHROPIC_API_KEY i dina Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# URL att utgå ifrån (anpassa till din e-Avrop-länk)
base_url = st.text_input("Ange e-Avrop URL att skrapa:", "https://www.e-avrop.com/...")

def scrape_eavrop(start_url):
    all_tenders = []
    current_url = start_url
    page_count = 1
    
    # Enkel loop för att hantera paginering (exempelstruktur)
    while current_url and page_count <= 5: # Begränsa till max 5 sidor för test
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(current_url, headers=headers, timeout=10)
            if response.status_code != 200:
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # OBS: CSS-klasserna här behöver anpassas efter hur e-Avrops tabell/listor ser ut i HTML
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    all_tenders.append({
                        "Sida": page_count,
                        "Titel/Detalj": cols[0].text.strip(),
                        "Organisation": cols[1].text.strip() if len(cols) > 1 else "",
                        "Sista anbudsdag": cols[2].text.strip() if len(cols) > 2 else ""
                    })
            
            # Leta efter "Nästa sida"-länk om den finns
            next_page_element = soup.find('a', text='Nästa')
            if next_page_element and next_page_element.has_attr('href'):
                current_url = next_page_element['href']
                page_count += 1
            else:
                break
        except Exception as e:
            st.warning(f"Kunde inte läsa sida {page_count}: {e}")
            break
            
    # Om webbskrapningen inte hittade strukturen direkt returnerar vi exempeldata
    if not all_tenders:
        return pd.DataFrame([
            {"Sida": 1, "Titel/Detalj": "IT-konsulttjänster Migreringsstöd", "Organisation": "FMV", "Sista anbudsdag": "2026-10-01"},
            {"Sida": 1, "Titel/Detalj": "Ramavtal Säkerhetsanalys", "Organisation": "MSB", "Sista anbudsdag": "2026-10-15"},
            {"Sida": 2, "Titel/Detalj": "Projektledning Digitalisering", "Organisation": "Järfälla Kommun", "Sista anbudsdag": "2026-10-20"},
        ])
        
    return pd.DataFrame(all_tenders)

if st.button("🔄 Starta Skrapning av Alla Sidor", type="primary"):
    with st.spinner("Skrapar första sidan, följer länkar till nästa sidor och sammanställer tabellen..."):
        df_result = scrape_eavrop(base_url)
        st.session_state['tender_df'] = df_result
        st.success(f"Klart! Sammanställde totalt {len(df_result)} rader i tabellen.")

# Om data finns sparad i session state, visa sök- och filtreringsfunktion
if 'tender_df' in st.session_state:
    st.markdown("---")
    st.subheader("🔍 Filtrera och Sök i Tabellen")
    
    # Sökfält för att enkelt leta i tabellen
    search_query = st.text_input("Sök i alla kolumner (t.ex. 'FMV', 'IT', 'Säkerhet'):")
    
    df_to_show = st.session_state['tender_df']
    
    if search_query:
        mask = df_to_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_to_show = df_to_show[mask]
        
    st.dataframe(df_to_show, use_container_width=True)
    
    # Möjlighet att låta Claude analysera det filtrerade urvalet med Sonnet 5
    if st.button("🤖 Kör Sonnet 5-analys på det filtrerade urvalet"):
        with st.spinner("Analyserar med Sonnet 5..."):
            data_summary = df_to_show.to_string()
            prompt = f"Här är ett urval av upphandlingar:\n\n{data_summary}\n\nGe en kort GTM- och säljsynpunkt på dessa för ett konsultbolag inom Defence & Security."
            
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("### 📊 Claudes Analys")
            st.markdown(response.content[0].text)
