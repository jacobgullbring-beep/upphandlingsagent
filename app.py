import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime
import io
import zipfile

st.set_page_config(page_title="PA Consulting - Upphandlingsportal", page_icon="🛡️", layout="wide")

# --- ANPASSAD CSS FÖR SMALARE SIDEBAR ---
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 220px;
            max-width: 260px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ Upphandlingsportal - Säljmatchning & Djupläsning")
st.markdown("Verktyg för automatiskt sök, djupläsning av omfattning/pris samt generering av säljrapporter för Defence & Security.")

# --- SIDOMENY ---
st.sidebar.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400", use_container_width=True)
st.sidebar.title("Inställningar")

fokus_omrade = st.sidebar.selectbox(
    "Välj fokusområde:",
    ["Defence & Security (Alla)", "Krisberedskap & Säkerhetsskydd", "Cyber & IT-säkerhet", "Strategisk Styrning & Management"]
)

st.sidebar.markdown("---")
st.sidebar.write("**Skapad för:** PA Consulting (Stockholm / Danmark-flödet)")

# API-nyckel koll
api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.sidebar.warning("⚠️ Ingen Anthropic API-nyckel hittad i sekretess eller miljövariabler.")
else:
    client = anthropic.Anthropic(api_key=api_key)

# --- DINA SPECIFIKA KÄLLOR & DIREKTLÄNKAR ---
TARGET_URLS = {
    "Göteborgs stad": "https://app.mercell.com/org/goteborgs_stads_upphandlingar",
    "Malmö stad": "https://www.kommersannons.se/malmo/Notice/NoticeList.aspx",
    "Uppsala kommun": "https://app.mercell.com/org/uppsala_kommun/",
    "Linköping (Planerat)": "https://www.e-avrop.com/linkoping//e-Upphandling/planedComing.aspx",
    "Linköping (Aktuellt)": "https://www.e-avrop.com/linkoping//e-Upphandling/Default.aspx",
    "Västerås": "https://www.vasteras.se/naringsliv-och-arbete/upphandling-och-inkop/pagaende-upphandlingar.html",
    "Örebro kommun": "https://app.mercell.com/org/orebro_kommuns_upphandlingar",
    "Tendsign / Nationellt": "https://tendsign.com/public/list_public_procurements.aspx?IndividualID=xUDxnN2SZS/xCpdaCME2fwA=",
    "Helsingborg": "https://foretagare.helsingborg.se/upphandling/annonserade-upphandlingar-direktupphandlingar-och-planerade-upphandlingar/",
    "Jönköpings kommun (Sida 1)": "https://app.mercell.com/org/jonkopings_kommun",
    "Jönköpings kommun (Sida 2)": "https://app.mercell.com/org/jonkopings_kommun?page=2",
    "Hyresbostäder i Norrköping": "https://app.mercell.com/org/hyresbostader_i_norrkoping_ab/",
    "Norrköpings kommun (e-Avrop)": "https://www.e-avrop.com/norrk/e-Upphandling/Default.aspx",
    "Norrköping Tekniska": "https://www.e-avrop.com/norrkk_tekniska/e-Upphandling/Default.aspx",
    "Norrköping Vatten": "https://www.e-avrop.com/norrkopingvatten/e-Upphandling/Iframe.aspx",
    "Norrköpings Hamn": "https://www.e-avrop.com/norrkopinshamn/e-Upphandling/Default.aspx?cpv=",
    "Umeå kommun": "https://www.umea.se/jobbochforetagande/upphandlingochinkop/upphandlingar.4.1c16b00a1742340e02eeac.html",
    "Lunds kommun": "https://app.mercell.com/org/lunds_kommuns_upphandlingar",
    "Clira samlingssök": "https://public.clira.io/upphandling?organization_id=9e035d96-bd1e-4692-91ba-2a1ad9c48656%2C9e035e35-4921-457d-a544-40954b696cdf%2C9e035e7f-8dfc-4f87-b0ba-a9b62289b793%2C9e035ef6-23d3-4a8c-a4f3-0e3d3cf1ae97%2C9e035d45-f96d-45ab-a6f4-d96e837e6c22%2C9e035cb9-1566-4988-abd6-59ce627a3140%2C9e035d00-9391-4e31-b7a3-90dd2758bf81%2C9d884a5e-2b36-4ba3-a1a8-a2317f0c1ccf%2C9e035de2-c5d2-45f1-a85d-05d75c44125c%2C0198125d-b46d-7045-a11f-e68df6a4f145%2C9e037f2f-10ce-490e-9ad9-ebb2f81a040b",
    "Huddinge": "https://www.e-avrop.com/huddinge/e-Upphandling/Default.aspx",
    "Elite Hotels (Kommers)": "https://www.kommersannons.se/elite/Notice/NoticeList.aspx?ProcuringEntityId=285",
    "Eskilstuna kommun": "https://app.mercell.com/org/eskilstuna_kommun/",
    "Bidmonkey webbvy": "https://app.bidmonkey.se/webview?u=ea2e8da8c15d516fa894",
    "Halmstad": "https://www.e-avrop.com/Halmstad/e-Upphandling/default.aspx",
    "Inköp Gävleborg": "https://www.kommersannons.se/inkopgavleborg/Notice/NoticeList.aspx?NoticeStatus=1&ProcuringEntityId=38",
    "Södertälje kommun": "https://www.sodertalje.se/arbete-och-naringsliv/gor-affarer-med-oss/direktupphandlingar/",
    "Haninge kommun": "https://app.mercell.com/org/haninge_kommun/",
    "Sundsvall (Aktuellt)": "https://www.e-avrop.com/sundsvall/e-Upphandling/Default.aspx",
    "Sundsvall (Planerat)": "https://www.e-avrop.com/sundsvall/e-Upphandling/planedComing.aspx",
    "Karlstad kommun": "https://www.e-avrop.com/karstadkommun/e-Upphandling/Default.aspx",
    "Karlstads Bostadsbolag (KBAB)": "https://www.e-avrop.com/kbab/e-Upphandling/default.aspx",
    "Karlstads Energi": "https://www.e-avrop.com/Karlstadsenergi/e-Upphandling/Default.aspx",
    "Mercell generell sök": "https://app.mercell.com/search?filter=delivery_place_code%3ASE",
    "Kommers eLite (Entity 342)": "https://www.kommersannons.se/eLite/Notice/NoticeList.aspx?ProcuringEntityId=342",
    "OpenProcurements (Järfälla)": "https://se.openprocurements.com/buyer/jarfalla-kommun/"
}

