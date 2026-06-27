import streamlit as st
import fitz
from PIL import Image
import imagehash
import io
import os

# Configurazione
DB_FOLDER = "database_foto"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_FOLDER)

st.set_page_config(page_title="Catalogo Scanner", layout="wide")
st.title("Catalogo Scanner: Solo test.pdf 🔍")

@st.cache_data(ttl=1)
def get_data():
    data = []
    # Definiamo il file specifico da cercare
    file_da_cercare = "test.pdf"
    file_path = os.path.join(DB_PATH, file_da_cercare)

    # Controlliamo se il file specifico esiste
    if not os.path.exists(file_path):
        return data

    # Elaboriamo SOLO il file test.pdf
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
                    "text": f"Pagina {page.number + 1}",
                    "filename": file_da_cercare
                })
        doc.close()
    except Exception as e:
        st.error(f"Errore durante l'apertura di {file_da_cercare}: {e}")
            
    return data

# Logica di confronto
catalog_data = get_data()

if not catalog_data:
    st.error("Il file 'test.pdf' non è stato trovato o non contiene immagini elaborabili.")
else:
    uploaded_file = st.file_uploader("Carica foto per confronto", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        user_img = Image.open(uploaded_file).convert("RGB")
        user_hash = imagehash.phash(user_img)
        found = False
        
        for item in catalog_data:
            if (user_hash - item['hash']) < 20:
                st.success("✅ Trovata corrispondenza in test.pdf!")
                st.image(item['img'])
                st.write(f"**Dettaglio:** {item['text']}")
                found = True
                break
        if not found:
            st.warning("Nessuna corrispondenza trovata all'interno di test.pdf.")
