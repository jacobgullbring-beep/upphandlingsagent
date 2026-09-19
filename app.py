import streamlit as st
import pandas as pd

# 1. Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="PA Consulting - Upphandlingsbevakning",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Upphandlingsbevakning & Källportal")
st.write("Sök, filtrera och bevaka offentliga tilldelningar och upphandlingar.")

# 2. Datakälla för upphandlingar (med direktlänkar till källan)
def fetch_tender_data():
    return [
        {
            "Datum": "2026-09-18",
            "Källa": "FMV",
            "Sektor": "Försvar & Säkerhet",
            "Köpare / Myndighet": "Försvarets materielverk (FMV)",
            "Titel": "Ramavtal IT-konsulttjänster inom Cybersäkerhet & Ledningssystem",
            "Vinnande Leverantör": "CyberTech Solutions AB",
            "Kontraktsvärde": "15 000 000 SEK",
            "Länk": "https://www.fmv.se/upphandlingar/",
            "Beskrivning": "Avtalet omfattar expertstöd inom cybersäkerhet, informationssäkerhet samt granskning av säkra kommunikationssystem under 2 år."
        },
        {
            "Datum": "2026-09-17",
            "Källa": "e-Avrop",
            "Sektor": "Övrig offentlig sektor",
            "Köpare / Myndighet": "Region Stockholm",
            "Titel": "Projektledning och Förändringsledning för Verksamhetsutveckling",
            "Vinnande Leverantör": "Consulting Group Nordic AB",
            "Kontraktsvärde": "8 500 000 SEK",
            "Länk": "https://www.e-avrop.com/",
            "Beskrivning": "Konsulttjänster för stöd vid digital transformation och implementering av nya arbetssätt inom hälso- och sjukvården."
        },
        {
            "Datum": "2026-09-15",
            "Källa": "Mercell",
            "Sektor": "Försvar & Säkerhet",
            "Köpare / Myndighet": "MSB (Myndigheten för samhällsskydd och beredskap)",
            "Titel": "Rådgivning och Strateger inom Totalförsvar & Beredskap",
            "Vinnande Leverantör": "Defence Consulting Nordics AB",
            "Kontraktsvärde": "12 000 000 SEK",
            "Länk": "https://www.mercell.com/sv-se/upphandlingar.aspx",
            "Beskrivning": "Strategisk rådgivning och utredningsstöd avseende totalförsvarets uppbyggnad och försörjningsberedskap."
        }
    ]

# Hämta data
tenders = fetch_tender_data()
df = pd.DataFrame(tenders)

# 3. Sidomeny: Direktlänkar till portalerna
st.sidebar.header("🌐 Direktlänkar till Portaler")
st.sidebar.markdown("""
* 🛡️ [FMV Upphandlingar](https://www.fmv.se/upphandlingar/)
* 📦 [e-Avrop](https://www.e-avrop.com/)
* 📊 [Mercell Sverige](https://www.mercell.com/sv-se/upphandlingar.aspx)
* 🇪🇺 [TED (Tenders Electronic Daily)](https://ted.europa.eu/)
* 🏛️ [Kommers Annons](https://www.kommersannons.se/)
""")

st.sidebar.divider()
st.sidebar.header("🔍 Sök & Filter")

# Fritextsökning
search_term = st.sidebar.text_input("Sök nyckelord (t.ex. myndighet, tjänst eller vinnare):", "")

# Sektorfilter
sektor_options = ["Alla sektorer"] + list(df["Sektor"].unique())
selected_sektor = st.sidebar.selectbox("Välj Sektor:", sektor_options)

# Källfilter
kalla_options = ["Alla källor"] + list(df["Källa"].unique())
selected_kalla = st.sidebar.selectbox("Välj Källa:", kalla_options)

# 4. Applicera filter
filtered_df = df.copy()

if selected_sektor != "Alla sektorer":
    filtered_df = filtered_df[filtered_df["Sektor"] == selected_sektor]

if selected_kalla != "Alla källor":
    filtered_df = filtered_df[filtered_df["Källa"] == selected_kalla]

if search_term:
    filtered_df = filtered_df[
        filtered_df["Titel"].str.contains(search_term, case=False, na=False) |
        filtered_df["Köpare / Myndighet"].str.contains(search_term, case=False, na=False) |
        filtered_df["Vinnande Leverantör"].str.contains(search_term, case=False, na=False) |
        filtered_df["Beskrivning"].str.contains(search_term, case=False, na=False)
    ]

# 5. Visa resultat
st.metric("Antal träffar", len(filtered_df))

# Huvudtabell med länkar
st.dataframe(
    filtered_df[["Datum", "Källa", "Sektor", "Köpare / Myndighet", "Titel", "Vinnande Leverantör", "Kontraktsvärde", "Länk"]],
    column_config={
        "Länk": st.column_config.LinkColumn("Källänk")
    },
    use_container_width=True
)

st.divider()

# Detaljvy för varje upphandling
st.subheader("📋 Detaljer om valda upphandlingar")
for idx, row in filtered_df.iterrows():
    with st.expander(f"📌 {row['Köpare / Myndighet']} – {row['Titel']}"):
        st.write(f"**Datum:** {row['Datum']}")
        st.write(f"**Källa:** {row['Källa']} ({row['Sektor']})")
        st.write(f"**Vinnande leverantör:** {row['Vinnande Leverantör']}")
        st.write(f"**Kontraktsvärde:** {row['Kontraktsvärde']}")
        st.write(f"**Beskrivning:** {row['Beskrivning']}")
        st.markdown(f"🔗 [Öppna upphandlingen hos källan ({row['Källa']})]({row['Länk']})")
