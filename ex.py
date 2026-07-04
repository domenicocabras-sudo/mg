import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
from datetime import datetime

# --- CONFIGURAZIONE DATABASE ---
DB_FILE = "inventario.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(layout="wide")
st.title("Inventario Multi-Cassa")

# --- STATO SESSIONE ---
if 'casse_aperte' not in st.session_state:
    st.session_state.casse_aperte = ["Cassa 1"]

# --- INTERFACCIA ---
col_titolo, col_btn = st.columns([4, 1])
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
        
        if st.button(f"Salva Dati {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foto_bytes = foto_upload.getvalue() if foto_upload else None
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for j, q in enumerate(quantita):
                if q > 0:
                    c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                              (i, session_timestamp, num_cassa, codice, cliente, 
                               session_timestamp, f"L{j+1}", q, foto_bytes if j == 0 else None))
            conn.commit()
            conn.close()
            st.success("Salvato!")

        # --- SIDEBAR DOWNLOAD ---
        with st.sidebar:
            st.header(f"Gestione: {st.session_state.casse_aperte[i]}")
            
            conn = sqlite3.connect(DB_FILE)
            df_cassa = pd.read_sql_query("SELECT * FROM inventario WHERE tab_index = ?", conn, params=(i,))
            conn.close()
            
            if not df_cassa.empty:
                nome_file = f"Report_{st.session_state.casse_aperte[i]}.xlsx"
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    ws = wb.add_worksheet("Inventario")
                    headers = ["Foto", "Cassa", "Codice", "Cliente", "Data", "Livello", "Pezzi"]
                    ws.write_row(0, 0, headers)
                    for r, row in enumerate(df_cassa.to_dict('records'), 1):
                        ws.write_row(r, 1, [row['Cassa'], row['Codice'], row['Cliente'], 
                                           row['Data'], row['Livello'], row['Pezzi']])
                
                st.download_button(f"📥 Scarica {nome_file}", data=output.getvalue(), file_name=nome_file)
                
                if st.button(f"🔄 Reset {st.session_state.casse_aperte[i]}", key=f"reset_{i}"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                    conn.commit()
                    conn.close()
                    st.rerun()
