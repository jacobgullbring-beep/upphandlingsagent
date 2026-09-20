import streamlit as st
import pandas as pd
import anthropic
import os
import json
import io

st.set_page_config(page_title="DAS Upphandlingsbevakning", page_icon="🛡️", layout="wide")

st.title("🛡️ DAS Upphandlingsbevakning – Veckans Mötesvy")
st.write("Klistra in rådata från portalerna, välj ut intressanta uppdrag under mötet med checkrutor och exportera direkt till Excel!")

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen Anthropic API-nyckel hittades under Streamlit Secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# --- FLIKAR FÖR INMATNING ---
tab_kommers_1, tab_kommers_2, tab_eavrop, tab_mercell, tab_ovrig = st.tabs([
    "Kommers Annons (Notices)", 
    "Kommers Annons (eLite)", 
    "e-Avrop", 
    "Mercell", 
    "Övrigt / FMV"
])

with tab_kommers_1:
    text_c1 = st.text_area("Klistra in från Kommers Annons (Notices):", height=120, key="c1")

with tab_kommers_2:
    text_c2 = st.text_area("Klistra in från Kommers Annons (eLite):", height=120, key="c2")

with tab_eavrop:
    text_e = st.text_area("Klistra in från e-Avrop:", height=120, key="e")

with tab_mercell:
    text_m = st.text_area("Klistra in från Mercell:", height=120, key="e_mercell")

with tab_ovrig:
    text_o = st.text_area("Klistra in från Övrig Källa / FMV:", height=120, key="o")

st.markdown("---")

if st.button("🚀 Generera filtrerad säljtabell", type="primary", use_container_width=True):
    
    combined_input = f"""
    ### [KÄLLA: Kommers Annons (Notices)]
    {text_c1 if text_c1.strip() else "Ej data."}
    ### [KÄLLA: Kommers Annons (eLite)]
    {text_c2 if text_c2.strip() else "Ej data."}
    ### [KÄLLA: e-Avrop]
    {text_e if text_e.strip() else "Ej data."}
    ### [KÄLLA: Mercell]
    {text_m if text_m.strip() else "Ej data."}
    ### [KÄLLA: Övrigt / FMV]
    {text_o if text_o.strip() else "Ej data."}
    """
    
    if not any([text_c1.strip(), text_c2.strip(), text_e.strip(), text_m.strip(), text_o.strip()]):
        st.warning("Du behöver klistra in text i minst en flik först!")
    else:
        with st.spinner("Analyserar data, letar deadlines och rensar bort ej relevanta..."):
            
            prompt = f"""
            Du är en expert på Business Development / GTM för PA Consulting inom Defence & Security och management. Analysera råtexten nedan från upphandlingsportaler.
            
            VIKTIG REGLER FÖR FILTRERING:
            - TA BORT ALLA upphandlingar som rör byggnation, anläggning, renovering av fastigheter, gatuarbeten, VVS, elinstallationer i byggnader eller traditionell entreprenad.
            - Behåll ENDAST upphandlingar som rör: Försvar & Säkerhet, IT & Digitalisering, Managementkonsulttjänster, Strategi, Utbildning, Rådgivning, Systemutveckling eller analys.
            
            VIKTIGT OM DEADLINE:
            - Leta noggrant efter sista anbudsdag, anbudstid eller datum i texten som hör till respektive upphandling (t.ex. datum skrivna som ÅÅÅÅ-MM-DD, DD/MM eller liknande). 
            - Om du hittar ett datum, konvertera det till formatet ÅÅÅÅ-MM-DD. Om det absolut inte finns något datum, sätt "Ej angivet".
            
            Returnera resultatet ENDAST som en giltig JSON-lista med objekt för de relevanta upphandlingarna. Ingen inledande text, ingen markdown runt om. Varje objekt ska ha följande exakta nycklar (i denna ordning):
            - "Deadline": (Datum i formatet ÅÅÅÅ-MM-DD, eller "Ej angivet")
            - "Kategori": (T.ex. Försvar & Säkerhet, IT & Digitalisering, Management & Strategi)
            - "Myndighet": (Organisation/Köpare)
            - "Upphandling": (Titel på upphandlingen)
            - "Säljvinkel": (Kort rekommendation för PA Consulting-teamet)
            - "Källa": (Vilken plattform det kom från, t.ex. e-Avrop, Mercell, Kommers Annons)
            - "Käll-länk": (URL till respektive plattform om det finns i texten, annars lämna tom)

            Råtext att analysera:
            {combined_input}
            """
            
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                raw_output = "".join([block.text for block in response.content if hasattr(block, "text")])
                
                clean_json = raw_output.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                
                if not clean_json.endswith("]") and clean_json.startswith("["):
                    last_brace = clean_json.rfind("}")
                    if last_brace != -1:
                        clean_json = clean_json[:last_brace+1] + "\n]"
                
                data = json.loads(clean_json)
                df = pd.DataFrame(data)
                
                if not df.empty:
                    # Lägg till en kolumn med checkrutor först (False som standard)
                    df.insert(0, "Välj", False)
                    
                    if "Deadline" in df.columns:
                        df = df.sort_values(by="Deadline", ascending=True)
                    
                    st.session_state['tender_df'] = df
                    st.success(f"✅ Hittade {len(df)} relevanta upphandlingar!")
                else:
                    st.warning("Hittade inga relevanta upphandlingar efter filtrering.")
                    
            except Exception as e:
                st.error(f"Kunde inte tolka datat till tabell. Här är det råa svaret:\n\n{raw_output}")

# --- VISA INTERAKTIV TABELL OCH EXPORT OM DATA FINNS ---
if 'tender_df' in st.session_state and not st.session_state['tender_df'].empty:
    st.markdown("---")
    st.subheader("📋 Bocka för veckans intressanta uppdrag")
    st.write("Klicka i rutorna för de uppdrag ni vill gå vidare med under mötet:")
    
    # Använd data_editor så man kan klicka i checkrutorna live på skärmen
    edited_df = st.data_editor(
        st.session_state['tender_df'],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Välj": st.column_config.CheckboxColumn(
                "Välj för affär",
                help="Bocka för de uppdrag ni vill spåra vidare",
                default=False,
            )
        }
    )
    
    # Filtrera fram enbart de rader där checkrutan är ietkryssad
    selected_rows = edited_df[edited_df["Välj"] == True]
    
    st.markdown("### 💾 Exportera till Excel")
    if len(selected_rows) > 0:
        st.info(f"Du har valt **{len(selected_rows)}** uppdrag att exportera.")
        
        # Skapa en Excel-fil i minnet med pandas och openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Exkludera "Välj"-kolumnen från själva Excel-filen för renare ark
            export_df = selected_rows.drop(columns=["Välj"])
            export_df.to_excel(writer, index=False, sheet_name="Utvalda Uppdrag")
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Ladda ner markerade som Excel (.xlsx)",
            data=excel_data,
            file_name="Utvalda_Upphandlingar_PA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.write("*(Bocka för minst ett uppdrag ovan för att aktivera nerladdningsknappen)*")
