import streamlit as st
import requests

API_KEY = "AIzaSyBJo4sK0hzzeopDSj4GOUzsL6A9DEzTNZ4"
URL_API = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={API_KEY}"
)

def call_gemini_scientific_paraphrase(input_text: str) -> str:
    prompt = (
        "Please correcting grammar where necessary then rewrite the following text in the style of a scientific article, no need for addition context or content"
        "only returning the paragraph after rewrite:\n\n"
        f"{input_text}\n"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(URL_API, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json().get("candidates", [])
        if not data:
            return "API returned no valid candidates."
        return data[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error calling Gemini API: {e}"


st.markdown(
    """
    Enter the paragraph you want to rewrite in the style of a scientific article.
    """
)

input_text = st.text_area(
    label="📥 Enter Original Paragraph:",
    height=200,
    placeholder="Type your paragraph here..."
)

if st.button("✍️ Rewrite"):
    if not input_text.strip():
        st.warning("Please enter at least one paragraph.")
    else:
        with st.spinner("Start rewriting..."):
            paraphrased = call_gemini_scientific_paraphrase(input_text)
        st.text_area(
            label="📤 Rewrote Text (Scientific Style):",
            value=paraphrased,
            height=200
        )