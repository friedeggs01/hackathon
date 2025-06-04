import streamlit as st
import os
from pdf2docx import Converter
from docx import Document
import tempfile

st.title("🔍 Searching platform for research")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.success(f"Uploaded file: {uploaded_file.name}")

    # Save uploaded file to a temporary path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(uploaded_file.read())
        pdf_path = tmp_pdf.name

    # Define temporary path for output .docx file
    docx_path = pdf_path.replace(".pdf", ".docx")

    # Convert PDF to DOCX
    with st.spinner("Converting PDF to DOCX..."):
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    st.success("Conversion to DOCX completed!")

    # Extract text from DOCX
    with st.spinner("Extracting text from DOCX..."):
        doc = Document(docx_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])

    # Show extracted text
    st.subheader("📄 Extracted Text:")
    st.text_area("Text from PDF", full_text, height=400)

    # Input box for question
    st.subheader("❓ Ask a Question:")
    user_question = st.text_input("Enter your question here")

    if user_question:
        st.info(f"You asked: {user_question}")
        # You can later plug in an LLM or search function here to answer the question

    # Clean up temporary files
    os.remove(pdf_path)
    os.remove(docx_path)
