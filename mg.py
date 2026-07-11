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

if 'pagina' not in st.session_state: 
    st.session_state.pagina = 'home'

# --- FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                  (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                   Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    c.execute("SELECT count(*) FROM configurazione")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
    conn.commit()
    conn.close()

def get_casse():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT nome_cassa FROM configurazione", conn)
    conn.close()
    return df['nome_cassa'].tolist()

def add_cassa():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO configurazione VALUES (?)", (f"Cassa {len(get_casse()) + 1}",))
    conn.commit()
    conn.close()

def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

init_db()

# --- ROUTER ---
if st.session_state.pagina == 'home':
    st.title("📦 Sistema Gestionale")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()

else:
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
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
                num_cassa = st.text_input("Numero Cassa:", key=f"c_{i}")
                codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
                cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
                foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'], key=f"f_{i}")
                cols = st.columns(4)
                quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
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
                
                # QR CODE
                dati_qr = f"Cassa:{num_cassa}|Cod:{codice}|Cli:{cliente}"
                qr = qrcode.make(dati_qr)
                qr_buf = io.BytesIO()
                qr.save(qr_buf, format="PNG")
                st.image(qr_buf.getvalue(), caption="QR Code Generato", width=150)
                st.download_button("Scarica QR", qr_buf.getvalue(), "qr.png")
                st.rerun()

            # METRICHE
            dati_totali = leggi_dal_db()
            totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
            st.metric(f"Totale pezzi salvati ({casse_attive[i]})", totale_archiviato)

            # SIDEBAR E EXPORT
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
                    ultimo_codice = dati_filtrati[-1].get('Codice') or "SenzaCodice"
                    nome_file = f"Report_{casse_attive[i]}_{ultimo_codice}.xlsx".upper()
                    output = io.BytesIO()
                    
                    with xlsxwriter.Workbook(output) as wb:
                        hdr = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                        fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
                        alt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#F2F2F2'})
                        ws = wb.add_worksheet("Inventario")
                        ws.set_column('A:A', 20)
                        ws.write_row(0, 0, ["FOTO", "CASSA", "CODICE", "CLIENTE", "DATA", "LIVELLO", "PEZZI"], hdr)
                        
                        last_session = None
                        row = 1
                        for entry in dati_filtrati:
                            f = alt if row % 2 == 0 else fmt
                            if entry['session_id'] != last_session:
                                if entry.get('foto_bytes'):
                                    ws.insert_image(row, 0, 'f.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                                ws.write(row, 1, str(entry['Cassa']), f)
                                ws.write(row, 2, str(entry['Codice']), f)
                                ws.write(row, 3, str(entry['Cliente']), f)
                                ws.write(row, 4, str(entry['Data']), f)
                            ws.write(row, 5, str(entry['Livello']), f)
                            ws.write(row, 6, entry['Pezzi'], f)
                            ws.set_row(row, 60)
                            last_session = entry['session_id']
                            row += 1
                    
                    st.download_button(f"📥 Scarica {nome_file}", output.getvalue(), file_name=nome_file)
