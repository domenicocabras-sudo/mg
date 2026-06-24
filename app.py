import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import imagehash
import io
import os

st.title("Verifica Immagine da Catalogo PDF 📄")

# Nome del tuo file PDF su GitHub
PDF_FILE = "catalogo.pdf"

@st.cache_data
def load_pdf_data(pdf_path):
    """Estrae immagini e testo dal PDF."""
    db_data = {}
    if not os.path.exists(pdf_path):
        return None
    
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Estrai il testo come descrizione
        descrizione = page.get_text().strip()
        
        # 2. Estrai le immagini dalla pagina
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Converti in PIL Image
            img = Image.open(io.BytesIO(image_bytes))
            img_hash = imagehash.phash(img)
            
            # Salva nel database (usa l'xref come ID univoco)
            db_data[xref] = {
                "hash": img_hash,
                "descrizione": descrizione,
                "image": img
            }
    doc.close()
    return db_data

# Caricamento PDF
db_data = load_pdf_data(PDF_FILE)

if not db_data:
    st.error("File PDF non trovato. Caricalo nella cartella principale del repository.")
else:
    uploaded_file = st.file_uploader("Carica foto dallo smartphone...", type=['jpg', 'jpeg'])

    if uploaded_file:
        user_img = Image.open(uploaded_file)
        user_hash = imagehash.phash(user_img)
        
        found = False
        THRESHOLD = 5
        
        for key, data in db_data.items():
            if (user_hash - data['hash']) < THRESHOLD:
                st.success("### Corrispondenza trovata!")
                st.image(data['image'], caption="Immagine dal PDF")
                st.write(f"**Descrizione estratta:** {data['descrizione'][:200]}...") # Prime 200 lettere
                found = True
                break
        
        if not found:
            st.warning("Nessuna corrispondenza nel PDF.")
