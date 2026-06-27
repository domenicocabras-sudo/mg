import streamlit as st
import fitz
from PIL import Image, ImageOps
import imagehash
import io
import os

# --- CONFIGURAZIONE ---
DB_FOLDER = "database_foto"
FILE_TARGET = "test.pdf"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_FOLDER)
FILE_PATH = os.path.join(DB_PATH, FILE_TARGET)

st.set_page_config(page_title="Catalogo Scanner", layout="wide")
st.title("Catalogo Scanner (Versione Stabile) 🔍")

@st.cache_data(ttl=3600)
def get_data():
    data = []
    if not os.path.exists(FILE_PATH):
        return data

    try:
        doc = fitz.open(FILE_PATH)
        for page in doc:
            img_list = page.get_images(full=True)
            for img_info in img_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                # Apriamo l'immagine dal PDF
                img = Image.open(io.BytesIO(base_image["image"])).convert("RGB")
                # Riduciamo la risoluzione per rendere il confronto più robusto al rumore
                img_resiz = img.copy()
                img_resiz.thumbnail((400, 400))
                
                data.append({
                    "hash": imagehash.phash(img_resiz), 
                    "img": img, 
                    "text": f"Pagina {page.number + 1}",
                })
        doc.close()
    except Exception as e:
        st.error(f"Errore: {e}")
    return data

# --- LOGICA DI CONFRONTO ---
catalog_data = get_data()
uploaded_file = st.file_uploader("Carica foto", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # 1. Carica e normalizza orientamento (EXIF)
    user_img = Image.open(uploaded_file).convert("RGB")
    user_img = ImageOps.exif_transpose(user_img)
    
    # 2. Riduci risoluzione (come fatto per il database)
    user_img_resiz = user_img.copy()
    user_img_resiz.thumbnail((400, 400))
    
    user_hash = imagehash.phash(user_img_resiz)
    
    found = False
    # Con questo metodo (thumbnail + phash), una soglia di 15-20 è ideale
    SOGLIA = 18 
    
    for item in catalog_data:
        diff = user_hash - item['hash']
        if diff < SOGLIA:
            st.success(f"✅ Trovato! (Differenza: {diff})")
            st.image(item['img'], caption=f"Corrispondenza in {item['text']}")
            found = True
            break
            
    if not found:
        st.warning(f"Nessuna corrispondenza trovata (Differenza troppo alta).")
