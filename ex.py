import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato per il reset e archivio
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0
if 'file_list' not in st.session_state:
    st.session_state.file_list = []
if 'inventario_data' not in st.session_state:
    st.session_state.inventario_data = []

# Barra laterale per i download (sempre visibile)
with st.sidebar:
    st.header("📥 Archivio File")
    for i, file_data in enumerate(st.session_state.file_list):
        st.download_button(f"Scarica Report Cassa {i+1}", file_data, f"Report_Cassa_{i+1}.xlsx")

st.title("📦 Inventario Rapido: Reset Automatico")

# 1. Input Dati con chiavi dinamiche (per il reset)
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

st.metric("Totale Pezzi Inseriti", totale_calcolato)

# 2. Caricamento Foto
uploaded_file = st.file_uploader("Trascina qui la foto della cassa", type=['jpg', 'png', 'jpeg'], key=f"up_{st.session_state.reset_key}")

# 3. Salvataggio e Reset
if uploaded_file and st.button("Conferma e Salva"):
    # Creazione Excel Professionale
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    # Formati grafici
    header_format = workbook.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    
    # Intestazioni e larghezza
    headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
    for i, h in enumerate(headers): worksheet.write(0, i, h, header_format)
    worksheet.set_column(0, 7, 15)
    
    # Inserimento dati
    img_data = io.BytesIO(uploaded_file.getvalue())
    worksheet.insert_image(1, 0, "foto.jpg", {'image_data': img_data, 'x_scale': 0.08, 'y_scale': 0.08})
    worksheet.set_row(1, 60)
    
    row = 1
    for det in input_data:
        worksheet.write(row, 1, num_cassa, cell_format)
        worksheet.write(row, 2, datetime.now().strftime("%d/%m/%Y %H:%M"), cell_format)
        worksheet.write(row, 3, codice_articolo, cell_format)
        worksheet.write(row, 4, nome_cliente, cell_format)
        worksheet.write(row, 5, det["Livello"], cell_format)
        worksheet.write(row, 6, det["Pezzi"], cell_format)
        worksheet.write(row, 7, totale_calcolato, cell_format)
        row += 1
            
    workbook.close()
    
    # Aggiunta all'archivio della sidebar
    st.session_state.file_list.append(output.getvalue())
    st.success("Dati salvati!")
    
    # Incremento chiave per azzerare i campi
    st.session_state.reset_key += 1
    st.rerun()
