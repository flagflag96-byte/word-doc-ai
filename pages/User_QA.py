
import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import uuid

st.set_page_config(page_title="User AI Assistant", layout="wide")

st.markdown("""
    <style>
    .user-bubble { background-color: #2b5c8f; color: white; padding: 12px 16px; border-radius: 15px 15px 0px 15px; margin: 10px 0; width: fit-content; max-width: 80%; margin-left: auto; }
    .ai-bubble { background-color: #f0f2f6; color: #111111; padding: 12px 16px; border-radius: 15px 15px 15px 0px; margin: 10px 0; width: fit-content; max-width: 80%; }
    .chat-container { display: flex; flex-direction: column; }
    </style>
""", unsafe_allow_html=True)

st.title("📄 Cloud Document AI Assistant")

# Initialize Keys using internal cloud config secrets mappings
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_dict = dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=30)
def fetch_corpus_from_drive():
    try:
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(q="name='live_corpus.txt' and trashed=false", fields="files(id)").execute()
        items = results.get('files', [])
        
        if not items:
            return None
            
        file_id = items[0]['id']
        content = service.files().get_media(fileId=file_id).execute()
        return content.decode('utf-8')
    except Exception:
        return None

combined_text = fetch_corpus_from_drive()

if not combined_text:
    st.warning("⚠️ No synchronized cloud data found. Please ask the administrator to run upload cycles on the Admin Panel.")
    st.stop()

if "all_chats" not in st.session_state: st.session_state["all_chats"] = {}
if "current_chat_id" not in st.session_state: st.session_state["current_chat_id"] = None

with st.sidebar:
    st.header("💬 Chat Management")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state["all_chats"][new_id] = {"title": "New Conversation", "messages": []}
        st.session_state["current_chat_id"] = new_id
        st.rerun()
    st.write("---")
    search_query = st.text_input("🔍 Search conversations...", "").lower()
    st.subheader("🕒 Recent Chats")
    for chat_id, chat_data in list(st.session_state["all_chats"].items()):
        if search_query in chat_data["title"].lower():
            is_active = (chat_id == st.session_state["current_chat_id"])
            if st.button(f"📝 {chat_data['title']}", key=chat_id, use_container_width=True, type="secondary" if not is_active else "primary"):
                st.session_state["current_chat_id"] = chat_id
                st.rerun()

if not st.session_state["current_chat_id"] or st.session_state["current_chat_id"] not in st.session_state["all_chats"]:
    default_id = str(uuid.uuid4())
    st.session_state["all_chats"][default_id] = {"title": "New Conversation", "messages": []}
    st.session_state["current_chat_id"] = default_id

active_id = st.session_state["current_chat_id"]
current_messages = st.session_state["all_chats"][active_id]["messages"]

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in current_messages:
    if msg["role"] == "user": st.markdown(f'<div class="user-bubble"><b>You:</b><br>{msg["text"]}</div>', unsafe_allow_html=True)
    else: st.markdown(f'<div class="ai-bubble"><b>AI:</b><br>{msg["text"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    user_question = st.text_input("Message the Document AI...", placeholder="Type your question here...")
    submit_button = st.form_submit_button("Send ✨")

if submit_button and user_question.strip():
    current_messages.append({"role": "user", "text": user_question})
    if st.session_state["all_chats"][active_id]["title"] == "New Conversation":
        st.session_state["all_chats"][active_id]["title"] = user_question[:25] + "..."
        
    with st.spinner("Analyzing cloud documents..."):
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash-8b"]
        ai_answer = None
        prompt = f"Use ONLY this text to answer: {combined_text}\n\nQuestion: {user_question}\nAnswer:"
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                ai_answer = response.text
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower(): continue
                else: st.error(f"Error: {e}"); st.stop()
                
        if ai_answer:
            current_messages.append({"role": "ai", "text": ai_answer})
            st.rerun()
