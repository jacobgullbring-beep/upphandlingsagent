import streamlit as st
import pandas as pd
import anthropic
import os

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(
    api_key=api_key
)

st.success("✅ Claude ansluten")

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.dataframe(df)

    antal = st.slider(
        "Antal upphandlingar",
        1,
        min(len(df), 20),
        min(len(df), 10)
    )

    if st.button("🚀 Analysera"):

        resultat = []

        progress = st.progress(0)

        rows = df.head(antal)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])

            prompt = (
                "Du arbetar för PA Consulting Defence & Security.\n\n"
                "VIKTIGT:\n"
                "Bedöm INTE om kunden är militär.\n"
                "Bedöm om PA kan sälja management consulting.\n\n"
                "Ge hög score för:\n"
                "- PMO\n"
                "- Programledning\n"
                "- Transformation\n"
                "- Förändringsledning\n"
                "- Governance\n"
                "- Operating Model\n"
                "- Risk\n"
                "- Resiliens\n"
                "- Beredskap\n"
                "- Säkerhetsskydd\n"
                "- Informationssäkerhet\n"
                "- Cybersäkerhet\n"
                "- Verksamhetsutveckling\n"
                "- Ledningsstöd\n\n"
                "Ge låg score för:\n"
                "- Måleri\n"
                "- Bygg\n"
                "- Städning\n"
                "- Fordon\n"
                "- Varuinköp\n\n"
                f"Organisation: {organisation}\n"
                f"Titel: {title}\n"
                f"Beskrivning: {description}\n\n"
                "Svara i exakt format:\n"
                "SCORE: X\n"
                "KATEGORI: text\n"
                "MOTIVERING: text"
            )

            try:

                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=250,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                svar = response.content[0].text

            except Exception as e:

                svar = str(e)

            resultat.append({
                "Organisation": organisation,
                "Title": title,
                "AI Result": svar
            })

            progress.progress((i + 1) / len(rows))

        result_df = pd.DataFrame(resultat)

        st.subheader("🎯 Resultat")

        st.dataframe(
            result_df,
            use_container_width=True
        )
