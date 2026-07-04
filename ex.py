import streamlit as st
import pandas as pd
import io
import xlsxwriter
import os

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. GESTIONE ARCHIVIO ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        try:
            st.session_state.archivio_dati = pd.read_csv(DB_FILE).to_dict('records')
        except: pass

def salva_su_disco():
    pd.DataFrame(st.session_state.archivio_dati).to_csv(DB_FILE, index=False)

# --- 2. INTERFACCIA ---
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

st.title("Inventario Multi-Cassa")

if st.sidebar.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        # Campi di input
        num_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        
        # Quantità L1-L4
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        # --- IL CONTATORE PARTE DA ZERO ---
        # Sommiamo i pezzi già archiviati per questa tab (indice 'i')
        totale_archiviato = sum(item['Pezzi'] for item in st.session_state.archivio_dati if item.get('tab_index') == i)
        
        # Il totale visualizzato è la somma di quanto inserito ORA + quanto già salvato
        totale_corrente = sum(quantita) + totale_archiviato
        
        st.metric("Totale pezzi in questa cassa", totale_corrente)
        
        if st.button(f"Salva Dati Cassa {i+1}", key=f"btn_{i}"):
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, 
                        "Cassa": num_cassa, "Codice": codice, 
                        "Cliente": cliente, "Livello": f"L{j+1}", "Pezzi": q
                    })
            salva_su_disco()
            st.rerun()

# --- 3. SIDEBAR (REPORT) ---
with st.sidebar:
    st.header("Esporta Dati")
    if st.session_state.archivio_dati:
        output = io.BytesIO()
        with xlsxwriter.Workbook(output) as wb:
            ws = wb.add_worksheet("Inventario")
            for r, entry in enumerate(st.session_state.archivio_dati, 1):
                ws.write(r, 0, str(entry.get('Cassa', '')))
                ws.write(r, 1, str(entry.get('Codice', '')))
                ws.write(r, 2, entry.get('Pezzi', 0))
        
        st.download_button("📥 Scarica Report Excel", output.getvalue(), "Inventario.xlsx")
