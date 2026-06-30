import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Barra laterale per i download
with st.sidebar:
    st.header("📥 Archivio File")
    if 'file_list' not in st.session_state:
        st.session_state.file_list = []
    
    for i, file_data in enumerate(st.session_state.file_list):
        st.download_button(f"Scarica Report {i+1}", file_data, f"Report_{i+1}.xlsx")

st.title("📦 Inventario Rapido: Reset e Archivio")

# 1. Input Dati
with st.container():
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a:
        num_cassa = st.text_input("Numero Cassa:", key="cassa")
    with col_b:
        codice_articolo = st.text_input("Codice Articolo:", key="codice")
    with col_c:
        nome_cliente = st.text_input("Nome Cliente:", key="cliente")

cols = st.columns(4)
input_data = []
totale_calcolato = 0

for i in range(1, 5):
    with cols[i-1]:
        q = st.number_input(f"Quantità (Livello {i}):", min_value=0, key=f"q_{i}")
        if q > 0:
            input_data.append({"Livello": f"Livello {i}", "Pezzi": q})
            totale_calcolato += q

uploaded_file = st.file_uploader("Trascina qui la foto della cassa", type=['jpg', 'png', 'jpeg'])

if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio
if uploaded_file and st.button("Conferma e Salva"):
    st.session_state.inventario.append({
        "Cassa": num_cassa, "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Codice": codice_articolo, "Cliente": nome_cliente,
        "Totale": totale_calcolato, "Foto": uploaded_file.getvalue(),
        "Dettagli": input_data
    })
    
    # Generazione Excel immediata per la sidebar
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet()
        # ... (stessa logica di scrittura vista in precedenza) ...
        # (Per brevità ho omesso la formattazione, la inserisci come prima)
        ws.write(0, 0, "Cassa"); ws.write(0, 1, num_cassa) 
        
    st.session_state.file_list.append(output.getvalue())
    st.success("Dati salvati!")
    
    # RESET: Ricarica la pagina per azzerare i campi
    st.rerun()

st.write("### Riepilogo in corso")
if st.session_state.inventario:
    st.table(pd.DataFrame(st.session_state.inventario).drop(columns=['Foto', 'Dettagli']))
