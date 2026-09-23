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

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.dataframe(df)

    if st.button("🚀 Testa första upphandlingen"):

        row = df.iloc[0]

        prompt = (
            f"Organisation: {row['Organisation']}\n"
            f"Titel: {row['Title']}\n"
            f"Beskrivning: {row['Description']}\n\n"
            "Bedöm om detta är relevant för PA Consulting Defence & Security.\n"
            "Ge score mellan 0 och 100 samt motivering."
        )

        st.write("⏳ Skickar till Claude...")

        try:

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            st.success("✅ Svar mottaget")

            st.write(response.content[0].text)

        except Exception as e:

            st.error(str(e))
