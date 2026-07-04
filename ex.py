import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter
import os

st.set_page_config(layout="wide")

# File per il salvataggio persistente
DB_FILE = "inventario_salvato.csv"

# --- CARICAMENTO DATI AL REFRESH ---
if 'archivio_dati' not in st.session_state:
    if os.path.exists(DB_FILE):
        # Se il file esiste, lo ricarichiamo nella sessione
        df = pd.read_csv(DB_FILE)
        st.session_state.archivio_dati = df.to_dict('records')
    else:
        st.session_state.archivio_dati = []

# --- INIZIALIZZAZIONE ALTRE VARIABILI ---
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]
if 'file_riepilogo' not in st.session_state: st.session_state.file_riepilogo = None

# Funzione per salvare su disco
def salva_su_disco():
    df = pd.DataFrame(st.session_state.archivio_dati)
    df.to_csv(DB_FILE, index=False)

# ... (Mantieni le tue funzioni genera_excel, ecc.) ...

# --- PARTE DEL CODICE DI SALVATAGGIO ---
        if uploaded_file and st.button(f"Conferma e Salva {st.session_state.casse_aperte[i]}"):
            # ... (tuo codice di inserimento in st.session_state.archivio_dati) ...
            
            # AGGIUNTA FONDAMENTALE:
            salva_su_disco()  # Salva il file ogni volta che aggiungi un pezzo
            
            st.session_state.file_riepilogo = genera_excel()
            st.success("Dati salvati in modo permanente!")
            st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Archivio e Totali")
    # Calcolo dinamico basato sui dati ricaricati dal CSV
    totale = sum(item['Pezzi'] for item in st.session_state.archivio_dati)
    st.metric("Totale Pezzi Globale", totale)
    # ... resto della sidebar ...
