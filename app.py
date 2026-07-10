import streamlit as st
import docx2txt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import base64
import os

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("⚙️ Admin Control Panel (Google Drive Secure Storage)")

SCOPES = ['https://www.googleapis.com/auth/drive']
DRIVE_FOLDER_ID = "1WezwaqrZ_llVz3_ukTDi8Ds7rsc5fVQw" 

def get_drive_service():
    try:
        # መረጃውን ከ Streamlit Secrets ላይ ማንበብ
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 🔐 በ Base64 የታሰረውን ቁልፍ ፈትቶ ወደ መደበኛ ጽሑፍ መቀየር
        b64_key = creds_info["private_key_base64"]
        decoded_key = base64.b64decode(b64_key).decode("utf-8")
        
        # የ \n ምልክቶችን በትክክል ወደ አዲስ መስመር መለወጥ
        fixed_key = decoded_key.replace("\\n", "\n")
        
        # የሰርቪስ አካውንት መዋቅር ማዘጋጀት
        creds_dict = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": fixed_key,
            "client_email": creds_info["client_email"],
            "client_id": creds_info["client_id"],
            "auth_uri": creds_info["auth_uri"],
            "token_uri": creds_info["token_uri"],
            "auth_provider_x509_cert_url": creds_info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": creds_info["client_x509_cert_url"],
            "universe_domain": creds_info.get("universe_domain", "googleapis.com")
        }
        
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"❌ Configuration Error: {e}")
        st.stop()

uploaded_files = st.file_uploader("Upload Microsoft Word files (.docx)", type=["docx"], accept_multiple_files=True)

if st.button("Process and Upload to Google Drive"):
    if uploaded_files:
        try:
            service = get_drive_service()
            combined_text = ""
            
            with st.spinner("Processing documents and syncing with Google Drive..."):
                for uploaded_file in uploaded_files:
                    file_text = docx2txt.process(uploaded_file)
                    combined_text += f"\n\n--- Start of Document: {uploaded_file.name} ---\n{file_text}\n"
                
                temp_file = "live_corpus.txt"
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(combined_text)
                
                # የድሮ ፋይል ካለ ማጥፋት
                query = f"name='live_corpus.txt' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
                results = service.files().list(q=query, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                items = results.get('files', [])
                for item in items:
                    try:
                        service.files().delete(fileId=item['id'], supportsAllDrives=True).execute()
                    except Exception:
                        pass
                
                # አዲሱን ፋይል መጫን
                text_metadata = {
                    'name': 'live_corpus.txt',
                    'parents': [DRIVE_FOLDER_ID]
                }
                    
                media = MediaFileUpload(temp_file, mimetype='text/plain', resumable=True)
                service.files().create(body=text_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            st.success("🎉 All documents successfully synchronized and backed up to Google Drive!")
        except Exception as e:
            st.error(f"Failed connection to Google Drive API: {e}")
    else:
        st.warning("Please upload at least one file first.")
