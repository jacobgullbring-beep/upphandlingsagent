import streamlit as st
import requests
from bs4 import BeautifulSoup
import anthropic

# 1. Sidkonfiguration
st.set_page_config(
    page_title="Upphandlingsagent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Offentliga Upphandlingar – Automatiskt Filter")
st.write("Hämtar aktuella upphandlingar från e-Avrop och filtrerar ut relevanta konsult- och managementuppdrag med hjälp av Claude.")

# 2. Hämta API-nyckel från Streamlit Secrets
api_key = st.secrets.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("⚠️ Ingen `ANTHROPIC_API_KEY` hittades i Streamlit Secrets. Gå till Settings -> Secrets och lägg till din nyckel.")
    st.stop()

# 3. Knapp för att starta analysen
if st.button("Hämta & Analysera Upphandlingar", type="primary"):
    with st.spinner("Hämtar data från e-Avrop och analyserar med Claude..."):
        
        # Steg A: Hämta e-Avrops publika sida
        url = "https://www.e-avrop.com/UpphandlingDefault.aspx"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                st.error(f"Kunde inte hämta sidan från e-Avrop. Statuskod: {response.status_code}")
                st.stop()
        except Exception as e:
            st.error(f"Ett nätverksfel uppstod vid anrop till e-Avrop: {e}")
            st.stop()

        # Steg B: Extrahera texten från tabellen
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table") 
        raw_text = table.get_text(separator="\n", strip=True) if table else soup.get_text()

        # Steg C: Anropa Claude API för filtrering
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            prompt = f"""
            Här är en rå textlista över aktuella offentliga upphandlingar från e-Avrop:

            ---
            {raw_text[:14000]}
            ---

            Uppgift:
            1. Filtrera listan och behåll endast upphandlingar inom management, IT, organisation, rådgivning eller konsulttjänster.
            2. Presentera resultatet i en ren Markdown-tabell med följande kolumner:
               - Titel
               - Organisation/Myndighet
               - Sista anbudsdag
            3. Om inga relevanta upphandlingar hittas, skriv en kort förklaring.
            """

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_result = message.content[0].text
            
            # Steg D: Visa resultatet i Streamlit
            st.success("Analysen är klar!")
            st.markdown(analysis_result)

        except Exception as e:
            st.error(f"Ett fel uppstod vid anrop till Claude: {e}")
