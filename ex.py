import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "inventario.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONE DI INIZIALIZZAZIONE STATO ---
def setup_state():
    if 'casse_aperte' not in st.session_state:
        st.session_state['casse_aperte'] = ["Cassa 1"]

setup_state()

# --- INTERFACCIA ---
col_titolo, col_btn = st.columns([4, 1])
with col_titolo: 
    st.title("Inventario")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        nuovo_nome = f"Cassa {len(st.session_state['casse_aperte']) + 1}"
        st.session_state['casse_aperte'].append(nuovo_nome)
        st.rerun()

# Utilizziamo la lista dal session state
tabs = st.tabs(st.session_state['casse_aperte'])

for i, tab_name in enumerate(st.session_state['casse_aperte']):
    with tabs[i]:
        # Form per gestire i dati
        with st.form(key=f"form_{i}"):
            num_cassa = st.text_input("Numero Cassa:")
            codice = st.text_input("Codice Articolo:")
            cliente = st.text_input("Nome Cliente:")
            foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
            cols = st.columns(4)
            quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0) for j in range(4)]
            submit_button = st.form_submit_button(label=f"Salva Dati {tab_name}")

        if submit_button:
            # Salvataggio DB
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foto_bytes = foto_upload.getvalue() if foto_upload else None
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for j, q in enumerate(quantita):
                if q > 0:
                    c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                              (i, session_timestamp, num_cassa.upper(), codice.upper(), cliente.upper(), 
                               session_timestamp, f"L{j+1}", q, foto_bytes if j == 0 else None))
            conn.commit()
            conn.close()
            st.rerun()

        # Visualizzazione totale
        conn = sqlite3.connect(DB_FILE)
        dati_totali = pd.read_sql_query("SELECT * FROM inventario", conn).to_dict('records')
        conn.close()
        totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({tab_name})", totale_archiviato)

        # Sidebar e Download (mantenuto inalterato)
        # ... (restante logica di download invariata)
