import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter
import os

st.set_page_config(layout="wide")

DB_FILE = "inventario_salvato.csv"

# --- INIZIALIZZAZIONE ---
if 'archivio_dati' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.archivio_dati = df.to_dict('records')
        except:
            st.session_state.archivio_dati = []
    else:
        st.session_state.archivio_dati = []

if 'casse_aperte' not in st.session_state:
    st.session_state.casse_aperte = ["Cassa 1"]

# --- FUNZIONI ---
def salva_su_disco():
    df = pd.DataFrame(st.session_state.archivio_dati)
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
        # Raggruppiamo i dati per cassa/codice per evitare ripetizioni
        # Assumendo che ogni blocco aggiunto sia un gruppo unico
        for entry in st.session_state.archivio_dati:
            # Scriviamo i dati comuni
            ws.write(row_idx, 0, "N/A", fmt) # Placeholder foto
            ws.write(row_idx, 1, entry.get('Cassa', ''), fmt)
            ws.write(row_idx, 2, entry.get('Data', ''), fmt)
            ws.write(row_idx, 3, entry.get('Codice', ''), fmt)
            ws.write(row_idx, 4, entry.get('Cliente', ''), fmt)
            ws.write(row_idx, 5, entry.get('Livello', ''), fmt)
            ws.write(row_idx, 6, entry.get('Pezzi', 0), fmt)
            ws.write(row_idx, 7, entry.get('Totale_Cassa', 0), fmt)
            row_idx += 1
            
    return output.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Archivio e Totali")
    totale = sum(item.get('Pezzi', 0) for item in st.session_state.archivio_dati)
    st.metric("Totale Pezzi Globale", totale)
    st.divider()
    if st.session_state.archivio_dati:
        st.download_button("📥 Scarica Report Excel", genera_excel(), "Inventario.xlsx")

# --- INTERFACCIA ---
st.title("Inventario Multi-Cassa")

if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        col_a, col_b, col_c = st.columns([1, 2, 2])
        num_cassa = col_a.text_input("Numero Cassa:", key=f"cassa_{i}")
        codice_articolo = col_b.text_input("Codice Articolo:", key=f"codice_{i}")
        nome_cliente = col_c.text_input("Nome Cliente:", key=f"cliente_{i}")

        cols = st.columns(4)
        input_data = []
        totale_cassa = 0
        for j in range(1, 5):
            q = cols[j-1].number_input(f"Quantità (Livello {j}):", min_value=0, key=f"q_{i}_{j}")
            if q > 0:
                input_data.append({"Livello": f"Livello {j}", "Pezzi": q})
                totale_cassa += q

        if st.button(f"Salva {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            # Qui scriviamo solo il primo livello con i dati completi
            # e i successivi con dati "vuoti" per evitare ripetizioni nel report
            for idx, det in enumerate(input_data):
                st.session_state.archivio_dati.append({
                    "Cassa": num_cassa if idx == 0 else "",
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M") if idx == 0 else "",
                    "Codice": codice_articolo if idx == 0 else "",
                    "Cliente": nome_cliente if idx == 0 else "",
                    "Livello": det["Livello"],
                    "Pezzi": det["Pezzi"],
                    "Totale_Cassa": totale_cassa if idx == 0 else ""
                })
            salva_su_disco()
            st.success("Dati salvati!")
            st.rerun()
