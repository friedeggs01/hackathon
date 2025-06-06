import streamlit as st
import os
import requests
from pdf2docx import Converter
from docx import Document
import tempfile
import hashlib
    
API_KEY = "AIzaSyBJo4sK0hzzeopDSj4GOUzsL6A9DEzTNZ4"
URL_API = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={API_KEY}"
)

SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

def hash_filename(filename: str):
    return hashlib.md5(filename.encode()).hexdigest()

def get_saved_paths(filename: str):
    file_hash = hash_filename(filename)
    return {
        "doc_text": os.path.join(SAVE_DIR, f"{file_hash}_doc.txt"),
        "translated_text": os.path.join(SAVE_DIR, f"{file_hash}_translated.txt"),
    }

def call_gemini_to_translate(text: str, src_lang: str, tgt_lang: str):
    prompt = (
        f"""Translate the following text from {src_lang} to {tgt_lang}, preserving formatting as much as possible.
        {text}
        --- End of text ---"""
    )
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(URL_API, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json().get("candidates", [])
        if not data:
            return "API returned no valid candidates."
        return data[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error calling Gemini API: {e}"

if "doc_text" not in st.session_state:
    st.session_state["doc_text"] = ""
if "translated_text" not in st.session_state:
    st.session_state["translated_text"] = ""
if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = None
if "has_uploaded_in_this_session" not in st.session_state:
    st.session_state["has_uploaded_in_this_session"] = False

with st.sidebar:
    st.header("📂 Upload PDF")
    uploaded_file = st.file_uploader("", type=["pdf"])
    
    if uploaded_file:
        st.session_state["has_uploaded_in_this_session"] = True
        st.session_state["uploaded_filename"] = uploaded_file.name
        saved_paths = get_saved_paths(uploaded_file.name)

        if os.path.exists(saved_paths["doc_text"]):
            with open(saved_paths["doc_text"], "r", encoding="utf-8") as f:
                st.session_state["doc_text"] = f.read()
            if os.path.exists(saved_paths["translated_text"]):
                with open(saved_paths["translated_text"], "r", encoding="utf-8") as f:
                    st.session_state["translated_text"] = f.read()
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(uploaded_file.read())
                pdf_path = tmp_pdf.name

            docx_path = pdf_path.replace(".pdf", ".docx")
            with st.spinner("Converting PDF to DOCX..."):
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()

            with st.spinner("Extracting text from DOCX..."):
                doc = Document(docx_path)
                paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                full_text = "\n\n".join(paragraphs)

            st.session_state["doc_text"] = full_text
            st.session_state["translated_text"] = ""

            with open(saved_paths["doc_text"], "w", encoding="utf-8") as f:
                f.write(full_text)

            os.remove(pdf_path)
            os.remove(docx_path)

        st.info(f"Uploaded: {uploaded_file.name}")

container = st.container()

with container:
    if not st.session_state["doc_text"] or not st.session_state["has_uploaded_in_this_session"]:
        st.info("Please upload a PDF file from the sidebar to get started.")
        st.stop()

    col1, col2 = st.columns(2)
    lang_options = ["en", "fr", "es", "kr", "jp"]
    with col1:
        src_lang = st.selectbox("Source language", options=lang_options, index=0)
    with col2:
        tgt_lang = st.selectbox("Target language", options=lang_options, index=1)

    st.markdown("---")
    st.subheader("📄 Original text (extracted from PDF)")
    st.text_area("Original text", st.session_state["doc_text"], height=300)

    st.markdown("---")
    if st.button("🚀 Translate to " + tgt_lang.upper()):
        with st.spinner(f"Translating from {src_lang} to {tgt_lang}…"):
            translated = call_gemini_to_translate(
                    st.session_state["doc_text"], src_lang, tgt_lang
                )
            st.session_state["translated_text"] = translated

            saved_paths = get_saved_paths(st.session_state["uploaded_filename"])
            with open(saved_paths["translated_text"], "w", encoding="utf-8") as f:
                f.write(translated)

    if st.session_state["translated_text"]:
        st.subheader("🌐 Translated text")
        st.text_area(
            f"Translated text ({tgt_lang})",
            st.session_state["translated_text"],
            height=300,
        )
