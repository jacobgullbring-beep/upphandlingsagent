import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PA Defence & Security Opportunity Radar",
    page_icon="🛡️"
)

st.title("🛡️ PA Defence & Security Opportunity Radar")

st.success("✅ App fungerar")

uploaded_file = st.file_uploader(
    "Ladda upp CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("✅ CSV inläst")

    st.write("Kolumner hittade:")

    st.write(df.columns.tolist())

    st.dataframe(df)
