import streamlit as st
import anthropic

st.title("🧪 Test av Claude API-nyckel")

# Hämta nyckeln från Streamlit Secrets
api_key = st.secrets.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("Ingen ANTHROPIC_API_KEY hittades under Secrets i Streamlit Cloud.")
    st.stop()

st.success("API-nyckel hittades i Secrets!")

if st.button("Kör testanrop mot Claude", type="primary"):
    with st.spinner("Skickar testförfrågan..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": "Svara med en kort hälsning och bekräfta att kopplingen fungerar!"}]
            )
            st.success("Kopplingen fungerar klockrent!")
            st.write(response.content[0].text)
        except Exception as e:
            st.error(f"Ett fel uppstod vid anropet: {e}")
