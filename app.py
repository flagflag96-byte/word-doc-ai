import streamlit as st
import docx2txt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("⚙️ Admin Control Panel (Google Drive Secure Storage)")

# Fetches service account dictionaries directly out of cloud environment secrets securely
SCOPES = ['https://www.googleapis.com/auth/drive']
creds_dict = dict(st.secrets["gcp_service_account"]
)

# ⚠️ PASTE YOUR SHARED GOOGLE DRIVE FOLDER ID LINK CORRECTIONS HERE
DRIVE_FOLDER_ID = "https://drive.google.com/drive/folders/1WezwaqrZ_llVz3_ukTDi8Ds7rsc5fVQw" 

def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

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
                
                # Wipe old version files in the destination folder to prevent clutter
                query = f"name='live_corpus.txt' and '{DRIVE_FOLDER_ID}' in parents and trashed=false" if DRIVE_FOLDER_ID else "name='live_corpus.txt' and trashed=false"
                results = service.files().list(q=query, fields="files(id)").execute()
                items = results.get('files', [])
                for item in items:
                    service.files().delete(fileId=item['id']).execute()
                
                text_metadata = {'name': 'live_corpus.txt'}
                if DRIVE_FOLDER_ID:
                    text_metadata['parents'] = [DRIVE_FOLDER_ID]
                    
                media = MediaFileUpload(temp_file, mimetype='text/plain')
                service.files().create(body=text_metadata, media_body=media, fields='id').execute()
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            st.success("🎉 All documents successfully synchronized and backed up to Google Drive!")
        except Exception as e:
            st.error(f"Failed connection to Google Drive API: {e}")
    else:
        st.warning("Please upload at least one file first.")
