import os
import streamlit as st
import pandas as pd
from anthropic import Anthropic

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="Upphandlingsagent",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsagent & Analys")
st.write("Hämtar och analyserar senaste tilldelade upphandlingar med Claude.")

# 2. Hämta API-nyckel och Workspace ID från secrets eller miljövariabler
api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
workspace_id = st.secrets.get("ANTHROPIC_WORKSPACE_ID") or os.environ.get("ANTHROPIC_WORKSPACE_ID")

if not api_key:
    st.error("❌ Hittade ingen ANTHROPIC_API_KEY. Lägg till den i Streamlit Secrets eller .env-filen.")
    st.stop()

# Skapa headers för workspace-id om det finns
custom_headers = {}
if workspace_id:
    custom_headers["anthropic-workspace-id"] = workspace_id

# Initialisera Anthropic-klienten
client = Anthropic(
    api_key=api_key,
    default_headers=custom_headers if custom_headers else None
)

# 3. Upphandlingsdata
def fetch_tender_data():
    return [
        {
            "id": "UPP-2026-001",
            "titel": "Ramavtal IT-konsulttjänster inom Cybersäkerhet & Ledningssystem",
            "myndighet": "Försvarets materielverk (FMV)",
            "vinnare": "CyberTech Solutions AB",
            "värde": "15 000 000 SEK",
            "beskrivning": "Avtalet omfattar expertstöd inom cybersäkerhet, informationssäkerhet samt granskning av säkra kommunikationssystem under 2 år."
        },
        {
            "id": "UPP-2026-002",
            "titel": "Projektledning och Förändringsledning för Verksamhetsutveckling",
            "myndighet": "Region Stockholm",
            "vinnare": "Consulting Group Nordic AB",
            "värde": "8 500 000 SEK",
            "beskrivning": "Konsulttjänster för stöd vid digital transformation och implementering av nya arbetssätt inom hälso- och sjukvården."
        },
        {
            "id": "UPP-2026-003",
            "titel": "Rådgivning och Strateger inom Totalförsvar & Beredskap",
            "myndighet": "Myndigheten för samhällsskydd och beredskap (MSB)",
            "vinnare": "Defence Consulting Nordics AB",
            "värde": "12 000 000 SEK",
            "beskrivning": "Strategisk rådgivning och utredningsstöd avseende totalförsvarets uppbyggnad och försörjningsberedskap."
        }
    ]

# 4. Analysera upphandling med Claude
def analyze_tender(tender):
    prompt = f"""
    Du är en expert på offentlig upphandling och affärsanalys. 
    Analysera följande tilldelade upphandling och ge en kortfattad, strukturerad summering:
    
    Titel: {tender['titel']}
    Myndighet: {tender['myndighet']}
    Vinnare: {tender['vinnare']}
    Värde: {tender['värde']}
    Beskrivning: {tender['beskrivning']}

    Formatera svaret i Markdown med följande rubriker:
    - **Sammandrag:** (Vad handlar avtalet om i korthet?)
    - **Möjliga underleverantörsmöjligheter:** (Finns det chans för mindre bolag/underkonsulter att leverera?)
    - **Viktiga insikter:** (Vad bör man tänka på inför framtida liknande upphandlingar?)
    """
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# 5. Körknapp och visualisering
if st.button("🚀 Hämta & Analysera Senaste Tilldelningarna", type="primary"):
    with st.spinner("Hämtar data och analyserar med Claude..."):
        tenders = fetch_tender_data()
        
        st.subheader("📋 Senaste Tilldelade Upphandlingar")
        df = pd.DataFrame(tenders)[["titel", "myndighet", "vinnare", "värde"]]
        df.columns = ["Titel", "Köpare / Myndighet", "Vinnande Leverantör", "Kontraktsvärde"]
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("🤖 AI-Analys av Tilldelningarna")
        
        for tender in tenders:
            with st.expander(f"🔍 Analys: {tender['titel']} ({tender['myndighet']})", expanded=True):
                try:
                    analysis = analyze_tender(tender)
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"Ett fel uppstod vid anrop till Claude för {tender['titel']}: {e}")
