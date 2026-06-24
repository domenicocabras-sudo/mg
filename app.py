import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import imagehash
import io
import os

st.title("Catalogo Scanner V2 🔍")

# Percorsi fissi
PDF_PATH = "catalogo.pdf"
DB_DIR = "database_foto"

# Funzione per caricare le immagini dal PDF
@st.cache_data
def get_pdf_data():
    if not os.path.exists(PDF_PATH):
        return None
    data = []
    doc = fitz.open(PDF_PATH)
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img = Image.open(io.BytesIO(base_image["image"]))
            data.append({"hash": imagehash.phash(img), "img": img, "text": "Foto da PDF"})
    doc.close()
    return data

# Visualizzazione errori
if not os.path.exists(PDF_PATH):
    st.error(f"Errore: Il file '{PDF_PATH}' non è stato trovato nella root di GitHub.")
else:
    catalog_data = get_pdf_data()
    uploaded_file = st.file_uploader("Carica una foto dallo smartphone:", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        user_img = Image.open(uploaded_file)
        user_hash = imagehash.phash(user_img)
        
        found = False
        for item in catalog_data:
            if (user_hash - item['hash']) < 8:
                st.success("✅ Corrispondenza trovata!")
                st.image(item['img'], caption="Oggetto identificato")
                found = True
                break
        if not found:
            st.warning("Nessuna corrispondenza trovata nel catalogo.")
