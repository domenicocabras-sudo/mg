import streamlit as st
import fitz
from PIL import Image
import imagehash
import io
import os

# Configurazione
DB_FOLDER = "database_foto"
# Assicuriamoci di lavorare solo con percorsi relativi sicuri
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_FOLDER)

st.set_page_config(page_title="Catalogo Scanner", layout="wide")
st.title("Catalogo Scanner 🔍")

@st.cache_data
def get_data():
    data = []
    if not os.path.exists(DB_PATH):
        return data

    for filename in os.listdir(DB_PATH):
        file_path = os.path.join(DB_PATH, filename)
        
        # Gestione PDF
        if filename.lower().endswith('.pdf'):
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    img_list = page.get_images(full=True)
                    for img_info in img_list:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        img = Image.open(io.BytesIO(base_image["image"])).convert("RGB")
                        data.append({
                            "hash": imagehash.phash(img), 
                            "img": img, 
                            "text": f"Dal PDF: {filename} - Pag {page.number + 1}"
                        })
                doc.close()
            except Exception:
                pass # Ignora file PDF corrotti

        # Gestione Immagini
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
            try:
                with Image.open(file_path) as img:
                    img_rgb = img.convert("RGB")
                    data.append({
                        "hash": imagehash.phash(img_rgb), 
                        "img": img_rgb.copy(), 
                        "text": f"File: {filename}"
                    })
            except Exception:
                pass # Ignora file immagine non validi
    return data

# Logica di confronto
catalog_data = get_data()
uploaded_file = st.file_uploader("Carica foto per confronto", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    user_img = Image.open(uploaded_file).convert("RGB")
    user_hash = imagehash.phash(user_img)
    found = False
    
    for item in catalog_data:
        if (user_hash - item['hash']) < 8:
            st.success("✅ Trovata corrispondenza!")
            st.image(item['img'])
            st.write(f"Fonte: {item['text']}")
            found = True
            break
    if not found:
        st.warning("Nessuna corrispondenza trovata.")
