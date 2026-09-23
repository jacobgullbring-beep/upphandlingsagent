import streamlit as st
import pandas as pd
import anthropic
import os
import json
from io import BytesIO

st.set_page_config(
    page_title="PA D&S Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# ==========================
# API KEY
# ==========================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# ==========================
# UPPLADDNING
# ==========================

uploaded_file = st.file_uploader(
    "Ladda upp Excel eller CSV",
    type=["xlsx", "csv"]
)

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    else:

        df = pd.read_excel(uploaded_file)

    st.subheader("Förhandsvisning")

    st.dataframe(df.head())

    col_to_analyse = st.selectbox(
        "Vilken kolumn innehåller upphandlingstexten?",
        df.columns
    )

    max_rows = st.slider(
        "Antal rader att analysera",
        min_value=1,
        max_value=min(50, len(df)),
        value=min(10, len(df))
    )

    if st.button("🚀 Analysera upphandlingar"):

        results = []

        progress = st.progress(0)

        rows = df.head(max_rows)

        for i, (_, row) in enumerate(rows.iterrows()):

            text = str(row[col_to_analyse])

            prompt = f"""
Du arbetar för PA Consulting Defence & Security Sverige.

Bedöm om upphandlingen är relevant för:

- PMO
- Programledning
- Transformation
- Förändringsledning
- Governance
- Risk
- Resiliens
- Beredskap
- Säkerhetsskydd
- Informationssäkerhet
- Cybersäkerhet
- Verksamhetsutveckling

Returnera endast JSON:

{{
  "score": 0,
  "recommendation": "",
  "category": "",
  "reason": ""
}}

UPPHANDLING:

{text}
"""

            try:

                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=600,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                result_text = response.content[0].text

                try:

                    parsed = json.loads(result_text)

                except:

                    parsed = {
                        "score": 0,
                        "recommendation": "Parse Error",
                        "category": "",
                        "reason": result_text[:500]
                    }

            except Exception as e:

                parsed = {
                    "score": 0,
                    "recommendation": "Error",
                    "category": "",
                    "reason": str(e)
                }

            result_row = row.to_dict()

            result_row["D&S Score"] = parsed.get("score", 0)
            result_row["Recommendation"] = parsed.get("recommendation", "")
            result_row["Category"] = parsed.get("category", "")
            result_row["Reason"] = parsed.get("reason", "")

            results.append(result_row)

            progress.progress((i + 1) / len(rows))

        result_df = pd.DataFrame(results)

        result_df = result_df.sort_values(
            by="D&S Score",
            ascending=False
        )

        st.subheader("🎯 Resultat")

        st.dataframe(
            result_df,
            use_container_width=True
        )

        high_priority = result_df[
            result_df["D&S Score"] >= 80
        ]

        st.subheader("🔥 High Priority Opportunities")

        st.dataframe(
            high_priority,
            use_container_width=True
        )

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result_df.to_excel(
                writer,
                index=False,
                sheet_name="D&S Radar"
            )

        st.download_button(
            label="📥 Ladda ned analyserad Excel",
            data=output.getvalue(),
            file_name="PA_DS_Radar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