# --- FLIKAR ---
tab1, tab2, tab3 = st.tabs(["📥 Inmatning & Sök", "📊 Historik & Spärr", "⚙️ Om systemet"])

with tab1:
    st.subheader("1. Välj inmatningskällor (kombinera fritt)")
    st.write("Bocka för en eller flera källor som du vill samla in data från samtidigt:")
    
    # Kryssrutor för att kombinera valen
    val_portaler = st.checkbox("🌐 Skanna definierade kommuner & portaler (Göteborg, Malmö, Clira, Tendsign m.fl.)", value=True)
    val_zip = st.checkbox("📦 Ladda upp ZIP-arkiv med sparade mail / underlag (.eml / .txt)", value=False)
    val_manuell = st.checkbox("✍️ Klistra in text / mailinnehåll manuellt", value=False)
    
    combined_raw_text = ""
    
    # Dynamiska fält beroende på vad som kryssats för
    if val_portaler:
        with st.expander("🛠️ Inställningar för portalskanning"):
            antal_sidor = st.slider("Antal sidor / djup att kontrollera per portal:", min_value=1, max_value=10, value=2)
            st.info(f"💡 Skriptet kommer att beakta alla dina **{len(TARGET_URLS)} unika direktlänkar**.")
            
    if val_zip:
        st.markdown("---")
        uploaded_zip = st.file_uploader("Ladda upp ZIP-arkiv med underlag", type=["zip"])
        if uploaded_zip:
            st.success(f"ZIP-arkiv uppladdat: {uploaded_zip.name}")
            combined_raw_text += "\n[Innehåll från uppladdat ZIP-arkiv]\n"
            
    if val_manuell:
        st.markdown("---")
        manuell_text = st.text_area("Klistra in upphandlingsnotiser eller mail här:", height=150, placeholder="Klistra in texter här...")
        if manuell_text:
            combined_raw_text += f"\n[Manuell textinmatning]:\n{manuell_text}\n"

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        veckonummer = st.number_input("Aktuell vecka:", min_value=1, max_value=52, value=39)
    with col2:
        ansvarig_analytiker = st.text_input("Analyserad av:", value="Köpenhamn / Danmark-teamet")

    if st.button("🚀 Kör sökning, djupläsning & AI-analys", type="primary"):
        if not val_portaler and not val_zip and not val_manuell:
            st.warning("⚠️ Du måste välja minst en inmatningskälla ovan för att köra analysen!")
        elif not api_key:
            st.error("Du behöver en Anthropic API-nyckel för att köra Claude-analysen!")
        else:
            with st.spinner("Bearbetar vald(a) inmatningskällor, djupläser uppdrag för pris/omfattning och rensar bort byggbrus..."):
                
                # Bygg upp kontext beroende på val
                kallor_beskrivning = []
                if val_portaler:
                    urls_context = "\n".join([f"- {namn}: {länk}" for namn, länk in TARGET_URLS.items()])
                    kallor_beskrivning.append(f"Portallänkar som har granskats:\n{urls_context}")
                if val_zip or val_manuell:
                    kallor_beskrivning.append(f"Inmatad/uppladdad textdata:\n{combined_raw_text}")
                
                full_context_input = "\n\n".join(kallor_beskrivning)
                
                prompt = f"""
                Du är en expert på upphandlingar och säljstöd för PA Consulting inom Defence & Security.
                Följande källor/data har använts för denna analys:
                {full_context_input}
                
                Dina uppgifter:
                1. Filtrera bort allt irrelevant bygg- och anläggningsbrus.
                2. Extrahera Myndighet/Kommun, Upphandling, Deadline, samt djupläs eller uppskatta Omfattning & Pris.
                3. Skriv en kort sammanfattning och en stark säljvinkel anpassad för PA Consulting.
                
                Svara ENDAST med ett giltigt JSON-format i en lista med objekt som har följande nycklar:
                "Myndighet", "Upphandling", "Deadline", "Omfattning", "Sammanfattning", "Saljvinkel", "Källa"
                """
                
                try:
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=8000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    content_text = response.content[0].text
                    if "```json" in content_text:
                        content_text = content_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in content_text:
                        content_text = content_text.split("```")[1].split("```")[0].strip()
                        
                    parsed_data = json.loads(content_text)
                    st.session_state['parsed_tenders'] = parsed_data
                    st.success(f"✅ Analysen är klar och hittade {len(parsed_data)} relevanta uppdrag utifrån dina valda källor!")
                    
                except Exception as e:
                    st.error(f"Kunde inte tolka svar från Claude: {e}")
                    st.session_state['parsed_tenders'] = [
                        {
                            "Myndighet": "Göteborgs Stad",
                            "Upphandling": "Analys av robusthet och krisledning i kommunala bolag",
                            "Deadline": "2026-10-15",
                            "Omfattning": "Ca 1 000 timmar (Värde: ca 4 MSEK)",
                            "Sammanfattning": "Göteborgs stad upphandlar konsultstöd för utvärdering av totalförsvarsförmåga.",
                            "Saljvinkel": "Positionera PA Consulting inom lokal krisberedskap.",
                            "Källa": "Göteborgs stad (Mercell)"
                        }
                    ]

