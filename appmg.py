import streamlit as st
import os
from PIL import Image

# Configurazione della pagina
st.set_page_config(page_title="La mia App Cloud", layout="wide")

# 1. Definiamo la cartella dove sono le foto nel repository GitHub
IMAGE_FOLDER = "images"

st.title("La mia App su Streamlit Cloud ☁️")
st.write("Questa app legge le foto dalla cartella 'images' del repository.")

# 2. Funzione per caricare le immagini
def load_image(image_name):
    """Carica un'immagine dalla cartella definita, gestendo gli errori."""
    path = os.path.join(IMAGE_FOLDER, image_name)
    
    # Verifica che il file esista realmente
    if os.path.exists(path):
        try:
            return Image.open(path)
        except Exception as e:
            st.error(f"Impossibile aprire l'immagine {image_name}: {e}")
            return None
    else:
        st.error(f"Errore: Il file '{image_name}' non esiste nella cartella '{IMAGE_FOLDER}/'.")
        return None

# 3. Esempio di visualizzazione
# Sostituisci 'foto1.jpg' con il nome reale di una tua foto caricata
nome_foto = "foto1.jpg" 
st.subheader(f"Anteprima: {nome_foto}")

img = load_image(nome_foto)

if img:
    st.image(img, caption="Ecco la tua foto dal cloud!", use_container_width=True)
else:
    st.warning("Carica almeno una foto chiamata 'foto1.jpg' nella cartella 'images' su GitHub per vedere l'anteprima.")

# 4. (Opzionale) Lista automatica di tutte le foto nella cartella
st.divider()
st.subheader("Galleria automatica")
if os.path.exists(IMAGE_FOLDER):
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if files:
        cols = st.columns(3) # Crea 3 colonne per la galleria
        for i, file in enumerate(files):
            img = load_image(file)
            if img:
                cols[i % 3].image(img, caption=file, use_container_width=True)
    else:
        st.write("La cartella 'images' è vuota o non contiene immagini valide.")
