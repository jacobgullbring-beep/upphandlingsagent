import streamlit as st
import pandas as pd
import anthropic
import json
import os

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# Claude

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# CSV

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
        min(len(df), 5)
    )

    if st.button("🚀 Analysera"):

        resultat = []

        rows = df.head(antal)

        progress = st.progress(0)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])
            value = str(row["Value"])

            prompt = (
                "Du arbetar för PA Consulting Defence & Security.\n\n"
                "Bedöm om upphandlingen är relevant för:\n"
                "- PMO\n"
                "- Programledning\n"
                "- Transformation\n"
                "- Förändringsledning\n"
                "- Beredskap\n"
                "- Säkerhetsskydd\n"
                "- Informationssäkerhet\n"
                "- Cybersäkerhet\n\n"
                "Returnera ENDAST JSON enligt:\n"
                '{"score":0,"recommendation":"","category":"","reason":""}\n\n'
                f"Organisation: {organisation}\n"
                f"Titel: {title}\n"
                f"Beskrivning: {description}\n"
                f"Värde: {value}"
            )

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

                text = response.content[0].text

                try:
                    parsed = json.loads(text)

                except:
                    parsed = {
                        "score": 0,
                        "recommendation": "Parse Error",
                        "category": "",
                        "reason": text[:200]
                    }

            except Exception as e:

                parsed = {
                    "score": 0,
                    "recommendation": "Claude Error",
                    "category": "",
                    "reason": str(e)
                }

            resultat.append({
                "Organisation": organisation,
                "Title": title,
                "D&S Score": parsed.get("score", 0),
                "Recommendation": parsed.get("recommendation", ""),
                "Category": parsed.get("category", ""),
                "Reason": parsed.get("reason", "")
            })

            progress.progress((i + 1) / len(rows))

        result_df = pd.DataFrame(resultat)

        result_df = result_df.sort_values(
            by="D&S Score",
            ascending=False
        )

 
