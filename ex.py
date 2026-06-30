import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")
st.title("📦 Inventario Rapido: Report Ottimizzato")

# 1. Input Dati
with st.container():
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a:
        num_cassa = st.text_input("Numero Cassa:")
    with col_b:
        codice_articolo = st.text_input("Codice Articolo:")
    with col_c:
        nome_cliente = st.text_input("Nome Cliente:")

cols = st.columns(4)
input_data = []
totale_calcolato = 0

for i in range(1, 5):
    with cols[i-1]:
        q = st.number_input(f"Quantità (Livello {i}):", min_value=0, key=f"q_{i}")
        if q > 0:
            input_data.append({"Livello": f"Livello {i}", "Pezzi": q})
            totale_calcolato += q

st.metric("Totale Pezzi Inseriti", totale_calcolato)
uploaded_file = st.file_uploader("Trascina qui la foto della cassa", type=['jpg', 'png', 'jpeg'])

if 'inventario' not in st.session_state:
    st.session_state.inventario = []

if uploaded_file and st.button("Conferma e Salva in Lista"):
    # Salviamo l'intero blocco come una singola operazione
    st.session_state.inventario.append({
        "Cassa": num_cassa,
        "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Codice": codice_articolo,
        "Cliente": nome_cliente,
        "Totale": totale_calcolato,
        "Foto": uploaded_file.getvalue(),
        "Dettagli": input_data # Lista dei livelli e pezzi
    })
    st.success("Dati salvati!")

# 2. Creazione Excel
if st.session_state.inventario:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    # Formati
    header_format = workbook.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    
    # Intestazioni
    headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
    for i, h in enumerate(headers): worksheet.write(0, i, h, header_format)
    
    # Larghezza colonne
    col_widths = [20, 15, 20, 20, 20, 15, 15, 15]
    for i, width in enumerate(col_widths): worksheet.set_column(i, i, width)
    
    current_row = 1
    for item in st.session_state.inventario:
        start_row = current_row
        
        # Inserisci dati fissi solo una volta per cassa
        img_data = io.BytesIO(item["Foto"])
        worksheet.insert_image(start_row, 0, "f.jpg", {'image_data': img_data, 'x_scale': 0.08, 'y_scale': 0.08})
        
        worksheet.write(start_row, 1, item["Cassa"], cell_format)
        worksheet.write(start_row, 2, item["Data"], cell_format)
        worksheet.write(start_row, 3, item["Codice"], cell_format)
        worksheet.write(start_row, 4, item["Cliente"], cell_format)
        worksheet.write(start_row, 7, item["Totale"], cell_format)
        
        # Inserisci i dettagli (Livello/Pezzi)
        for det in item["Dettagli"]:
            worksheet.write(current_row, 5, det["Livello"], cell_format)
            worksheet.write(current_row, 6, det["Pezzi"], cell_format)
            worksheet.set_row(current_row, 60)
            current_row += 1

    workbook.close()
    st.download_button("📥 Scarica Report Excel Professionale", output.getvalue(), "Report_Inventario.xlsx")
