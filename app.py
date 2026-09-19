import streamlit as st
import requests
from bs4 import BeautifulSoup
import anthropic
import pandas as pd
import json

# 1. Sidkonfiguration
st.set_page_config(
    page_title="GTM Defence & Security - Upphandlingsagent",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ GTM Upphandlingsbevakning & Säljinsikter")
st.write("Hämtar aktuella upphandlingar från e-Avrop och analyserar säljmöjligheter med Claude.")

# 2. Hämta API-nyckel från Streamlit Secrets
api_key = st.secrets.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("⚠️ Ingen `ANTHROPIC_API_KEY` hittades i Streamlit Secrets. Gå till Settings -> Secrets och lägg till din nyckel.")
    st.stop()

# 3. Filter i sidomenyn
st.sidebar.header("🔍 Filter")
kategori_filter = st.sidebar.radio(
    "Välj fokusområde:",
    ["Alla upphandlingar", "Endast Försvar & Säkerhet", "Övrig offentlig sektor"]
)

# 4. Knapp för att starta analysen
if st.button("Hämta & Analysera Upphandlingar", type="primary"):
    with st.spinner("Hämtar data från e-Avrop och analyserar med Claude..."):
        
        url = "https://www.e-avrop.com/UpphandlingDefault.aspx"
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.e-avrop.com/"
        }
        
        try:
            session.get("https://www.e-avrop.com/", headers=headers, timeout=15)
            response = session.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                st.error(f"Kunde inte hämta sidan från e-Avrop. Statuskod: {response.status_code}")
                st.stop()
        except Exception as e:
            st.error(f"Ett nätverksfel uppstod vid anrop till e-Avrop: {e}")
            st.stop()

        # Extrahera texten från tabellen
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        
        raw_text_parts = []
        for table in tables:
            raw_text_parts.append(table.get_text(separator="\n", strip=True))
            
        raw_text = "\n\n".join(raw_text_parts) if raw_text_parts else soup.get_text(separator="\n", strip=True)
        
        if not raw_text.strip():
            st.warning("Hittade ingen text på sidan. e-Avrop kan ha ändrat struktur.")
            st.stop()

        # Skapa en enklare struktur för datan
        tender_data = [{
            "källa": "e-Avrop",
            "innehåll": raw_text[:12000]
        }]
        
        df = pd.DataFrame(tender_data)
        data_text = json.dumps(df.to_dict(orient="records"), ensure_ascii=False)

        # Anropa Claude API för filtrering och analys
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            prompt = f"""
            Du är en expert på Business Development / Go-To-Market (GTM) för konsulter inom offentlig sektor, med särskilt fokus på Defence & Security samt management/IT-rådgivning (som PA Consulting).
            
            Här är rådata hämtad från e-Avrop:
            {data_text}

            Uppgift:
            1. Analysera datan och extrahera relevanta offentliga upphandlingar inom management, IT, organisation, rådgivning eller försvar/säkerhet.
            2. Presentera resultatet i en ren Markdown-tabell med följande kolumner:
               - Myndighet / Organisation
               - Titel / Uppdrag
               - Sista anbudsdag
               - GTM-rekommendation (kort säljvinkel)
            3. Om inga relevanta upphandlingar hittas i texten, skriv en kort förklaring baserat på vad som fanns tillgängligt.
            """

            message = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            answer_text = "".join([block.text for block in message.content if hasattr(block, "text")])
            
            # Visa resultatet i Streamlit
            st.success("Analysen är klar!")
            st.markdown(answer_text)

            # Expander för rådata
            with st.expander("Visa rådata från hämtad sida"):
                st.text(raw_text[:4000])

        except Exception as e:
            st.error(f"Ett fel uppstod vid anrop till Claude: {e}")
