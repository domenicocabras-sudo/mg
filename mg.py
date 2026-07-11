import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestione Inventario Pro", layout="wide")

# CSS Personalizzato per un look moderno
st.markdown("""
    <style>
    .main {background-color: #f5f7f9;}
    .stButton>button {width: 100%; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "inventario.db")

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

def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

# --- LANDING PAGE HEADER ---
st.title("📦 Sistema di Gestione Inventario")
st.markdown("---")
st.write("Benvenuto nel portale di gestione magazzino. Seleziona una cassa per inserire i dati o scaricare i report aggiornati.")

# --- INTERFACCIA PRINCIPALE ---
col_titolo, col_btn = st.columns([6, 1])
with col_btn:
    if st.button("➕ Nuova Cassa"):
        add_cassa()
        st.rerun()

casse_attive = get_casse()
tabs = st.tabs(casse_attive)

for i, tab in enumerate(tabs):
    with tab:
        st.subheader(f"Inserimento Dati - {casse_attive[i]}")
        with st.form(key=f"form_{i}", clear_on_submit=True):
            cols_input = st.columns(3)
            num_cassa = cols_input[0].text_input("Numero Cassa:")
            codice = cols_input[1].text_input("Codice Articolo:")
            cliente = cols_input[2].text_input("Nome Cliente:")
            foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
            
            st.write("Quantità per livello:")
            cols = st.columns(4)
            quantita = [cols[j].number_input(f"Livello {j+1}", min_value=0) for j in range(4)]
            submit_button = st.form_submit_button(label="🚀 Salva nel Database")

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
            st.success("Dati salvati con successo!")
            st.rerun()

        # Metriche
        dati_totali = leggi_dal_db()
        totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
        st.metric(f"Totale pezzi in {casse_attive[i]}", totale_archiviato)

        # --- SIDEBAR E DOWNLOAD ---
        with st.sidebar:
            st.header(f"⚙️ Impostazioni: {casse_attive[i]}")
            if st.button(f"🗑️ Resetta {casse_attive[i]}", key=f"reset_{i}"):
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
                    header_fmt = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                    cell_fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
                    alt_fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#F2F2F2'})
                    
                    ws = wb.add_worksheet("Inventario")
                    ws.set_column('A:A', 20); ws.set_column('B:G', 15)
                    ws.write_row(0, 0, ["FOTO", "CASSA", "CODICE", "CLIENTE", "DATA", "LIVELLO", "PEZZI"], header_fmt)
                    
                    last_session = None
                    row_idx = 1
                    for entry in dati_filtrati:
                        current_fmt = alt_fmt if row_idx % 2 == 0 else cell_fmt
                        if entry['session_id'] != last_session:
                            if entry.get('foto_bytes'):
                                ws.insert_image(row_idx, 0, 'foto.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                            ws.write(row_idx, 1, str(entry['Cassa']).upper(), current_fmt)
                            ws.write(row_idx, 2, str(entry['Codice']).upper(), current_fmt)
                            ws.write(row_idx, 3, str(entry['Cliente']).upper(), current_fmt)
                            ws.write(row_idx, 4, entry['Data'], current_fmt)
                        
                        ws.write(row_idx, 5, str(entry['Livello']).upper(), current_fmt)
                        ws.write(row_idx, 6, entry['Pezzi'], current_fmt)
                        ws.set_row(row_idx, 60)
                        last_session = entry['session_id']
                        row_idx += 1
                
                st.download_button(label="📥 Scarica Report Excel", data=output.getvalue(), file_name=nome_file)
