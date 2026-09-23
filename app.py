import streamlit as st
import pandas as pd
import anthropic
import os

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️"
)

st.title("🛡️ PA D&S Opportunity Radar")

# API key
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# CSV Upload
uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.dataframe(df)

    row = df.iloc[0]

    organisation = str(row["Organisation"])
    title = str(row["Title"])
    description = str(row["Description"])

    st.subheader("Första upphandlingen")

    st.write("Organisation:", organisation)
    st.write("Titel:", title)

    if st.button("🚀 Analysera första upphandlingen"):

        prompt = (
            "Du arbetar för PA Consulting Defence & Security.\n\n"
            "Bedöm INTE om kunden är militär.\n"
            "Bedöm om PA kan sälja management consulting.\n\n"
            "Ge hög relevans för:\n"
            "- PMO\n"
            "- Programledning\n"
            "- Transformation\n"
            "- Förändringsledning\n"
            "- Resiliens\n"
            "- Beredskap\n"
            "- Säkerhetsskydd\n"
            "- Informationssäkerhet\n\n"
            f"Organisation: {organisation}\n"
            f"Titel: {title}\n"
            f"Beskrivning: {description}\n\n"
            "Svara med 3 rader:\n"
            "SCORE: X av 10\n"
            "KATEGORI: ...\n"
            "MOTIVERING: ..."
        )

        with st.spinner("Analyserar..."):

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

                st.success("✅ Svar mottaget")

                st.text(response.content[0].text)

            except Exception as e:

                st.error(str(e))
