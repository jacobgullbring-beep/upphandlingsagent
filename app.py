import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(
    page_title="PA D&S Radar",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

if st.button("TESTA PLAYWRIGHT"):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                "https://example.com",
                timeout=30000
            )

            title = page.title()

            browser.close()

        st.success("✅ Playwright fungerar")

        st.write(title)

    except Exception as e:

        st.error("❌ Playwright fungerar inte ännu")

        st.exception(e)
