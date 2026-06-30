import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")
st.title("📦 Inventario Rapido con Totali")

# 1. Input Dati
with st.container():
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a:
        num_cassa = st.text_input("Numero Cassa:")
    with col_b:
        codice_articolo = st.text_input("Codice Articolo:")
    with col_c:
        nome_cliente = st.text_input("Nome Cliente:")

st.write("---")

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

# 2. Caricamento Foto
uploaded_file = st.file_uploader("Trascina o carica foto cassa", type=['jpg', 'png', 'jpeg'])

if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio
if uploaded_file and st.button("Conferma e Salva in Lista"):
    img_bytes = uploaded_file.getvalue()
    for entry in input_data:
        st.session_state.inventario.append({
            "Cassa": num_cassa,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Codice": codice_articolo,
            "Cliente": nome_cliente,
            "Livello": entry["Livello"],
            "Pezzi": entry["Pezzi"],
            "Totale_Pezzi": totale_calcolato,
            "Foto": img_bytes
        })
    st.success("Dati salvati!")

# 3. Download Excel "Graficamente Bello"
if st.session_state.inventario:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    # Formati grafici
    header_format = workbook.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
    
    headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
    for i, h in enumerate(headers): worksheet.write(0, i, h, header_format)
    
    for row_num, item in enumerate(st.session_state.inventario, start=1):
        img_data = io.BytesIO(item["Foto"])
        worksheet.insert_image(row_num, 0, "foto.jpg", {'image_data': img_data, 'x_scale': 0.08, 'y_scale': 0.08})
        worksheet.set_row(row_num, 60)
        
        data = [item["Cassa"], item["Data"], item["Codice"], item["Cliente"], item["Livello"], item["Pezzi"], item["Totale_Pezzi"]]
        for col_idx, val in enumerate(data):
            worksheet.write(row_num, col_idx + 1, val, cell_format)
            
    workbook.close()
    st.download_button("📥 Scarica Report Excel Professionale", output.getvalue(), "Report_Inventario.xlsx")
