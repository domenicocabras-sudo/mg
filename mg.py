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

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Creazione tabella
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                  (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                   Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, Totale_Pezzi INTEGER, foto_bytes BLOB)''')
    
    # Patch per colonna Totale_Pezzi se il DB esiste già
    c.execute("PRAGMA table_info(inventario)")
    columns = [info[1] for info in c.fetchall()]
    if 'Totale_Pezzi' not in columns:
        c.execute("ALTER TABLE inventario ADD COLUMN Totale_Pezzi INTEGER DEFAULT 0")
        
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    c.execute("SELECT count(*) FROM configurazione")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI ---
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

# --- INTERFACCIA ---
col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("📦 Sistema Gestionale Inventario")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        add_cassa()
        st.rerun()

casse_attive = get_casse()
tabs = st.tabs(casse_attive)

for i, tab in enumerate(tabs):
    with tab:
        nome_cassa_corrente = casse_attive[i]
        with st.form(key=f"form_{i}", clear_on_submit=True):
            num_cassa = st.text_input("Numero Cassa:", value=nome_cassa_corrente)
            codice = st.text_input("Codice Articolo:")
            cliente = st.text_input("Nome Cliente:")
            foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
            cols = st.columns(4)
            quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
            submit_button = st.form_submit_button(label=f"Salva Dati {nome_cassa_corrente}")

        if submit_button:
            totale_pezzi = sum(quantita)
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foto_bytes = foto_upload.getvalue() if foto_upload else None
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for j, q in enumerate(quantita):
                if q > 0:
                    c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?,?)", 
                              (i, session_timestamp, num_cassa.upper(), codice.upper(), cliente.upper(), 
                               session_timestamp, f"L{j+1}", q, totale_pezzi, foto_bytes if j == 0 else None))
            conn.commit()
            conn.close()
            
            # Generazione QR Code
            dati_qr = f"Cassa:{num_cassa}|Art:{codice}|Tot:{totale_pezzi}"
            img = qrcode.make(dati_qr)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.session_state.last_qr = buf.getvalue()
            st.success("Dati salvati!")
            st.rerun()

        # Visualizzazione QR
        if st.session_state.get('last_qr'):
            st.image(st.session_state.last_qr, caption="QR Generato", width=150)
            st.download_button("Scarica QR", st.session_state.last_qr, "qrcode.png", "image/png")

        # Sidebar Download
        with st.sidebar:
            st.header(f"Archivio: {nome_cassa_corrente}")
            if st.button(f"🔄 Azzerare {nome_cassa_corrente}", key=f"reset_{i}"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                conn.commit()
                conn.close()
                st.rerun()

            dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
            if dati_filtrati:
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    hdr = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white'})
                    ws = wb.add_worksheet("Inventario")
                    ws.write_row(0, 0, ["FOTO", "DATA", "CODICE", "CLIENTE", "TOTALE PEZZI"], hdr)
                    
                    sessioni = sorted(list(set(d['session_id'] for d in dati_filtrati)))
                    row = 1
                    for sid in sessioni:
                        r = next((d for d in dati_filtrati if d['session_id'] == sid), None)
                        if r:
                            if r.get('foto_bytes'):
                                ws.insert_image(row, 0, 'f.jpg', {'image_data': io.BytesIO(r['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                            ws.write(row, 1, r['Data'])
                            ws.write(row, 2, r['Codice'])
                            ws.write(row, 3, r['Cliente'])
                            ws.write(row, 4, int(r['Totale_Pezzi'] or 0))
                            ws.set_row(row, 60)
                            row += 1
                st.download_button(f"📥 Scarica Excel {nome_cassa_corrente}", output.getvalue(), "Report.xlsx")
