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

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'
if 'last_qr' not in st.session_state:
    st.session_state.last_qr = None

# --- ROUTER ---
if st.session_state.pagina == 'home':
    st.title("📦 Sistema Gestionale Inventario")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()

else:
    # --- PAGINA INVENTARIO ---
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
        st.session_state.last_qr = None
        st.rerun()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.join(BASE_DIR, "inventario.db")

    def init_db():
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Aggiunta colonna Totale_Pezzi
        c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                     (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                      Cliente TEXT, Data TEXT, Totale_Pezzi INTEGER, foto_bytes BLOB)''')
        c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
        c.execute("SELECT count(*) FROM configurazione")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
        conn.commit()
        conn.close()

    init_db()

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

    def leggi_dal_db():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM inventario", conn)
        conn.close()
        return df.to_dict('records')

    # Visualizzazione QR Code
    if st.session_state.last_qr:
        st.success("Dati salvati!")
        st.image(st.session_state.last_qr, caption="QR Code Generato", width=150)
        st.download_button("Scarica QR", st.session_state.last_qr, "qrcode.png", "image/png")
        if st.button("Chiudi QR"):
            st.session_state.last_qr = None
            st.rerun()

    col_titolo, col_btn = st.columns([4, 1])
    with col_titolo: st.title("Inventario")
    with col_btn:
        if st.button("➕ Aggiungi Cassa"):
            add_cassa()
            st.rerun()

    casse_attive = get_casse()
    tabs = st.tabs(casse_attive)

    for i, tab in enumerate(tabs):
        with tab:
            with st.form(key=f"form_{i}", clear_on_submit=True):
                num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{i}")
                codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
                cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
                foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'], key=f"f_{i}")
                
                # Input per i 4 livelli (si sommano per il totale)
                cols = st.columns(4)
                q1 = cols[0].number_input("Q L1", min_value=0, key=f"q1_{i}")
                q2 = cols[1].number_input("Q L2", min_value=0, key=f"q2_{i}")
                q3 = cols[2].number_input("Q L3", min_value=0, key=f"q3_{i}")
                q4 = cols[3].number_input("Q L4", min_value=0, key=f"q4_{i}")
                
                submit_button = st.form_submit_button(label=f"Salva Dati {casse_attive[i]}")

            if submit_button:
                totale_pezzi = q1 + q2 + q3 + q4
                session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                foto_bytes = foto_upload.getvalue() if foto_upload else None
                
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?)", 
                             (i, session_timestamp, num_cassa.upper(), codice.upper(), 
                              cliente.upper(), session_timestamp, totale_pezzi, foto_bytes))
                conn.commit()
                conn.close()
                
                dati_qr = f"Cassa:{num_cassa}|Art:{codice}|Cli:{cliente}|Tot:{totale_pezzi}"
                qr = qrcode.make(dati_qr)
                qr_io = io.BytesIO()
                qr.save(qr_io, format='PNG')
                st.session_state.last_qr = qr_io.getvalue()
                st.rerun()

            with st.sidebar:
                st.header(f"Archivio: {casse_attive[i]}")
                if st.button(f"🔄 Azzerare {casse_attive[i]}", key=f"reset_{i}"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                    conn.commit()
                    conn.close()
                    st.rerun()

                dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
                if dati_filtrati:
                    output = io.BytesIO()
                    with xlsxwriter.Workbook(output) as wb:
                        fmt = wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                        hdr = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                        ws = wb.add_worksheet("Inventario")
                        # Colonne: FOTO, DATA, CODICE, CLIENTE, TOTALE PEZZI
                        headers = ["FOTO", "DATA", "CODICE", "CLIENTE", "TOTALE PEZZI"]
                        ws.write_row(0, 0, headers, hdr)
                        
                        for row, d in enumerate(dati_filtrati, 1):
                            if d['foto_bytes']:
                                ws.insert_image(row, 0, 'f.jpg', {'image_data': io.BytesIO(d['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                            ws.write(row, 1, d['Data'], fmt)
                            ws.write(row, 2, d['Codice'], fmt)
                            ws.write(row, 3, d['Cliente'], fmt)
                            ws.write(row, 4, d['Totale_Pezzi'], fmt)
                            ws.set_row(row, 60)
                    
                    st.download_button(f"📥 Scarica Excel {casse_attive[i]}", output.getvalue(), "Report.xlsx")
