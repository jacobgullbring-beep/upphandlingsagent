import streamlit as st
import pandas as pd
import anthropic
import os
import re
from io import BytesIO

# =====================================
# SETUP
# =====================================

st.set_page_config(
    page_title="PA D&S Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

# =====================================
# CLAUDE
# =====================================

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY saknas")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.success("✅ Claude ansluten")

# =====================================
# CSV
# =====================================

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.dataframe(df)

    antal = st.slider(
        "Antal upphandlingar",
        min_value=1,
        max_value=min(len(df), 20),
        value=min(len(df), 5)
    )

    if st.button("🚀 Analysera"):

        resultat = []

        progress = st.progress(0)

        rows = df.head(antal)

        for i, row in rows.iterrows():

            organisation = str(row["Organisation"])
            title = str(row["Title"])
            description = str(row["Description"])
            value = str(row["Value"])
            link = str(row["Link"])

            prompt = (
                "Du arbetar för PA Consulting Defence & Security.\n\n"
                "Bedöm om PA kan sälja management consulting här.\n\n"
                "Returnera EXAKT enligt detta format:\n\n"
                "SCORE: X\n"
                "CATEGORY: ...\n"
                "SUMMARY: ...\n"
                "REASON: ...\n\n"
                "Ge hög score för:\n"
                "- PMO\n"
                "- Programledning\n"
                "- Transformation\n"
                "- Förändringsledning\n"
                "- Governance\n"
                "- Risk\n"
                "- Resiliens\n"
                "- Beredskap\n"
                "- Säkerhetsskydd\n"
                "- Informationssäkerhet\n"
                "- Cybersäkerhet\n"
                "- Verksamhetsutveckling\n\n"
                f"Organisation: {organisation}\n"
                f"Titel: {title}\n"
                f"Beskrivning: {description}\n"
                f"Värde: {value}\n"
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

                ai_result = response.content[0].text

            except Exception as e:

                ai_result = str(e)

            # ==========================
            # Extrahera fält
            # ==========================

            score = 0
            category = ""
            summary = ""
            reason = ""

            score_match = re.search(
                r"SCORE:\s*(\d+)",
                ai_result,
                re.IGNORECASE
            )

            if score_match:
                score = int(score_match.group(1))

            for line in ai_result.splitlines():

                if line.upper().startswith("CATEGORY:"):
                    category = line.replace(
                        "CATEGORY:",
                        ""
                    ).strip()

                elif line.upper().startswith("SUMMARY:"):
                    summary = line.replace(
                        "SUMMARY:",
                        ""
                    ).strip()

                elif line.upper().startswith("REASON:"):
                    reason = line.replace(
                        "REASON:",
                        ""
                    ).strip()

            # ==========================
            # Prioritet
            # ==========================

            if score >= 9:
                priority = "🔥 Pursue"

            elif score >= 7:
                priority = "🟢 Review"

            elif score >= 5:
                priority = "🟡 Watch"

            else:
                priority = "🔴 Ignore"

            resultat.append(
                {
                    "Score": score,
                    "Priority": priority,
                    "Organisation": organisation,
                    "Title": title,
                    "Category": category,
                    "Summary": summary,
                    "Reason": reason,
                    "Value": value,
                    "Link": link
                }
            )

            progress.progress(
                (i + 1) / len(rows)
            )

        result_df = pd.DataFrame(resultat)

        result_df = result_df.sort_values(
            by="Score",
            ascending=False
        )

        # ==========================
        # Dashboard
        # ==========================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🔥 Pursue",
                len(
                    result_df[
                        result_df["Priority"] == "🔥 Pursue"
                    ]
                )
            )

        with col2:

            st.metric(
                "🟢 Review",
                len(
                    result_df[
                        result_df["Priority"] == "🟢 Review"
                    ]
                )
            )

        with col3:

            st.metric(
                "🔴 Ignore",
                len(
                    result_df[
                        result_df["Priority"] == "🔴 Ignore"
                    ]
                )
            )

        # ==========================
        # Resultat
        # ==========================

        st.subheader("🎯 D&S Opportunity Radar")

        st.dataframe(
            result_df,
            use_container_width=True
        )

        # ==========================
        # Excel Export
        # ==========================

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
            label="📥 Ladda ner Excel",
            data=output.getvalue(),
            file_name="PA_DS_Opportunity_Radar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
