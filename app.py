import streamlit as st
import pandas as pd
import feedparser

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="PA Consulting - Upphandlingsbevakning",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsbevakning via RSS")
st.write("Automatisk inläsning av de senaste tilldelningarna och upphandlingarna från dina bevakningsflöden.")

# 2. Sidomeny för RSS-länk och Filter
st.sidebar.header("📡 RSS-Inställningar")

# Exempel-RSS eller skriv in egen
rss_url = st.sidebar.text_input(
    "Klistra in RSS-länk från Mercell/e-Avrop:",
    value="https://ted.europa.eu/api/v2/rss/searches?q=defence"  # Exempelflöde för försvarsupphandlingar i EU
)

st.sidebar.divider()
st.sidebar.header("🔍 Sök & Filter")
search_term = st.sidebar.text_input("Sök i rubrik eller beskrivning:", "")

# 3. Funktion för att hämta och tolka RSS-flödet
@st.cache_data(ttl=900) # Cachar datan i 15 minuter så det går snabbt
def load_rss_data(url):
    feed = feedparser.parse(url)
    items = []
    
    for entry in feed.entries:
        # Hämtar publiceringsdatum, titel, länk och sammanfattning/beskrivning
        published = getattr(entry, "published", getattr(entry, "updated", "Ej angivet"))
        summary = getattr(entry, "summary", getattr(entry, "description", ""))
        
        items.append({
            "Publicerad": published,
            "Titel": entry.title,
            "Länk": entry.link,
            "Beskrivning": summary
        })
    return pd.DataFrame(items)

# 4. Hämta och visa datan
if rss_url:
    try:
        df = load_rss_data(rss_url)
        
        if not df.empty:
            # Applicera fritextfilter om användaren söker
            if search_term:
                df = df[
                    df["Titel"].str.contains(search_term, case=False, na=False) |
                    df["Beskrivning"].str.contains(search_term, case=False, na=False)
                ]
            
            st.metric("Antal hittade upphandlingar i flödet", len(df))
            
            # Huvudtabell med klickbara länkar
            st.dataframe(
                df[["Publicerad", "Titel", "Länk"]],
                column_config={
                    "Länk": st.column_config.LinkColumn("Öppna källa")
                },
                use_container_width=True
            )
            
            st.divider()
            
            # Detaljvy för varje kort
            st.subheader("📋 Detaljerade notiser")
            for idx, row in df.iterrows():
                with st.expander(f"📌 {row['Titel']}"):
                    st.write(f"**Publicerad:** {row['Publicerad']}")
                    st.write(f"**Beskrivning:** {row['Beskrivning']}")
                    st.markdown(f"🔗 [Läs hela upphandlingen hos källan]({row['Länk']})")
        else:
            st.warning("Hittade inga poster i detta RSS-flöde. Kontrollera länken.")
            
    except Exception as e:
        st.error(f"Kunde inte läsa av RSS-flödet. Felmeddelande: {e}")
else:
    st.info("Klistra in en RSS-länk i sidomenyn till vänster för att läsa in upphandlingar.")
