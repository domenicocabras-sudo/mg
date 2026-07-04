import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter
import os

st.set_page_config(layout="wide")

DB_FILE = "inventario_salvato.csv"

# --- INIZIALIZZAZIONE E CARICAMENTO ---
if 'archivio_dati' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            # Forza la lettura come stringa per evitare errori di tipo
            df = pd.read_csv(DB_FILE, dtype=str)
            # Converte le colonne numeriche se necessario
            if 'Pezzi' in df.columns:
                df['Pezzi'] = pd.to_numeric(df['Pezzi'], errors='coerce').fillna(0).astype(int)
            st.session_state.archivio_dati = df.to_dict('records')
        except Exception as e:
            st.error(f"Errore nel caricamento dati: {e}")
            st.session_state.archivio_dati = []
    else:
        st.session_state.archivio_dati = []

if 'casse_aperte' not in st.session_state:
    st.session_state.casse_aperte = ["Cassa 1"]

# --- FUNZIONI ---
def salva_su_disco():
    # Escludiamo le foto dal salvataggio su CSV
    dati_per_csv = [{k: v for k, v in item.items() if k != 'foto_bytes'} for item in st.session_state.archivio_dati]
    df = pd.DataFrame(dati_per_csv)
    df.to_csv(DB_FILE, index=False)

def genera_excel():
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        hdr = wb.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        
        headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
        for i, h in enumerate(headers):
            ws.write(0, i, h, hdr)
        
        row_idx = 1
        for entry in st.session_state.archivio_dati:
            # Foto
            if entry.get('foto_bytes'):
                try:
                    # NOTA: Se la foto è stata caricata nella sessione corrente
                    ws.insert_image(row_idx, 0, "foto.jpg", {
                        'image_data': io.BytesIO(entry['foto_bytes']), 
                        'x_scale': 0.1, 'y_scale': 0.1
                    })
                except:
                    pass
            
            ws.write(row_idx, 1, str(entry.get('Cassa', '')), fmt)
            ws.write(row_idx, 2, str(entry.get('Data', '')), fmt)
            ws.write(row_idx, 3, str(entry.get('Codice', '')), fmt)
            ws.write(row_idx, 4, str(entry.get('Cliente', '')), fmt)
            ws.write(row_idx, 5, str(entry.get('Livello', '')), fmt)
            ws.write(row_idx, 6, int(entry.get('Pezzi', 0)), fmt)
            ws.write(row_idx, 7, str(entry.get('Totale_Cassa', '')), fmt)
            ws.set_row(row_idx, 60)
            row_idx += 1
    return output.getvalue()

# --- SIDEBAR E UI ---
# (Il resto del codice rimane identico, assicurati di usare i metodi sopra)
