import streamlit as st
import pandas as pd
import feedparser

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="PA Consulting - Upphandlingsbevakning",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsbevakning med Smarta Filter")
st.write("Samlad vy över alla dina RSS-flöden med filtrering på myndighetstyp och upphandlingsstatus.")

# 2. Sidomeny för RSS-länkar och Filter
st.sidebar.header("📡 RSS-Källor")
st.sidebar.write("Lägg in RSS-länkar (en per rad):")

default_urls = """https://www.kommersannons.se/rss/rss.aspx
https://ted.europa.eu/api/v2/rss/searches?q=defence"""

urls_input = st.sidebar.text_area(
    "RSS-Länkar:",
    value=default_urls,
    height=120
)

st.sidebar.divider()
st.sidebar.header("🔍 Smarta Filter")

# Fritextsökning
search_term = st.sidebar.text_input("Sök nyckelord:", "")

# Filter för Myndighetstyp
org_filter = st.sidebar.selectbox(
    "Filtrera på Myndighetstyp:",
    ["Alla myndigheter", "Kommuner", "Regioner", "Statliga myndigheter & Försvar"]
)

# Filter för Upphandlingsstatus
status_filter = st.sidebar.selectbox(
    "Filtrera på Status:",
    ["Alla upphandlingar", "Endast Klara / Tilldelade avtal", "Pågående upphandlingar"]
)

# 3. Funktion för att hämta RSS-data
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
        except Exception:
            pass
            
    return pd.DataFrame(all_items)

# 4. Bearbeta och filtrera datan
urls = [u for u in urls_input.split("\n") if u.strip()]

if urls:
    df = fetch_all_rss(urls)
    
    if not df.empty:
        # Skapa söksområde i gemensam textkolumn
        full_text = df["Titel"].fillna("") + " " + df["Beskrivning"].fillna("")
        
        # 1. Fritextfilter
        if search_term:
            df = df[full_text.str.contains(search_term, case=False, na=False)]
            full_text = df["Titel"].fillna("") + " " + df["Beskrivning"].fillna("")

        # 2. Myndighetsfilter
        if org_filter == "Kommuner":
            df = df[full_text.str.contains("kommun", case=False, na=False)]
        elif org_filter == "Regioner":
            df = df[full_text.str.contains("region|landsting", case=False, na=False)]
        elif org_filter == "Statliga myndigheter & Försvar":
            df = df[full_text.str.contains("myndighet|verk|fmv|msb|försvarsmakten|polisen|styrelse", case=False, na=False)]

        # 3. Statusfilter
        full_text_status = df["Titel"].fillna("") + " " + df["Beskrivning"].fillna("")
        award_keywords = "tilldelning|tilldelat|vinnare|kontrakt|avtal tecknat|avslutad|tilldelningsbeslut"
        
        if status_filter == "Endast Klara / Tilldelade avtal":
            df = df[full_text_status.str.contains(award_keywords, case=False, na=False)]
        elif status_filter == "Pågående upphandlingar":
            df = df[~full_text_status.str.contains(award_keywords, case=False, na=False)]

        st.metric("Antal matchande upphandlingar", len(df))
        
        # Tabellvy
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
        st.info("Inga upphandlingar hittades i de angivna RSS-flödena.")
else:
    st.warning("Lägg till minst en RSS-länk i rutan till vänster.")
