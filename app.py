import streamlit as st
import pandas as pd
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="GTM Defence & Security - Upphandlingsbevakning", layout="wide")

st.title("🛡️ GTM Upphandlingsbevakning & Säljinsikter")
st.write("Automatisk sammanställning av klara offentliga upphandlingar med fokuserade sälljananalyser.")

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades. Lägg till ANTHROPIC_API_KEY i dina Secrets/miljövariabler.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Filter i sidomenyn
st.sidebar.header("🔍 Filter")
kategori_filter = st.sidebar.radio(
    "Välj fokusområde:",
    ["Alla upphandlingar", "Endast Försvar & Säkerhet (FMV, MSB, Polisen m.fl.)", "Övrig offentlig sektor"]
)

def fetch_tender_data():
    return [
        {
            "Källa": "FMV",
            "Sektor": "Försvar & Säkerhet",
            "Titel": "Ramavtal IT-konsulttjänster inom Cybersäkerhet & Ledningssystem",
            "Myndighet": "Försvarets materielverk (FMV)",
            "Beskrivning": "Tilldelning av ramavtal avseende specialiststöd inom cybersäkerhet, arkitektur och ledningssystem. Total ramavtalsvolym beräknas till 45 MSEK över 4 år."
        },
        {
            "Källa": "e-Avrop",
            "Sektor": "Övrig offentlig sektor",
            "Titel": "Projektledning och Förändringsledning för Verksamhetsutveckling",
            "Myndighet": "Järfälla Kommun",
            "Beskrivning": "Upphandling av konsulttjänster för stöd vid införande av nytt digitalt ärendehanteringssystem och förändringsledning."
        },
        {
            "Källa": "Mercell",
            "Sektor": "Försvar & Säkerhet",
            "Titel": "Rådgivning och Strateger inom Totalförsvar & Beredskap",
            "Myndighet": "MSB (Myndigheten för samhällsskydd och beredskap)",
            "Beskrivning": "Avtal tecknat för strategisk rådgivning, krisberedskap och programledning under perioden 2026–2028."
        }
    ]

if st.button("🚀 Hämta & Analysera Senaste Tilldelningarna", type="primary"):
    with st.spinner("Hämtar upphandlingar och analyserar säljmöjligheter med Claude..."):
        all_tenders = fetch_tender_data()
        
        # Filtrering utifrån användarens val
        if kategori_filter == "Endast Försvar & Säkerhet (FMV, MSB, Polisen m.fl.)":
            filtered_tenders = [t for t in all_tenders if t["Sektor"] == "Försvar & Säkerhet"]
        elif kategori_filter == "Övrig offentlig sektor":
            filtered_tenders = [t for t in all_tenders if t["Sektor"] == "Övrig offentlig sektor"]
        else:
            filtered_tenders = all_tenders
        
        results = []
        for item in filtered_tenders:
            prompt = f"""
            Du är en expert på Business Development / Go-To-Market (GTM) för konsulter inom offentlig sektor, med särskilt fokus på Defence & Security samt management/IT-rådgivning.
            
            Analysera följande nyligen tilldelade upphandling:
            Myndighet: {item['Myndighet']}
            Titel: {item['Titel']}
            Beskrivning: {item['Beskrivning']}
            
            Ge korta och tydliga svar på följande punkter:
            1. **Vinnare / Tilldelat företag:** (Identifiera eller ange "Ej specat i korttext")
            2. **Avtalsvärde & Period:**
            3. **GTM & Säljvinkel för PA Consulting:** 
               - Hur kan GTM-teamet agera på detta? (T.ex. kontakta myndigheten för tilläggstjänster/förändringsledning, eller kontakta den vinnande leverantören som underleverantör/partner inom specialkompetens).
            """
            
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=600,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                results.append({
                    "Sektor": item["Sektor"],
                    "Myndighet": item["Myndighet"],
                    "Upphandling": item["Titel"],
                    "Claudes GTM-Analys": response.content[0].text
                })
            except Exception as e:
                st.error(f"Ett fel uppstod vid anrop till Claude för {item['Titel']}: {e}")
            
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ Analys klar! Hittade {len(df)} relevanta upphandlingar.")
            
            for idx, row in df.iterrows():
                with st.expander(f"📌 [{row['Sektor']}] {row['Myndighet']} – {row['Upphandling']}"):
                    st.markdown(row["Claudes GTM-Analys"])
