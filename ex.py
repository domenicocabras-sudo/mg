import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
import qrcode # Import aggiunto
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "inventario.db")

# ... (funzioni init_db, get_casse, add_cassa, leggi_dal_db restano identiche) ...

# --- INTERFACCIA ---
# ... (codice per le tabs rimane uguale) ...

for i, tab in enumerate(tabs):
    with tab:
        with st.form(key=f"form_{i}", clear_on_submit=True):
            # ... (campi input come prima) ...
            submit_button = st.form_submit_button(label=f"Salva Dati {casse_attive[i]}")

        if submit_button:
            # ... (logica salvataggio DB esistente) ...
            
            # --- AGGIUNTA: GENERATORE QR CODE ---
            dati_qr = f"Cassa:{num_cassa}|Art:{codice}|Cli:{cliente}|Tot:{sum(quantita)}"
            img = qrcode.make(dati_qr)
            
            # Salvataggio QR in un buffer per mostrarlo
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.session_state.last_qr = buf.getvalue() # Salviamo nello stato
            st.success("Dati salvati e QR generato!")

        # Visualizzazione QR Code salvato
        if st.session_state.get('last_qr'):
            st.image(st.session_state.last_qr, caption="Ultimo QR Generato", width=150)
            st.download_button("Scarica QR", st.session_state.last_qr, "qrcode.png", "image/png")

        # ... (resto del codice per metriche e download Excel) ...
