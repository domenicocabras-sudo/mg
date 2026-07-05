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

col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("Inventario")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
        st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        # Usiamo un FORM per evitare che i dati vadano persi durante il refresh
        with st.form(key=f"form_{i}", clear_on_submit=True):
            num_cassa = st.text_input("Numero Cassa:")
            codice = st.text_input("Codice Articolo:")
            cliente = st.text_input("Nome Cliente:")
            foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
            
            cols = st.columns(4)
            quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0) for j in range(4)]
            
            submit_button = st.form_submit_button(label=f"Salva Dati {st.session_state.casse_aperte[i]}")

        # Logica di salvataggio dopo il submit
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

        # Visualizzazione totale
        dati_totali = leggi_dal_db()
        totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({st.session_state.casse_aperte[i]})", totale_archiviato)

        # --- SIDEBAR E DOWNLOAD ---
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
                ultimo_codice = dati_filtrati[-1].get('Codice') or "SenzaCodice"
                nome_file = f"Report_{st.session_state.casse_aperte[i]}_{ultimo_codice}.xlsx".upper()
                
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    header_fmt = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                    cell_fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
                    alt_fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#F2F2F2'})
                    
                    ws = wb.add_worksheet("Inventario")
                    ws.set_column('A:A', 20)
                    ws.set_column('B:G', 15)
                    ws.write_row(0, 0, ["FOTO", "CASSA", "CODICE", "CLIENTE", "DATA", "LIVELLO", "PEZZI"], header_fmt)
                    
                    last_session = None
                    row_idx = 1
                    for entry in dati_filtrati:
                        current_fmt = alt_fmt if row_idx % 2 == 0 else cell_fmt
                        if entry.get('foto_bytes'):
                            ws.insert_image(row_idx, 0, 'foto.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                        
                        if entry['session_id'] != last_session:
                            ws.write_row(row_idx, 1, [str(entry['Cassa']).upper(), str(entry['Codice']).upper(), str(entry['Cliente']).upper(), entry['Data'], str(entry['Livello']).upper(), entry['Pezzi']], current_fmt)
                        else:
                            ws.write(row_idx, 5, str(entry['Livello']).upper(), current_fmt)
                            ws.write(row_idx, 6, entry['Pezzi'], current_fmt)
                        ws.set_row(row_idx, 60)
                        last_session = entry['session_id']
                        row_idx += 1
                
                st.download_button(label=f"📥 Scarica {nome_file}", data=output.getvalue(), file_name=nome_file)
