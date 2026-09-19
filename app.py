import streamlit as st
import pandas as pd
import feedparser

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="PA Consulting - Upphandlingsbevakning",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsbevakning (Flera RSS-flöden)")
st.write("Samlad vy för alla dina bevakningsflöden från Mercell, e-Avrop och andra portaler.")

# 2. Sidomeny för hantering av RSS-länkar
st.sidebar.header("📡 RSS-Källor")
st.sidebar.write("Lägg in en RSS-länk per rad:")

# Standardlänkar (Ersätt/komplettera med din kollegas riktiga RSS-länkar)
default_urls = """https://www.kommersannons.se/rss/rss.aspx
https://ted.europa.eu/api/v2/rss/searches?q=defence"""

urls_input = st.sidebar.text_area(
    "RSS-Länkar:",
    value=default_urls,
    height=150
)

st.sidebar.divider()
st.sidebar.header("🔍 Sök & Filter")
search_term = st.sidebar.text_input("Sök i rubrik eller beskrivning:", "")

# 3. Funktion för att hämta och slå ihop flera RSS-flöden
@st.cache_data(ttl=600)
def fetch_all_rss(urls_list):
    all_items = []
    
    for url in urls_list:
        url = url.strip()
        if not url:
            continue
            
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.get("title", url.split("/")[2] if "//" in url else url)
            
            for entry in feed.entries:
                published = getattr(entry, "published", getattr(entry, "updated", "Ej angivet"))
                summary = getattr(entry, "summary", getattr(entry, "description", ""))
                
                all_items.append({
                    "Källa/Flöde": source_title,
                    "Publicerad": published,
                    "Titel": entry.title,
                    "Länk": entry.link,
                    "Beskrivning": summary
                })
        except Exception as e:
            st.sidebar.warning(f"Kunde inte läsa: {url[:30]}...")
            
    return pd.DataFrame(all_items)

# 4. Bearbeta och visa datan
urls = [u for u in urls_input.split("\n") if u.strip()]

if urls:
    df = fetch_all_rss(urls)
    
    if not df.empty:
        # Filtrera baserat på sökord
        if search_term:
            df = df[
                df["Titel"].str.contains(search_term, case=False, na=False) |
                df["Beskrivning"].str.contains(search_term, case=False, na=False) |
                df["Källa/Flöde"].str.contains(search_term, case=False, na=False)
            ]
        
        st.metric("Totalt antal upphandlingar i alla flöden", len(df))
        
        # Översiktstabell
        st.dataframe(
            df[["Källa/Flöde", "Publicerad", "Titel", "Länk"]],
            column_config={
                "Länk": st.column_config.LinkColumn("Öppna källa")
            },
            use_container_width=True
        )
        
        st.divider()
        
        # Detaljvy
        st.subheader("📋 Detaljerade notiser")
        for idx, row in df.iterrows():
            with st.expander(f"📌 [{row['Källa/Flöde']}] {row['Titel']}"):
                st.write(f"**Publicerad:** {row['Publicerad']}")
                st.write(f"**Beskrivning:** {row['Beskrivning']}")
                st.markdown(f"🔗 [Läs hela upphandlingen]({row['Länk']})")
    else:
        st.info("Inga upphandlingar hittades i de angivna RSS-flödena. Klistra in kollegans giltiga RSS-länkar i rutan till vänster.")
else:
    st.warning("Lägg till minst en RSS-länk i textrutan till vänster.")
