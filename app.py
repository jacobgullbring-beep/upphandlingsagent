import streamlit as st
import pandas as pd
import anthropic
import os
from io import BytesIO
 
st.set_page_config(
page_title="PA Defence & Security Opportunity Radar",
page_icon="🛡️",
layout="wide"
)
 
st.title("🛡️ PA Defence & Security Opportunity Radar")
 
# =====================================
# Claude
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
# Upload
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
value=min(len(df), 10)
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
"Bedöm INTE om kunden är militär.\n"
"Bedöm om PA kan sälja management consulting.\n\n"
"Ge hög relevans för:\n"
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
f"Värde: {value}\n\n"
"Svara enligt:\n"
"SCORE: X av 10\n"
"KATEGORI: ...\n"
"MOTIVERING: ..."
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
 
resultat.append(
{
"Organisation": organisation,
"Title": title,
"Value": value,
"Link": link,
"AI Result": ai_result
}
)
 
progress.progress(
(i + 1) / len(rows)
)
 
result_df = pd.DataFrame(resultat)
 
st.subheader("🎯 Resultat")
 
st.dataframe(
result_df,
use_container_width=True
)
 
# =====================================
# Excel Export
# =====================================
 
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
