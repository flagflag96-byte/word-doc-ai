import streamlit as st
import docx2txt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import base64

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("⚙️ Admin Control Panel (Google Drive Secure Storage)")

SCOPES = ['https://www.googleapis.com/auth/drive']

# 🛠️ ማስተካከያ 1፦ ሙሉ በሙሉ 100% ንጹህ የሆነ የ Base64 ቁልፍ (ምንም የተሳሳተ ምልክት የሌለበት)
B64_KEY = (
    "TUlJRXZnSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2d3Z2dTa0FnRUFBb0lCQVFDbjVPVjZNb"
    "HBxUnNJRVhDR1QrRWxEbTFLRlRZNXEzLzdkZ1J1azYzamdkaE0xbTRXRm5ETWZFeHZoOEV3WDNjUGJ"
    "OOVdRWWxsSzlaQmVMdWl0NVhVSzF2Q1B2elpzNXIvbDU1N1FYaWMwYUcxTktyd2hQMTNxVW0za2xOM"
    "lh3YXB0ZGFjTWFlY2tCTWZFNlNYcStjTnR6WWU1QWl4aGdSWDNKVWRMbmRpQ3dORmtFbjFwVUxTZlZ"
    "tUllJS1Qzek9QNVJKRU1UYjI3dVcvK1BQZDRMdGQwa3lKRW9XaUtXWXNmM01NUjh1c014b0twYi84S"
    "jZhZTlwbGMvUnpuQm1MYnhjZU5RNmYxRGp4LzBYMTBBcloyWkhkVU55bm1hNXhRMHRhNm4ya0tMLy9z"
    "Ym1QeXkydWdmcDV0Tzh4RkkxVFlUVGd0ZzVITENVSFJtd3JkQWdNQkFBRUNnZ0VBTjYzSi9VNkFCc2Rh"
    "UGxQRWxlY3pjb1FsUVNkbURZd2dVNklmZGZiUjVhY1BQUmJHOTh0b1lGdHRSMk4vOWxHQVFrWXFPR2x"
    "DTE1WbmpMR0VWVkd4RSt0WmFHMzlRRVJleFhxUmZZWVkvUmk1VTJHZGFIQTNWQnpyV0dpN21zM2NuNF"
    "VXTmp0WGZmNm1kNm93VkwzWklMRW95THJUNCtabG9yM0xhd3dRSGZkWUpORjgrNnNXL1VBaGQrUWtKd"
    "U1UREJrRWhrenhDRTNmUVRUNk0yMENSVEhPLzZEaE9qUnVicDY0cEVoR3Rub2tlbWl1T1JyZkkvK2Ex"
    "akRTeU52YzRjelVnYnFnUW5SMmJZMlVmb3JaMkEveGNuc0xNTDJtZy91TVBmS3VSZlhycHlhQld0RTk"
    "xNlJOMi9KMnZMcXoyNVBmMDF2SDA3K0xSbXd2YUNRS0JnUURjWm01UmZkeFdNcGVFQW4xZU9hbFl0am"
    "oxRjdIR3JjRk9QYkI2MWttR1lBNnlpeVZIOElFdmE0bU5WU1cwdGplUzlEa3FxZkREcWJ2RUhYbWNJM"
    "ExxbkY1Rkg1dlZvQ1p1dm5YTVFxT0dwdEtDOWFVSEtrOXhsRGpCTXVJOWhtNDZiaDNTcUtEemRHY3BN"
    "VWdlWTF1NEFWMnlMelRmM0dTNUM4eEN6Zkpnd0tCZ1FEREZldlc3eWxhQVJDNmR1dFBybS9xSCtteUI"
    "xaWRGdktFOXl4RVJxVFR2Rm5hZFFzalZiTDVUTWJ4eEI3T1JIeHY0QU9WMUdoTFNVK2wrdklxVCthRj"
    "hZWjd3aFFPMkMvbzlOdjNSKzMzTTl5UWlNYUFpdDRYNTN0QVhET29qNzhzM1ZnWGtzRXU5eDBneUtvL"
    "ytleTNXUXcvTnJ0eWIxb0FsU3dMZFd1S01Id0tCZ0MrQWtEUldLU0FXNVZzWllrWGxyWjdtVmt0VTRR"
    "Y09PZ1NQL1RKc2J3cGNOVTY2bUw1a3A1UzBpRzVBVmhxSmtCaEROVXFMVzh1YlA2Mno1Z2NiWGE5WG"
    "RDNFB4WStRK1RVNmI0dGVxc3gxMXRNY0ZBeXd5U3dxeTVOOUZFM29zUFlyUWRqaFpnSHRrdVh5SkJz"
    "SDcrSDQ5YmNuOHZENTUycU9tYlBsbmJBb0dCQUkzaE1IOUZ1cTVCbmZodWl0Nk5mOGtueW4vZWhkemh"
    "wb2w3ZGc5RnpYUk1SSUR6aitidjJXYzZqdndCdjRQT2tyVmR6OVVlUGpqWks0QWxYTHNUdHpUclcyRE"
    "JEaEhEeldIeXlJQlBzbFMyMjR3K2UyYmI4eDk5Y3M2K3dIc1hWblhVVW1ZK3paSm95a0ZXYWZ4eTJHe"
    "lRZNnM5OC8raTZqc0lRbHNuRDZvV0RBb0dCQUtSVnVGQXlmOGRreDNUQzFyYTcxdW5yalNkVzM3c3BC"
    "ak5ibEVkWmp3eGRSaFJTWnl5K2paTlNxQklud3JDUzNvdTI1WGZwcGVRdTNodeNEd1FPMnUyY2NROXQ"
    "zeDJPQzFna0hkYitDeEpPYjJqOWJyUkRMM0VyTWNmM3Mza2pZNTVhcWdtdjA5WFA1aFRJbDJIb3ZELz"
    "BBTGFrSERsNWc1ZDhkUVQyNWg="
)

# ቁልፉን ወደ መደበኛ የጽሑፍ ፎርማት መመለስ
decoded_key = base64.b64decode(B64_KEY).decode("utf-8")
FIXED_PRIVATE_KEY = f"-----BEGIN PRIVATE KEY-----\n{decoded_key}\n-----END PRIVATE KEY-----\n"

creds_dict = {
    "type": "service_account",
    "project_id": "modified-badge-500709-q9",
    "private_key_id": "0aa49bef4c970b55706b16325162496d86bc4c18",
    "private_key": FIXED_PRIVATE_KEY,
    "client_email": "drive-ai-uploader@modified-badge-500709-q9.iam.gserviceaccount.com",
    "client_id": "115914592940349042795",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/drive-ai-uploader%40modified-badge-500709-q9.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# 🛠️ ማስተካከያ 2፦ የእርስዎ የግል Google Drive ማህደር (Folder ID)
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
                
                # 🛠️ ማስተካከያ 3፦ የ Quota 403 ስህተትን ለማስቀረት ፍለጋውን በዚህ ፎልደር ላይ ብቻ መወሰን
                query = f"name='live_corpus.txt' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
                results = service.files().list(q=query, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                items = results.get('files', [])
                for item in items:
                    try:
                        service.files().delete(fileId=item['id'], supportsAllDrives=True).execute()
                    except Exception:
                        pass
                
                # አዲሱን ፋይል በቀጥታ ወደ እርስዎ ማህደር መጫን
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
