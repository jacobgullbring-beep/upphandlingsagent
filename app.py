import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(
    page_title="Mercell Test",
    page_icon="🛡️"
)

st.title("🛡️ Mercell Browser Test")

URL = st.text_input(
    "Mercell URL",
    value="https://app.mercell.com/org/goteborgs_stads_upphandlingar"
)

if st.button("TEST PLAYWRIGHT"):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                URL,
                wait_until="networkidle",
                timeout=60000
            )

            html = page.content()

            browser.close()

        st.success("Sidan hämtad")

        st.write("Antal tecken")

        st.write(len(html))

        st.text_area(
            "HTML",
            html[:10000],
            height=500
        )

    except Exception as e:

        st.exception(e)
