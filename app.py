import requests
from bs4 import BeautifulSoup
import anthropic

def fetch_and_filter_tenders(api_key):
    # 1. Hämta hela sidan från e-Avrop
    url = "https://www.e-avrop.com/UpphandlingDefault.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return f"Kunde inte hämta sidan, statuskod: {response.status_code}"

    # 2. Rensa HTML och extrahera texten i tabellen
    soup = BeautifulSoup(response.text, "html.parser")
    # Hämta huvudinnehållet/tabellen för att minska antalet tokens som skickas
    table = soup.find("table") 
    raw_text = table.get_text(separator="\n", strip=True) if table else soup.get_text()

    # 3. Låt Claude analysera och filtrera ut relevanta upphandlingar
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""
    Här är en lista över aktuella offentliga upphandlingar från e-Avrop:

    ---
    {raw_text[:12000]}  # Begränsa tecken om sidan är väldigt lång
    ---

    Filtrera listan och visa endast upphandlingar inom management, IT, organisation, rådgivning eller konsulttjänster.
    Presentera resultatet i en snygg tabell med kolumnerna:
    - Titel
    - Organisation/Myndighet
    - Sista anbudsdag
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
