import streamlit as st
import pandas as pd
import io
import xlsxwriter
import os

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. CARICAMENTO DATI ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        try:
            st.session_state.archivio_dati = pd.read_csv(DB_FILE).to_dict('records')
        except: pass

def salva():
    pd.DataFrame(st.session_state.archivio_dati).to_csv(DB_FILE, index=False)

def genera_excel():
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        for r, entry in enumerate(st.session_state.archivio_dati, 1):
            ws.write(r, 0, str(entry.get('Cassa', '')))
            ws.write(r, 1, str(entry.get('Codice', '')))
            ws.write(r, 2, entry.get('Livello', ''))
            ws.write(r, 3, entry.get('Pezzi', 0))
    return output.getvalue()

# --- 2. INTERFACCIA ---
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

tabs = st.tabs(st.session_state.casse_aperte)

# Variabile per il totale della cassa selezionata
totale_cassa_attiva = 0

for i, tab in enumerate(tabs):
    with tab:
        # Campi input con key univoche per mantenere il valore
        id_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        # FILTRO CRITICO: Totale = (Input correnti) + (Dati salvati con lo stesso index 'i')
        totale_input = sum(quantita)
        totale_archivio = sum(d['Pezzi'] for d in st.session_state.archivio_dati if d.get('tab_index') == i)
        
        totale_cassa_attiva = totale_input + totale_archivio
        st.metric("Totale pezzi in questa cassa", totale_cassa_attiva)

        if st.button(f"Salva Dati Cassa {i+1}", key=f"btn_{i}"):
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, 
                        "Cassa": id_cassa, 
                        "Codice": codice, 
                        "Livello": f"L{j+1}", 
                        "Pezzi": q
                    })
            salva()
            st.rerun()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Gestione Dati")
    if st.button("➕ Aggiungi Nuova Cassa"):
        st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
        st.rerun()
    
    st.divider()
    if st.session_state.archivio_dati:
        st.download_button("📥 Scarica Report Excel", genera_excel(), "Inventario.xlsx")
