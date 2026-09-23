import streamlit as st

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

st.markdown("""
### Mål V1

Vi testar just nu bara:

- Kan Streamlit starta?
- Kan Playwright starta?
- Kan vi sedan läsa Mercell?

Inga AI-funktioner ännu.
""")

st.success("✅ Streamlit fungerar")

st.write("Nästa steg är att få Playwright/Chromium installerat.")

st.code("""
När Playwright fungerar kommer nästa version att:

1. Öppna Göteborgs Mercell-sida
2. Hämta alla /tender/... länkar
3. Visa dem i tabell
4. Därefter lägger vi på Claude-score
""")
