import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato per il reset
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0
if 'file_list' not in st.session_state:
    st.session_state.file_list = []

# Barra laterale per i download
with st.sidebar:
    st.header(" Archivio File")
    for i, file_data in enumerate(st.session_state.file_list):
        st.download_button(f"Scarica Report Cassa {i+1}", file_data, f"Report_Cassa_{i+1}.xlsx")

st.title(" Inventario ")

# Usiamo la chiave 'reset_key' per forzare il refresh dei campi
with st.container():
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a:
        num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{st.session_state.reset_key}")
    with col_b:
        codice_articolo = st.text_input("Codice Articolo:", key=f"codice_{st.session_state.reset_key}")
    with col_c:
        nome_cliente = st.text_input("Nome Cliente:", key=f"cliente_{st.session_state.reset_key}")

cols = st.columns(4)
input_data = []
totale_calcolato = 0

for i in range(1, 5):
    with cols[i-1]:
        q = st.number_input(f"Quantità (Livello {i}):", min_value=0, key=f"q_{i}_{st.session_state.reset_key}")
        if q > 0:
            input_data.append({"Livello": f"Livello {i}", "Pezzi": q})
            totale_calcolato += q

uploaded_file = st.file_uploader("Trascina qui la foto della cassa", type=['jpg', 'png', 'jpeg'], key=f"up_{st.session_state.reset_key}")

# Salvataggio
if uploaded_file and st.button("Conferma e Salva"):
    # ... (Logica di creazione file Excel identica alla precedente) ...
    
    # Esempio di salvataggio semplificato per il file
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet()
        ws.write(0, 0, "Cassa"); ws.write(0, 1, num_cassa)
    
    st.session_state.file_list.append(output.getvalue())
    st.success("Dati salvati!")
    
    # Incrementiamo il contatore: questo cambia i 'key' di tutti i campi, azzerandoli!
    st.session_state.reset_key += 1
    st.rerun()
