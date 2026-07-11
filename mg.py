import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
import qrcode
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "inventario.db")

if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
if 'last_qr' not in st.session_state: st.session_state.last_qr = None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                  (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                   Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    c.execute("SELECT count(*) FROM configurazione")
    if c.fetchone()[0] == 0: c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI ---
def get_casse():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT nome_cassa FROM configurazione", conn)
    conn.close()
    return df['nome_cassa'].tolist()

def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

# --- LOGICA PAGINE ---
if st.session_state.pagina == 'home':
    st.title("📦 Sistema Gestionale")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()
else:
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
        st.session_state.last_qr = None
        st.rerun()

    if st.session_state.last_qr:
        st.image(st.session_state.last_qr, caption="Ultimo QR Generato", width=150)

    # --- CODICE INVENTARIO ORIGINALE ---
    col_titolo, col_btn = st.columns([4, 1])
    with col_titolo: st.title("Inventario")
    with col_btn:
        if st.button("➕ Aggiungi Cassa"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO configurazione VALUES (?)", (f"Cassa {len(get_casse()) + 1}",))
            conn.commit()
            conn.close()
            st.rerun()

    casse_attive = get_casse()
    tabs = st.tabs(casse_attive)

    for i, tab in enumerate(tabs):
        with tab:
            with st.form(key=f"form_{i}", clear_on_submit=True):
                num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{i}")
                codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
                cliente = st.text_input("Nome Cliente:", key=f"clie_{i}")
                foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'], key=f"foto_{i}")
                cols = st.columns(4)
                quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
                submit_button = st.form_submit_button(label="Salva Dati")

            if submit_button:
                session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                foto_bytes = foto_upload.getvalue() if foto_upload else None
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for j, q in enumerate(quantita):
                    if q > 0:
                        c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                                  (i, session_id, num_cassa.upper(), codice.upper(), cliente.upper(), 
                                   session_id, f"L{j+1}", q, foto_bytes if j == 0 else None))
                conn.commit()
                conn.close()
                # Generazione QR
                qr = qrcode.make(f"Cassa:{num_cassa}|Art:{codice}")
                buf = io.BytesIO()
                qr.save(buf, format="PNG")
                st.session_state.last_qr = buf.getvalue()
                st.rerun()

            # --- REPORT EXCEL ORIGINALE ---
            dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
            if dati_filtrati:
                ultimo_codice = dati_filtrati[-1].get('Codice', 'REPORT')
                nome_file = f"Report_{casse_attive[i]}_{ultimo_codice}.xlsx".upper()
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    header_fmt = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1})
                    cell_fmt = wb.add_format({'align': 'center', 'border': 1})
                    ws = wb.add_worksheet("Inventario")
                    ws.write_row(0, 0, ["FOTO", "CASSA", "CODICE", "CLIENTE", "DATA", "LIVELLO", "PEZZI"], header_fmt)
                    
                    for row_idx, entry in enumerate(dati_filtrati, 1):
                        if entry.get('foto_bytes'):
                            ws.insert_image(row_idx, 0, 'f.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                        ws.write(row_idx, 1, str(entry['Cassa']), cell_fmt)
                        ws.write(row_idx, 2, str(entry['Codice']), cell_fmt)
                        ws.write(row_idx, 3, str(entry['Cliente']), cell_fmt)
                        ws.write(row_idx, 4, str(entry['Data']), cell_fmt)
                        ws.write(row_idx, 5, str(entry['Livello']), cell_fmt)
                        ws.write(row_idx, 6, entry['Pezzi'], cell_fmt)
                        ws.set_row(row_idx, 60)
                
                st.download_button(f"📥 Scarica {nome_file}", output.getvalue(), file_name=nome_file)
