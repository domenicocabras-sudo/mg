import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os

from datetime import datetime
# --- DEBUG PERCORSO ---
# Questo stampa nel terminale dove il sistema pensa di scrivere il file
DB_FILE = "inventario.db"
percorso_assoluto = os.path.abspath(DB_FILE)
print(f"\n--- DEBUG: Il database sta cercando di essere scritto qui: ---")
print(percorso_assoluto)
print(f"-----------------------------------------------------------\n")
# --- CONFIGURAZIONE ---
st.set_page_config(layout="wide")
DB_FILE = "inventario.db"

# --- 1. GESTIONE DATABASE (SQLite) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                  Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    conn.commit()
    conn.close()

# Inizializza il DB all'avvio
init_db()

# Funzione per leggere dal DB
def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

# --- 2. INTERFACCIA ---
if 'casse_aperte' not in st.session_state: 
    st.session_state.casse_aperte = ["Cassa 1"]

col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("Inventario Multi-Cassa")
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
        
        # Calcolo totale locale
        dati_totali = leggi_dal_db()
        totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({st.session_state.casse_aperte[i]})", totale_archiviato)
        
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
            st.success("Dati salvati nel database!")
            st.rerun()

        # --- 3. SIDEBAR E DOWNLOAD ---
        with st.sidebar:
            st.header(f"Archivio: {st.session_state.casse_aperte[i]}")
            
            if st.button(f"🔄 Azzerare {st.session_state.casse_aperte[i]}", key=f"reset_{i}"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                conn.commit()
                conn.close()
                st.rerun()

            dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
            if dati_filtrati:
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    ws = wb.add_worksheet("Inventario")
                    ws.set_column('A:G', 15)
                    ws.write_row(0, 0, ["Foto", "Cassa", "Codice", "Cliente", "Data", "Livello", "Pezzi"])
                    
                    last_session = None
                    for r, entry in enumerate(dati_filtrati, 1):
                        if entry.get('foto_bytes'):
                            ws.insert_image(r, 0, 'foto.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                        
                        if entry['session_id'] != last_session:
                            ws.write_row(r, 1, [entry['Cassa'], entry['Codice'], entry['Cliente'], entry['Data'], entry['Livello'], entry['Pezzi']])
                        else:
                            ws.write(r, 5, entry['Livello'])
                            ws.write(r, 6, entry['Pezzi'])
                        last_session = entry['session_id']
                        ws.set_row(r, 60)
                
                st.download_button(
                    label=f"📥 Scarica Report {st.session_state.casse_aperte[i]}", 
                    data=output.getvalue(), 
                    file_name=f"Report_{st.session_state.casse_aperte[i]}.xlsx"
                )
