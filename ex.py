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

def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

# --- INTERFACCIA ---
if 'casse_aperte' not in st.session_state: 
    st.session_state.casse_aperte = ["Cassa 1"]

# Layout Titolo e Bottone allineati
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("Inventario Multi-Cassa")
with col2:
    # Aggiunge spazio per allineare il bottone visivamente al titolo
    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
    if st.button("➕ Aggiungi Cassa", use_container_width=True):
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
        
        if st.button(f"💾 Salva Dati Cassa {i+1}", key=f"btn_{i}", use_container_width=True):
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
            st.rerun()

        # --- SIDEBAR E DOWNLOAD ---
        with st.sidebar:
            st.header(f"Gestione: {st.session_state.casse_aperte[i]}")
            dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
            
            if dati_filtrati:
                ultimo_codice = dati_filtrati[-1].get('Codice') or "SenzaCodice"
                nome_file = f"Report_{st.session_state.casse_aperte[i]}_{ultimo_codice}.xlsx"
                
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    ws = wb.add_worksheet("Inventario")
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
                
                st.download_button(label=f"📥 Scarica: {nome_file}", data=output.getvalue(), file_name=nome_file, use_container_width=True)

            if st.button(f"🔄 Reset {st.session_state.casse_aperte[i]}", key=f"reset_{i}", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                conn.commit()
                conn.close()
                st.rerun()
