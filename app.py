import streamlit as st
import anthropic
import os
import json

st.set_page_config(
    page_title="PA D&S Opportunity Radar",
    page_icon="🛡️",
    layout="wide"
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

st.markdown("""
### Klistra in upphandlingstext

AI bedömer:

✅ Relevans för PA Defence & Security

✅ PMO

✅ Programledning

✅ Transformation

✅ Beredskap

✅ Säkerhet

✅ Förändringsledning

✅ Värde och prioritet
""")

text_input = st.text_area(
    "Upphandlingstext",
    height=350
)

if st.button("🚀 Analysera"):

    if not text_input:

        st.warning("Klistra in upphandlingstext först.")
        st.stop()

    prompt = f"""
Du arbetar som erfaren bid manager för
PA Consulting Defence & Security Sverige.

Fundera INTE på om kunden är militär.

Fundera på om PA Consulting D&S skulle kunna sälja:

- PMO
- Programledning
- Transformation
- Förändringsledning
- Operating Model
- Governance
- Risk
- Resiliens
- Beredskap
- Säkerhetsskydd
- Informationssäkerhet
- Cybersäkerhet
- Verksamhetsutveckling
- Strategi

Bedöm upphandlingen.

Returnera ENDAST JSON:

{{
  "score": 0,
  "recommendation": "",
  "category": "",
  "estimated_value": "",
  "summary": "",
  "reason": "",
  "opportunity_type": "",
  "keywords_found": []
}}

UPPHANDLING:

{text_input}
"""

    try:

        with st.spinner("AI analyserar..."):

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

        result = response.content[0].text

        st.subheader("🎯 Resultat")

        try:

            parsed = json.loads(result)

            score = parsed.get("score", 0)

            if score >= 80:
                st.success(f"🔥 Hög potential ({score}/100)")

            elif score >= 50:
                st.warning(f"🟡 Möjlig möjlighet ({score}/100)")

            else:
                st.error(f"🔴 Låg relevans ({score}/100)")

            st.json(parsed)

        except:

            st.code(result)

    except Exception as e:

        st.exception(e)