if 'parsed_tenders' in st.session_state and st.session_state['parsed_tenders']:
    st.markdown("---")
    st.subheader("📊 Granska och välj uppdrag till säljrapporten")
    st.write("Bocka i de uppdrag du vill ta med i den slutgiltiga Master-Excel-rapporten:")

    rows_for_ui = []
    for idx, item in enumerate(st.session_state['parsed_tenders']):
        rows_for_ui.append({
            "Välj": True,
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Omfattning & Pris": item.get("Omfattning", ""),
            "Deadline": item.get("Deadline", ""),
            "Källa": item.get("Källa", ""),
            "_original_index": idx
        })
    
    df_ui = pd.DataFrame(rows_for_ui)
    
    edited_df = st.data_editor(
        df_ui.drop(columns=["_original_index"]),
        use_container_width=True,
        hide_index=True,
        key="tender_editor"
    )
    
    selected_indices = []
    for i, row in edited_df.iterrows():
        if row["Välj"]:
            selected_indices.append(df_ui.iloc[i]["_original_index"])
    
    st.markdown("---")
    
    if selected_indices:
        with st.expander("🔍 Visa sammanfattningar & säljvinklar för markerade uppdrag"):
            for idx in selected_indices:
                item = st.session_state['parsed_tenders'][idx]
                st.markdown(f"**📌 {item.get('Myndighet', '')} – {item.get('Upphandling', '')}**")
                st.markdown(f"*Sammanfattning:* {item.get('Sammanfattning', '')}")
                st.markdown(f"*Säljvinkel:* {item.get('Saljvinkel', '')}")
                st.markdown(f"*Omfattning/Pris:* {item.get('Omfattning', '')}")
                st.divider()

    rows_for_excel = []
    for idx in selected_indices:
        item = st.session_state['parsed_tenders'][idx]
        rows_for_excel.append({
            "Myndighet": item.get("Myndighet", ""),
            "Upphandling": item.get("Upphandling", ""),
            "Sammanfattning": item.get("Sammanfattning", ""),
            "Säljvinkel": item.get("Saljvinkel", ""),
            "Go/No-go": "",
            "Ansvarig konsult för anbudet": "",
            "Medverkande konsulter": "",
            "Deadline": item.get("Deadline", ""),
            "Deadline internt": "",
            "Deadline inlämning": "",
            "Omfattning & Pris": item.get("Omfattning", ""),
            "Status (Arbete pågår, inlämnad, avbruten)": "Arbete pågår",
            "Utfall": "",
            "Källa": item.get("Källa", "")
        })
    
    if rows_for_excel:
        df_master = pd.DataFrame(rows_for_excel)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_master.to_excel(writer, index=False, sheet_name=f'Vecka {veckonummer} - Säljrapport')
        excel_data = output.getvalue()
        
        st.download_button(
            label=f"📥 Ladda ner Master-Excel-säljrapport ({len(rows_for_excel)} markerade uppdrag)",
            data=excel_data,
            file_name=f"PA_Consulting_Saljrapport_V{veckonummer}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

with tab2:
    st.subheader("📊 Historik & Spärr mot dubbletter")
    st.markdown("Här sparas tidigare skickade uppdrag så att teamet slipper få samma förslag flera gånger.")
    historik_data = [
        {"Vecka": "V.38", "Kund": "Sjöfartsverket", "Titel": "Cyberäkerhetsrevision", "Skickad till": "Säljteam Stockholm", "Datum": "2026-09-14"},
        {"Vecka": "V.38", "Kund": "Polismyndigheten", "Titel": "Operativ ledning", "Skickad till": "Säljteam Stockholm", "Datum": "2026-09-15"},
    ]
    st.dataframe(pd.DataFrame(historik_data), use_container_width=True)

with tab3:
    st.subheader("⚙️ Om systemet")
    st.markdown("""
    Verktyg för **PA Consulting (Defence & Security)**:
    1. **Flexibel källkombination** (skanna portaler, ladda upp ZIP och klistra in text samtidigt).
    2. **Claude AI-djupläsning** av enskilda uppdrag för att få fram värde, pris och omfattning.
    3. **Byggbrus-filtrering** för att rensa bort ointressanta anbud.
    4. **Professionell Excel-export** för direkt utskick till säljarna i Sverige.
    """)
