import streamlit as st
import pandas as pd
import anthropic
import os
import json
from datetime import datetime
import io

st.set_page_config(page_title="GTM E-postbevakning", page_icon="🏛️", layout="wide")

st.title("🏛️ GTM Säljbevakning & Måndagsunderlag")
st.write("Analysera upphandlingsmejl, välj Go/No-go och ladda ner en renodlad Excel-fil med enbart era Go-affärer.")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Inmatning av mejl
email_input = st.text_area("Klistra in text från dina inkkommande upphandlingsmejl:", height=150)

if st.button("🚀 Kör AI-analys", type="primary", use_container_width=True):
    if not email_input.strip():
        st.warning("Klistra in lite text först!")
    else:
        prompt = f"""
        Extrahera alla upphandlingar från följande e-postmeddelanden. 
        Svara ENDAST med en giltig JSON-lista utan markdown-backticks.
        Varje objekt måste ha exakt dessa nycklar:
        - "Myndighet": Köpare/Region/Kommun
        - "Upphandling": Titel
        - "Deadline": Datum eller "Ej angivet"
        - "Omfattning": Omfattning i timmar/pengar eller "Ej angivet"
        - "Sammanfattning": Kort sammanfattning av upphandlingen
        - "Saljvinkel": Konkret rekommendation på hur ett konsultteam bör positionera sig

        Text:
        {email_input}
        """
        
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
            clean_json = raw_output.strip()
            if "```json" in clean_json: clean_json = clean_json.split("```json")[1]
            if "```" in clean_json: clean_json = clean_json.split("```")[0]
            
            start_idx = clean_json.find("[")
            end_idx = clean_json.rfind("]")
            
            if start_idx != -1 and end_idx != -1:
                parsed_data = json.loads(clean_json[start_idx:end_idx+1])
                
                rows = []
                for item in parsed_data:
                    rows.append({
                        "Go/No-go": "Ej satt",
                        "Myndighet": item.get("Myndighet", ""),
                        "Upphandling": item.get("Upphandling", ""),
                        "Deadline": item.get("Deadline", ""),
                        "Omfattning": item.get("Omfattning", ""),
                        "Sammanfattning": item.get("Sammanfattning", ""),
                        "Saljvinkel": item.get("Saljvinkel", ""),
                        "Ansvarig konsult": "",
                        "Status": "Arbete pågår"
                    })
                
                st.session_state['df_editable'] = pd.DataFrame(rows)
                st.success(f"✅ Extraherade {len(rows)} uppdrag!")
            else:
                st.error("Kunde inte tolka JSON-svaret.")
        except Exception as e:
            st.error(f"Fel vid anrop: {e}")

# Om vi har data i sessionen visar vi tabellen och detaljvyn
if 'df_editable' in st.session_state:
    st.markdown("---")
    st.subheader("📋 Översikt och Beslut")
    st.write("Sätt **Go** på de uppdrag ni vill gå vidare med. *(Klicka på en rad i tabellen för att se sammanfattning och säljvinkel längre ner)*.")

    # Interaktiv tabell (utan extra kryssrutor, renodlad grid)
    edited_df = st.data_editor(
        st.session_state['df_editable'],
        column_config={
            "Go/No-go": st.column_config.SelectboxColumn(
                "Go/No-go",
                help="Välj Go för att ta med i måndagsunderlaget",
                options=["Go", "No-go", "Ej satt"],
                required=True
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Arbete pågår", "Inlämnad", "Avbruten"],
                required=True
            )
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="data_editor_view"
    )

    # --- DETALJVY FÖR DEN RAD MAN KLICKAR PÅ ---
    st.markdown("---")
    st.subheader("🔍 Detaljerad information för vald rad")
    
    # Hämtar vilken rad användaren markerat i tabellen
    selection = st.session_state.get("data_editor_view", {})
    selected_rows = selection.get("edited_rows", {})
    
    # Vi kollar om användaren har klickat på/markerat någon specifik rad, 
    # annars visar vi den första raden som standard så att rutan inte är tom.
    target_idx = 0
    if selected_rows:
        # Ta den senaste raden som ändrats eller klickats på
        target_idx = list(selected_rows.keys())[0]
    elif len(edited_df) > 0:
        target_idx = 0

    if len(edited_df) > 0 and target_idx < len(edited_df):
        current_row = edited_df.iloc[target_idx]
        
        with st.container(border=True):
            st.markdown(f"### 📌 {current_row['Myndighet']} – {current_row['Upphandling']}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Beslut:** {current_row['Go/No-go']}")
            c2.markdown(f"**Deadline:** {current_row['Deadline']}")
            c3.markdown(f"**Omfattning:** {current_row['Omfattning']}")
            
            st.markdown("---")
            st.markdown(f"**📝 Sammanfattning:**\n{current_row['Sammanfattning']}")
            st.markdown(f"**💡 GTM / Säljvinkel:**\n{current_row['Saljvinkel']}")
    else:
                        st.info("Inga uppdrag att visa i detaljvyn.")

    # --- FILTRERING OCH EXCEL-EXPORT (ENBART 'GO') ---
    # Filtrera bort allt som INTE är "Go"
    df_go_only = edited_df[edited_df["Go/No-go"] == "Go"].copy()

    st.markdown("---")
    if len(df_go_only) > 0:
        st.success(f"Du har markerat **{len(df_go_only)} st** uppdrag som **Go** som kommer att tas med i exporten.")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_go_only.to_excel(writer, index=False, sheet_name='Go-uppdrag Måndagsmöte')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Ladda ner Excel med enbart era Go-uppdrag",
            data=excel_data,
            file_name=f"GTM_Go_Uppdrag_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("💡 Inga uppdrag är satta som **Go** ännu. Ändra till 'Go' i tabellen ovan för att aktivera nedladdningsknappen för måndagsmötet.")
