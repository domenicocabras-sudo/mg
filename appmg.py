import streamlit as st
import imagehash
from PIL import Image
import os
import json

# Caricamento descrizioni
def load_desc():
    with open('descrizioni.json', 'r') as f:
        return json.load(f)

# Calcola hash della foto
def get_hash(image):
    return imagehash.phash(image)

st.title("📷 Riconoscitore Foto (Lightweight)")

# Caricamento database
if os.path.exists('descrizioni.json'):
    descrizioni = load_desc()
else:
    descrizioni = {}

uploaded_file = st.file_uploader("Carica una foto per il confronto...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img_test = Image.open(uploaded_file)
    st.image(img_test, caption='Foto caricata', width=300)
    
    if st.button("Confronta nel DB"):
        hash_test = get_hash(img_test)
        trovato = None
        min_dist = 100 # Soglia di tolleranza (più è alto, più è permissivo)
        
        # Scansione cartella database
        for filename in os.listdir('database_foto'):
            path = os.path.join('database_foto', filename)
            img_db = Image.open(path)
            hash_db = get_hash(img_db)
            
            # Calcolo distanza di Hamming (differenza tra hash)
            distanza = hash_test - hash_db
            
            if distanza < min_dist:
                min_dist = distanza
                trovato = filename
        
        if trovato and min_dist < 15: # Soglia di somiglianza
            st.success(f"Trovata corrispondenza: {trovato}")
            st.write(f"**Descrizione:** {descrizioni.get(trovato, 'Nessuna descrizione disponibile')}")
        else:
            st.warning("Nessuna immagine simile trovata nel database.")

