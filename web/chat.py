import streamlit as st
import os
import requests
from pdf2docx import Converter
from docx import Document
import tempfile
import csv

# Path của file CSV lưu lịch sử hỏi-đáp
CSV_PATH = "qa_history.csv"
API_KEY = "AIzaSyBJo4sK0hzzeopDSj4GOUzsL6A9DEzTNZ4"
URL_API = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={API_KEY}"
)

def save_qa_to_csv(question, answer):
    """Append một dòng question–answer vào CSV."""
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([question, answer])

def load_previous_context():
    """Nạp 3 cặp QA gần nhất làm ngữ cảnh (nếu có)."""
    if not os.path.exists(CSV_PATH):
        return ""
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        history = list(reader)
        context = ""
        for q, a in history[-3:]:
            context += f"Q: {q}\nA: {a}\n"
        return context

def call_gemini(question: str, content: str):
    """Gọi API Gemini, thêm ngữ cảnh trước đó vào prompt."""
    previous_context = load_previous_context()
    prompt = (
        f"""Use the document content and previous conversation to answer the question.
        ## Document Content:
        {content}

        ## Previous Conversation:
        {previous_context}

        ## Current Question:
        {question}
        """
    )
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(URL_API, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json().get("candidates", [])
        if not data:
            return "API returned no valid candidates."
        return data[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error calling Gemini API: {e}"

# Khởi tạo session_state để lưu chat history và nội dung tài liệu
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # mỗi phần tử: {"role": "user"/"assistant", "text": str}
if "doc_text" not in st.session_state:
    st.session_state["doc_text"] = ""  # toàn bộ text của PDF đã chuyển

# Sidebar: upload và hiển thị nội dung tóm tắt
with st.sidebar:
    st.header("📂 Tải lên PDF")
    uploaded_file = st.file_uploader("", type=["pdf"])
    if uploaded_file:
        st.success(f"Đã tải: {uploaded_file.name}")
        # Lưu file PDF tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(uploaded_file.read())
            pdf_path = tmp_pdf.name
        # Đường dẫn .docx
        docx_path = pdf_path.replace(".pdf", ".docx")
        # Chuyển PDF → DOCX
        with st.spinner("Đang chuyển PDF thành DOCX..."):
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None)
            cv.close()
        # Trích xuất text từ DOCX
        with st.spinner("Đang trích xuất text từ DOCX..."):
            doc = Document(docx_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state["doc_text"] = full_text
        # Hiển thị đoạn preview (collapse)
        with st.expander("📄 Xem nội dung trích xuất"):
            st.text_area("Text từ PDF", full_text, height=300)
        # Xóa temp files
        os.remove(pdf_path)
        os.remove(docx_path)

st.title("💬 Chat Research")

# --- Phần chatbox: messages + input cố định ---
# 2) Hiển thị tất cả messages trong div vừa tạo
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["text"])
    else:
        st.chat_message("assistant").write(msg["text"])
st.markdown("</div>", unsafe_allow_html=True)

# 3) Chat input luôn nằm dưới div chứa messages
if st.session_state["doc_text"]:
    user_input = st.chat_input("Nhập câu hỏi của bạn...")
else:
    user_input = st.chat_input("Vui lòng tải lên PDF trước khi hỏi...")

if user_input:
    if not st.session_state["doc_text"]:
        st.warning("Bạn hãy tải lên file PDF để có tài liệu làm ngữ cảnh.")
    else:
        # Thêm tin nhắn user vào session state và hiển thị luôn
        st.session_state["messages"].append({"role": "user", "text": user_input})
        st.chat_message("user").write(user_input)

        # Gọi Gemini để lấy câu trả lời
        with st.spinner("Đang tạo phản hồi..."):
            answer_text = call_gemini(user_input, st.session_state["doc_text"])

        # Thêm tin nhắn assistant vào session state và hiển thị
        st.session_state["messages"].append({"role": "assistant", "text": answer_text})
        st.chat_message("assistant").write(answer_text)

        # Lưu QA vào CSV
        save_qa_to_csv(user_input, answer_text)
