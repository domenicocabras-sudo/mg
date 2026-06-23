import streamlit as st
from PIL import Image
import imagehash
import os

# Configurazione cartella
DB_FOLDER = "database_foto"
THRESHOLD = 5  # Soglia di differenza (più è bassa, più deve essere identica)

st.title("Verifica Immagine 🔍")

# 1. Caricamento e hashing del database (una sola volta)
@st.cache_data
def get_db_hashes():
    db_hashes = {}
    if os.path.exists(DB_FOLDER):
        for filename in os.listdir(DB_FOLDER):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(os.path.join(DB_FOLDER, filename))
                db_hashes[filename] = imagehash.phash(img)
    return db_hashes

# 2. Interfaccia di upload
uploaded_file = st.file_uploader("Carica una foto da confrontare...", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Mostra la foto caricata
    user_img = Image.open(uploaded_file)
    st.image(user_img, caption="Foto caricata", width=300)
    
    user_hash = imagehash.phash(user_img)
    db_hashes = get_db_hashes()
    
    st.write("Confronto in corso...")
    
    found = False
    for filename, db_h in db_hashes.items():
        diff = user_hash - db_h # Calcola la distanza di Hamming
        if diff < THRESHOLD:
            st.success(f"✅ Trovata corrispondenza: {filename} (Differenza: {diff})")
            found = True
            break
            
    if not found:
        st.warning("❌ Nessuna immagine simile trovata nel database.")
