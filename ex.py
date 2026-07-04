import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
from datetime import datetime

st.set_page_config(layout="wide")
DB_FILE = "inventario.db"

# --- 1. GESTIONE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    conn.commit()
    conn.close()

init_db()

def carica_dati():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

def salva_nel_db(dati):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Inseriamo solo l'ultimo salvataggio
    for item in dati:
        c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                  (item['tab_index'], item['session_id'], item['Cassa'], item['Codice'], 
                   item['Cliente'], item['Data'], item['Livello'], item['Pezzi'], item['foto_bytes']))
    conn.commit()
    conn.close()

# --- 2. INTERFACCIA ---
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("Inventario Multi-Cassa (DB)")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
        st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        num_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'], key=f"foto_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        # Carica dati aggiornati dal DB
        archivio_corrente = carica_dati()
        totale_archiviato = sum(item['Pezzi'] for item in archivio_corrente if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({st.session_state.casse_aperte[i]})", totale_archiviato)
        
        if st.button(f"Salva Dati {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foto_bytes = foto_upload.getvalue() if foto_upload else None
            
            nuovi_dati = []
            for j, q in enumerate(quantita):
                if q > 0:
                    nuovi_dati.append({
                        "tab_index": i, "session_id": session_timestamp,
                        "Cassa": num_cassa, "Codice": codice, "Cliente": cliente, 
                        "Data": session_timestamp, "Livello": f"L{j+1}", "Pezzi": q,
                        "foto_bytes": foto_bytes if j == 0 else None
                    })
            salva_nel_db(nuovi_dati)
            st.rerun()

        # SIDEBAR (con lettura dal DB)
        with st.sidebar:
            st.header(f"Gestione: {st.session_state.casse_aperte[i]}")
            if st.button(f"🔄 Azzerare {st.session_state.casse_aperte[i]}", key=f"reset_{i}"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                conn.commit()
                conn.close()
                st.rerun()

            dati_filtrati = [d for d in carica_dati() if d.get('tab_index') == i]
            
            if dati_filtrati:
                # ... (Logica Excel rimane identica, legge dai dati_filtrati)
                # (omesso per brevità, usa il blocco che avevamo già definito sopra)
                st.success("Dati pronti per il download")
