import streamlit as st
import pandas as pd
import sqlite3
import io
import qrcode
from datetime import datetime
import os

# Configurazione
st.set_page_config(layout="wide")
DB_FILE = "inventario.db"

# Inizializzazione Session State
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'

# --- FUNZIONI ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- PAGINE ---
def pagina_home():
    st.title("📦 Sistema Gestionale")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()

def pagina_inventario():
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
        st.rerun()

    st.title("Inventario")
    
    # Esempio semplificato di inserimento
    with st.form("form_inventario"):
        cassa = st.text_input("Cassa")
        codice = st.text_input("Codice")
        cliente = st.text_input("Cliente")
        pezzi = st.number_input("Pezzi", min_value=0)
        submitted = st.form_submit_button("Salva")
        
        if submitted:
            st.success("Salvato!")
            # Generazione QR
            dati = f"Cassa:{cassa}|Cod:{codice}|Cli:{cliente}"
            qr = qrcode.make(dati)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue())
            st.download_button("Scarica QR", buf.getvalue(), "qr.png", "image/png")

# --- ROUTER ---
if st.session_state.pagina == 'home':
    pagina_home()
else:
    pagina_inventario()
