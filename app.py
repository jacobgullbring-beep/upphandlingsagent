import anthropic
from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="GTM Upphandlingsbevakning", page_icon="🛡️", layout="wide"
)

st.title("🛡️ e-Avrop Bevakning & AI-analys")
st.write(
    "Hämtar publika upphandlingar automatiskt och låter Claude filtrera ut det"
    " som är intressant för dig."
)

# Hämta API-nyckel från Streamlit secrets eller sidopanel
api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.sidebar.text_input(
    "Anthropic API Key", type="password"
)

# Inställning för antal sidor att skrapa
num_pages = st.sidebar.slider(
    "Antal sidor att hämta från e-Avrop", min_w=1, max_value=5, value=2
)


def fetch_e_avrop_pages(max_pages):
  base_url = "https://www.e-avrop.com/e-Upphandling/Default.aspx"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  tenders = []

  for page in range(1, max_pages + 1):
    url = f"{base_url}?page={page}" if page > 1 else base_url
    try:
      response = requests.get(url, headers=headers, timeout=10)
      if response.status_code != 200:
        break

      soup = BeautifulSoup(response.text, "html.parser")
      rows = soup.find_all("tr")

      for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
          titel = cols[0].get_text(strip=True)
          publicerad = cols[1].get_text(strip=True)
          organisation = cols[2].get_text(strip=True)
          kontext = cols[3].get_text(strip=True)
          deadline = cols[4].get_text(strip=True)

          if titel and organisation:
            tenders.append({
                "Titel": titel,
                "Publicerad": publicerad,
                "Organisation": organisation,
                "Kontext": kontext,
                "Deadline": deadline,
            })
    except Exception as e:
      st.error(
          f"Ett fel uppstod vid hämtning av sida {page}: {str(e)}"
          )
      break

  return pd.DataFrame(tenders)


if st.button("🚀 Hämta och analysera upphandlingar"):
  if not api_key:
    st.warning("Vänligen ange din Anthropic API-nyckel i sidopanelen eller secrets.")
  else:
    with st.spinner(
        "Skrapar e-Avrop och låter Claude analysera resultaten..."
    ):
      df = fetch_e_avrop_pages(num_pages)

      if df.empty:
        st.warning(
            "Kunde inga upphandlingar hittas. Kontrollera nätverket eller"
            " sidstrukturen."
        )
      else:
        st.success(f"Hittade totalt {len(df)} upphandlingar!")

        # Konvertera dataframe till text för att skicka till Claude
        data_text = df.to_json(orient="records", ensure_ascii=False)

        # Anropa Claude
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Här är en lista på aktuella offentliga upphandlingar i JSON-format:"
            f" \n\n{data_text}\n\nAnalysera denna lista. "
            "Presentera de mest intressanta och relevanta upphandlingarna"
            " (särskilt med fokus på management, konsulttjänster, IT och"
            " försvars-/säkerhetssektorn om det finns). "
            "Svara på svenska med en snygg och överskådlig sammanställning"
            " (gärna i tabellformat eller tydliga punkter) och motivera varför"
            " de är intressanta."
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        st.markdown("### 🤖 Claudes analys & filtrering")
        st.markdown(response.content[0].text)

        with st.expander("Visa rådata från alla hämtade sidor"):
          st.dataframe(df)
