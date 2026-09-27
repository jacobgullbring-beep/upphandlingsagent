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
