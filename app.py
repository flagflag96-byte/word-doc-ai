import streamlit as st
import docx2txt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("⚙️ Admin Control Panel (Google Drive Secure Storage)")

# የደህንነት ፈቃድ መለያዎች
SCOPES = ['https://www.googleapis.com/auth/drive']

# 🛠️ ማስተካከያ፦ ቁልፉን በቀጥታ እዚህ በማስቀመጥ የ Secrets ፎርማት ስህተትን ሙሉ በሙሉ መፍታት
FIXED_KEY = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCn9OV6MlpqRsIE\n"
    "XCGT+ElDm1KFTF5q3/7dgRuk63jgdMH1m4WFnDMfEdvh8EwX3cPbN9WQYllK9ZBe\n"
    "Luit5UHK1vCPvzZw5r/l557QXic0aG1NKrwhP13qUm3klNkXwaptdacMaeckBMfE\n"
    "6SXq+cNtzYe5AixhgRX3JUdLndiCwNBkEn1PULSfVmRYIKQ3zswP5RJEMTb27uW/\n"
    "+PPd4Ltd0kyJEoWiKWYsf3MMR8usMxoKkpb/8J6ae1plc/RnnBmlbzxceNQ6f1Dj\n"
    "x/L0X10ArZ2ZHdUNynma5xQ0ta6n2kmK//scm2Pyy2ugfp5tO8xFI1TYTTgtg5HL\n"
    "CUHRmwrdAgMBAAECggEAN63J/U6ABsdaPlPEleczcoQlQSdmDYwgU5IfdfbR5acP\n"
    "PbrG8torYFttR2N/9lGAQkYqOGlCLMVnjLGEVVGxE+tZaG39QERezXqRfYYY/Ri5\n"
    "U2GdaHA3VBzrbWGi7ms3cn4UWNsq0xf6md6owVL3ZIlEOyLrT4+Zlor3LawwQHfd\n"
    "YJQNH8+6sW/UAhd+QkJuMTDSkEhkrzxCE3fQTT6M20CRTHO/6EhOjRubp64pEhGt\n"
    "nokemiuORrfI/+a1jDSyNvc4czUGbqgQnR9bY2UforZ2A/xcnsLMOL2mg/uMPfKuR\n"
    "fXrpyaBWtE916RN2/J2vLqz25Pf01vH07+LRmwvaCQKBgQDcZm5RfdxWMpeEAn1e\n"
    "OalYtzj1F7HGrcFOPbB61kmGYA6yiyVH8IEva4mNVSW0jyeS9DkqqfDDqbvEHXmc\n"
    "I0LqnF5FH5vVoCZuvnfXMQqOGptKC9aUHk9xlDjBMuI9hm46bh3SqKDdzdGppMUg\n"
    "eY1u4AV2yLzTf3GS5C8xCzfJgwKBgQDDFevW7ylaARC6dutPrm/qH+myB1idFvKE\n"
    "9yxERqTTvFnadQSjVbL5TMbxxB7ORHxv4AOV1GhLSU+l+iVqT+aF8YZ7whQO2C/o\n"
    "9Nv3R+33M9yQiMaAit4X53tAXDOoj78s3VgXksEu9x0gyK/+ey3WQw/Nrtyb1oAl\n"
    "SwLdWuKMHwKBgC+AkDRWKSAW5VsZYkXlrZ8mVktU4QcOOgSP/TJsbwpcN665mL5\n"
    "kp5S0iG5AVhqJkBhDNUqLW8ubP62z5gcbXa9XwAM8PxY+Q+TU6b4teqsx11tMcFY\n"
    "ywySwqy5N9PE3osPYrQdjhZgHtkuXyJBsH7+H49bcn8vD552OcmbPlnbAoGBAI3h\n"
    "MH9Fuq5Bnhfuit6Nf8knYn/ehdzhpol7dg9FzXRMRJDzj+b2Wc6jvwBv4POkrVdz\n"
    "9UePjjZK4AlXLsTtzTrW2DbDhHDzW4yyIBPslS224w+e2bb8x99cs6+wHsXVnXUU\n"
    "mY+zZJoykFWafxy2GzT72s98/+a6jsIQlsnD4oWDAoGBAKRVuFayf8dXk3RC1ra7\n"
    "1unrjSdW37spBjNblEdZjwxdFRhRSZy+jZFNSqBInwrCS3ovp25XfppaQuh3e3Dw\n"
    "QOJu2hcQ9q3x2OC1gkHdb+CxJPb2j9brRdL3ErMcf3r3kqjY5apgmv09XP5hTIl2\n"
    "HovD/0ALakHDl5g5d8dQT25h\n"
    "-----END PRIVATE KEY-----\n"
)

# የጉግል አካውንት መረጃዎችን እዚህ መሰብሰብ
creds_dict = {
    "type": "service_account",
    "project_id": "modified-badge-500709-q9",
    "private_key_id": "0aa49bef4c970b55706b16325162496d86bc4c18",
    "private_key": FIXED_KEY,
    "client_email": "drive-ai-uploader@modified-badge-500709-q9.iam.gserviceaccount.com",
    "client_id": "115914592940349042795",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/drive-ai-uploader%40modified-badge-500709-q9.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# የእርስዎ የጉግል ድራይቭ ፎልደር መለያ ቁጥር (ID)
DRIVE_FOLDER_ID = "1WezwaqrZ_llVz3_ukTDi8Ds7rsc5fVQw" 

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
