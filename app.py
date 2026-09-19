import streamlit as st
import pandas as pd
import feedparser
import anthropic

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="PA Consulting - Upphandlingsbevakning",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsbevakning & AI-analys via RSS")
st.write("Hämtar automatiskt upphandlingar från ditt RSS-flöde och analyserar dem med Claude.")

# 2. Hämta hemligheter från Streamlit Secrets
api_key = st.secrets.get("ANTHROPIC_API_KEY")
workspace_id = st.secrets.get("ANTHROPIC_WORKSPACE_ID")

if not api_key:
    st.error("❌ Saknar ANTHROPIC_API_KEY i Streamlit Secrets.")
    st.stop()

# Initiera Anthropic-klienten
custom_headers = {}
if workspace_id:
    custom_headers["anthropic-workspace-id"] = workspace_id

client = anthropic.Anthropic(
    api_key=api_key,
    default_headers=custom_headers if custom_headers else None
)

# 3. Sidomeny: RSS-länk och Sökfilter
st.sidebar.header("📡 RSS-Inställningar")
rss_url = st.sidebar.text_input(
    "Klistra in RSS-länk från Mercell/e-Avrop:",
    value="https://ted.europa.eu/api/v2/rss/searches?q=defence"  # Exempelflöde
)

st.sidebar.divider()
st.sidebar.header("🔍 Sök & Filter")
search_term = st.sidebar.text_input("Sök nyckelord i flödet:", "")

# 4. Funktion för att hämta och tolka RSS-flödet
@st.cache_data(ttl=900)
def load_rss_data(url):
    feed = feedparser.parse(url)
    items = []
    
    for entry in feed.entries:
        published = getattr(entry, "published", getattr(entry, "updated", "Ej angivet"))
        summary = getattr(entry, "summary", getattr(entry, "description", ""))
        
        items.append({
            "Publicerad": published,
            "Titel": entry.title,
            "Länk": entry.link,
            "Beskrivning": summary
        })
    return pd.DataFrame(items)

# 5. Hämta datan
if rss_url:
    try:
        df = load_rss_data(rss_url)
        
        if not df.empty:
            # Fritextfilter
            if search_term:
                df = df[
                    df["Titel"].str.contains(search_term, case=False, na=False) |
                    df["Beskrivning"].str.contains(search_term, case=False, na=False)
                ]
            
            st.metric("Antal hittade upphandlingar i flödet", len(df))
            
            # Huvudtabell med länkar
            st.dataframe(
                df[["Publicerad", "Titel", "Länk"]],
                column_config={
                    "Länk": st.column_config.LinkColumn("Källänk")
                },
                use_container_width=True
            )
            
            st.divider()
            
            # AI-analysknapp
            if st.button("🚀 Kör AI-analys på flödet med Claude", type="primary"):
                with st.spinner("Analyserar upphandlingar med Claude Sonnet 5..."):
                    results = []
                    
                    # Vi analyserar upp till de 5 senaste för att inte bränna tokens i onödan
                    for idx, row in df.head(5).iterrows():
                        prompt = f"""Följ instruktionerna exakt och svara enbart med den begärda analysen. Inled inte med några artighetsfraser eller hälsningar.

Analysera följande tilldelade offentliga upphandling ur ett sälj- och GTM-perspektiv (Go-To-Market) för konsultbolag:
- Titel: {row['Titel']}
- Beskrivning: {row['Beskrivning']}

Formatera ditt svar i Markdown med följande tre punkter:
1. **Sammandrag:** Kort sammanfattning av vad avtalet gäller.
2. **Underleverantörsmöjligheter:** Finns det öppningar för partners eller underkonsulter?
3. **GTM-rekommendation:** Vad bör säljteamet fokusera på vid nästa liknande tillfälle?
"""
                        try:
                            response = client.messages.create(
                                model="claude-sonnet-5",
                                max_tokens=800,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            analysis = response.content[0].text
                        except Exception as e:
                            analysis = f"Kunde inte generera analys: {e}"
                        
                        results.append({
                            "Titel": row["Titel"],
                            "Länk": row["Länk"],
                            "Analys": analysis
                        })
                    
                    st.success("✅ AI-analysen är klar!")
                    
                    st.subheader("📋 GTM-Analys av senaste upphandlingarna")
                    for item in results:
                        with st.expander(f"📌 {item['Titel']}"):
                            st.markdown(item["Analys"])
                            st.markdown(f"🔗 [Öppna källan]({item['Länk']})")
        else:
            st.warning("Hittade inga poster i detta RSS-flöde. Kontrollera länken.")
            
    except Exception as e:
        st.error(f"Kunde inte läsa av RSS-flödet. Felmeddelande: {e}")
else:
    st.info("Klistra in en RSS-länk i sidomenyn till vänster för att komma igång.")
