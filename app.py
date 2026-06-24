import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import imagehash
import io
import os

st.title("Catalogo Scanner 🔍")

# PUNTO CRITICO: Il nome della cartella deve essere esattamente questo
DB_FOLDER = "database_foto" 
PDF_FILE = "catalogo.pdf"

@st.cache_data
def get_data():
    data = []
    
    # 1. Carica dal PDF se esiste
    if os.path.exists(PDF_FILE):
        doc = fitz.open(PDF_FILE)
        for page in doc:
            img_list = page.get_images(full=True)
            for img_info in img_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                img = Image.open(io.BytesIO(base_image["image"]))
                data.append({"hash": imagehash.phash(img), "img": img, "text": page.get_text()[:100]})
        doc.close()
    
    # 2. Carica dalla cartella database_foto se esiste
    if os.path.exists(DB_FOLDER):
        for filename in os.listdir(DB_FOLDER):
            if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
                img = Image.open(os.path.join(DB_FOLDER, filename))
                data.append({"hash": imagehash.phash(img), "img": img, "text": filename})
                
    return data

# Esecuzione
catalog_data = get_data()

if not catalog_data:
    st.error(f"Nessun dato trovato! Assicurati che '{PDF_FILE}' o la cartella '{DB_FOLDER}' esistano.")
else:
    uploaded_file = st.file_uploader("Carica foto...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file:
        user_hash = imagehash.phash(Image.open(uploaded_file))
        found = False
        for item in catalog_data:
            if (user_hash - item['hash']) < 8:
                st.success("✅ Trovato!")
                st.image(item['img'])
                st.write(f"Info: {item['text']}")
                found = True
                break
        if not found:
            st.warning("Nessuna corrispondenza.")
            
