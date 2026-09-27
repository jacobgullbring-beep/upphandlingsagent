import streamlit as st
import pandas as pd
import anthropic
import os
from io import BytesIO
 
# =====================================
# SETUP
# =====================================
 
st.set_page_config(
page_title="PA Defence & Security Opportunity Radar",
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
# MODE
# =====================================
 
mode = st.radio(
"Välj källa",
["📧 e-Avrop Mail", "📊 CSV Upload"]
)
 
# =====================================
# E-AVROP MAIL
# =====================================
 
if mode == "📧 e-Avrop Mail":
 
email_text = st.text_area(
"Klistra in hela e-Avrop-mailet här",
height=400
)
 
if st.button("🚀 Analysera e-Avrop Mail"):
 
prompt = (
"Du arbetar för PA Consulting Defence & Security.\n\n"
"Analysera detta e-Avrop-mail.\n\n"
"Identifiera samtliga upphandlingar som nämns.\n\n"
"För varje upphandling returnera:\n"
"- Score 1-10\n"
"- Prioritet (Pursue, Review, Watch, Ignore)\n"
"- Organisation\n"
"- Titel\n"
"- Kategori\n"
"- Kort sammanfattning\n"
"- Motivering\n\n"
"Ge hög score för:\n"
"- Defence\n"
"- Security\n"
"- PMO\n"
"- Programledning\n"
"- Transformation\n"
"- Förändringsledning\n"
"- Governance\n"
"- Risk\n"
"- Resiliens\n"
"- Beredskap\n"
"- Informationssäkerhet\n"
"- Cybersäkerhet\n\n"
"Returnera resultatet som en tydlig tabell.\n\n"
"MAIL:\n"
+ email_text
)
 
with st.spinner("Analyserar..."):
 
try:
 
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
 
st.subheader("🎯 D&S Opportunity Radar")
 
st.markdown(
response.content[0].text
)
 
except Exception as e:
 
st.error(str(e))
 
# =====================================
# CSV
# =====================================
 
if mode == "📊 CSV Upload":
 
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
 
if st.button("🚀 Analysera CSV"):
 
resultat = []
 
rows = df.head(antal)
 
progress = st.progress(0)
 
for i, row in rows.iterrows():
 
organisation = str(row["Organisation"])
title = str(row["Title"])
description = str(row["Description"])
 
prompt = (
"Du arbetar för PA Consulting Defence & Security.\n\n"
"Bedöm relevansen för D&S.\n\n"
f"Organisation: {organisation}\n"
f"Titel: {title}\n"
f"Beskrivning: {description}\n\n"
"Returnera:\n"
"Score\n"
"Kategori\n"
"Sammanfattning\n"
"Motivering"
)
 
try:
 
response = client.messages.create(
model="claude-haiku-4-5-20251001",
max_tokens=400,
messages=[
{
"role": "user",
"content": prompt
}
]
)
 
result = response.content[0].text
 
except Exception as e:
 
result = str(e)
 
resultat.append({
"Organisation": organisation,
"Titel": title,
"Resultat": result
})
 
progress.progress(
(i + 1) / len(rows)
)
 
result_df = pd.DataFrame(resultat)
 
st.dataframe(
result_df,
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
sheet_name="Radar"
)
 
st.download_button(
label="📥 Ladda ner Excel",
data=output.getvalue(),
file_name="PA_DS_Radar.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
