import streamlit as st
import docx2txt
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("⚙️ Admin Control Panel (Google Drive Secure Storage)")

# 🛠️ ማስተካከያ፦ ከ Streamlit Secrets ላይ የጉግል API Keyን በጥራት መጫን
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    st.error("❌ GOOGLE_API_KEY በ Streamlit Secrets ላይ አልተገኘም! እባክዎ በቅድሚያ በሳጥኑ ውስጥ ማስቀመጥዎን ያረጋግጡ።")
    st.stop()

# የእርስዎ የጉግል ድራይቭ ፎልደር መለያ ቁጥር (ID)
DRIVE_FOLDER_ID = "1WezwaqrZ_llVz3_ukTDi8Ds7rsc5fVQw" 

def get_drive_service():
    # በ API Key በቀጥታ ከ Google Drive ጋር መገናኘት (የቁልፍ ፎርማት ስህተትን ሙሉ በሙሉ ያስቀራል)
    return build('drive', 'v3', developerKey=GOOGLE_API_KEY)

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
                
                # የድሮ ፋይልን ከእርስዎ ማህደር (Folder) ውስጥ መፈለግ እና ማጥፋት
                query = f"name='live_corpus.txt' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
                results = service.files().list(q=query, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                items = results.get('files', [])
                for item in items:
                    try:
                        service.files().delete(fileId=item['id'], supportsAllDrives=True).execute()
                    except Exception:
                        pass
                
                # አዲሱን ፋይል በቀጥታ ወደ እርስዎ ማህደር (Folder) መጫን
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
