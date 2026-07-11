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
    # Aggiunta colonna Totale_Pezzi
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                  (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                   Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, Totale_Pezzi INTEGER, foto_bytes BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI ---
def leggi_dal_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventario", conn)
    conn.close()
    return df.to_dict('records')

# --- INTERFACCIA ---
# [ ... (omesso: resto del codice invariato per pulsanti Aggiungi Cassa, ecc.) ... ]

# NELLA LOGICA DI SALVATAGGIO (DENTRO submit_button):
if submit_button:
    # Calcolo totale pezzi della sessione
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
    st.rerun()

# NELLA LOGICA DI DOWNLOAD EXCEL:
dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
if dati_filtrati:
    output = io.BytesIO()
    with xlsxwriter.Workbook(output) as wb:
        header_fmt = wb.add_format({'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
        cell_fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        
        ws = wb.add_worksheet("Inventario")
        ws.set_column('A:E', 20)
        # Nuove colonne richieste
        ws.write_row(0, 0, ["FOTO", "DATA", "CODICE", "CLIENTE", "TOTALE PEZZI"], header_fmt)
        
        # Filtriamo le sessioni uniche per non duplicare le righe foto/totale
        sessioni_uniche = sorted(list(set(d['session_id'] for d in dati_filtrati)))
        
        row_idx = 1
        for sid in sessioni_uniche:
            riga = next((d for d in dati_filtrati if d['session_id'] == sid), None)
            if riga:
                # Foto
                if riga.get('foto_bytes'):
                    ws.insert_image(row_idx, 0, 'foto.jpg', {'image_data': io.BytesIO(riga['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                
                # Scrittura dati
                ws.write(row_idx, 1, riga['Data'], cell_fmt)
                ws.write(row_idx, 2, riga['Codice'], cell_fmt)
                ws.write(row_idx, 3, riga['Cliente'], cell_fmt)
                ws.write(row_idx, 4, riga['Totale_Pezzi'], cell_fmt) # Colonna Totale
                
                ws.set_row(row_idx, 60)
                row_idx += 1
    
    st.download_button(label=f"📥 Scarica Report Excel", data=output.getvalue(), file_name="Report_Inventario.xlsx")
