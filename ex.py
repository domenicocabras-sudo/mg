import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato
if 'archivio_dati' not in st.session_state: st.session_state.archivio_dati = []
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]
if 'file_riepilogo' not in st.session_state: st.session_state.file_riepilogo = None

# Funzione per generare l'Excel con le foto
def genera_excel_globale():
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Riepilogo")
        # ... (qui inseriresti la logica di formattazione che avevi già)
        # Per semplicità, qui mettiamo i dati:
        df = pd.DataFrame(st.session_state.archivio_dati)
        df.to_excel(writer, index=False) # Nota: con le foto dovrai mantenere la tua logica ws.insert_image
    return output.getvalue()

st.title("Gestione Inventario Multi-Cassa")

# Sidebar sempre presente per il download
with st.sidebar:
    st.header("📥 Download Dati")
    if st.session_state.file_riepilogo:
        st.download_button("Scarica Riepilogo Globale (Excel)", st.session_state.file_riepilogo, "Riepilogo_Totale.xlsx")
    else:
        st.info("Salva almeno una cassa per generare il file.")

# Gestione Tab
if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        # ... (i tuoi input text_input e number_input qui) ...
        uploaded_file = st.file_uploader(f"Foto {st.session_state.casse_aperte[i]}", type=['jpg', 'png'], key=f"up_{i}")
        
        if uploaded_file and st.button(f"Salva {st.session_state.casse_aperte[i]}", key=f"save_{i}"):
            # 1. Aggiungi dati all'archivio
            st.session_state.archivio_dati.append({...}) 
            
            # 2. RIGENERA IL FILE E SALVALO NELLO STATO
            st.session_state.file_riepilogo = genera_excel_globale()
            st.success("Dato salvato e file riepilogo aggiornato!")
            st.rerun()
