import streamlit as st
import pandas as pd
import anthropic
import os
from io import BytesIO

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️"
)

st.title("🛡️ PA D&S Opportunity Radar")

# Claude

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
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

    if st.button("🚀 Analysera första 5 upphandlingarna"):

        resultat = []

        rows = df.head(5)

        progress = st.progress(0)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])

            prompt = (
                "Du arbetar för PA Consulting Defence & Security.\n\n"
                "Bedöm om PA kan sälja management consulting här.\n\n"
                f"Organisation: {organisation}\n"
                f"Titel: {title}\n"
                f"Beskrivning: {description}\n\n"
                "Svara med:\n"
                "SCORE: X av 10\n"
                "KATEGORI: ...\n"
                "MOTIVERING: ..."
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

                ai_result = response.content[0].text

            except Exception as e:

                ai_result = str(e)

            resultat.append({
                "Organisation": organisation,
                "Titel": title,
                "AI Result": ai_result
            })

            progress.progress((i + 1) / len(rows))

        result_df = pd.DataFrame(resultat)

        st.subheader("🎯 Resultat")

        st.dataframe(result_df)

        # Excel-export

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result_df.to_excel(
                writer,
                index=False,
                sheet_name="Resultat"
            )

        st.download_button(
            label="📥 Ladda ner Excel",
            data=output.getvalue(),
            file_name="PA_DS_Resultat.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
