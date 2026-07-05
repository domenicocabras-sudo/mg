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
    # Tabella inventario
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    # Tabella per salvare le casse aperte (Persistenza reale)
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    # Inizializza con Cassa 1 se vuoto
    c.execute("SELECT count(*) FROM configurazione")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI DATABASE ---
def get_casse():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT nome_cassa FROM configurazione", conn)
    conn.close()
    return df['nome_cassa'].tolist()

def add_cassa():
    conn = sqlite3.connect(DB_FILE)
    nuovo_nome = f"Cassa {len(get_casse()) + 1}"
    conn.execute("INSERT INTO configurazione VALUES (?)", (nuovo_nome,))
    conn.commit()
    conn.close()

# --- INTERFACCIA ---
col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("Inventario")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        add_cassa()
        st.rerun()

# Leggiamo le casse dal DB (Persistenza totale)
casse_attive = get_casse()
tabs = st.tabs(casse_attive)

for i, tab in enumerate(tabs):
    with tab:
        with st.form(key=f"form_{i}", clear_on_submit=True):
            num_cassa = st.text_input("Numero Cassa:")
            codice = st.text_input("Codice Articolo:")
            cliente = st.text_input("Nome Cliente:")
            foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
            cols = st.columns(4)
            quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0) for j in range(4)]
            submit_button = st.form_submit_button(label=f"Salva Dati {casse_attive[i]}")

        if submit_button:
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

        # Visualizzazione totale e Sidebar (mantenuta come nel tuo ultimo codice funzionante)
        # ... (restante logica di visualizzazione e download come da te richiesto)
