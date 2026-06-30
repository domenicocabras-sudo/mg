import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")
st.title("📦 Inventario Rapido: Foto e Dati")

# 1. Input Dati
with st.container():
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    with col1:
        num_cassa = st.text_input("Numero Cassa:")
    with col2:
        codice_articolo = st.text_input("Codice Articolo:")
    with col3:
        nome_cliente = st.text_input("Nome Cliente:")
    with col4:
        num_pezzi = st.number_input("Pezzi:", min_value=0, step=1)
    with col5:
        livello = st.selectbox("Livello:", ["A", "B", "C", "D"])

# 2. Caricamento Foto (Supporta Drag & Drop)
uploaded_file = st.file_uploader("Trascina o carica la foto della cassa", type=['jpg', 'png', 'jpeg'])

if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio
if uploaded_file and st.button("Conferma e Salva in Lista"):
    img_bytes = uploaded_file.getvalue()
    st.session_state.inventario.append({
        "Cassa": num_cassa,
        "Data": datetime.now().strftime("%H:%M:%S"),
        "Codice": codice_articolo,
        "Cliente": nome_cliente,
        "Pezzi": num_pezzi,
        "Livello": livello,
        "Foto": img_bytes
    })
    st.success("Dati salvati!")

if st.session_state.inventario:
    df = pd.DataFrame(st.session_state.inventario)
    
    # 3. Calcolo Automatico Totali
    st.write("### 📊 Riepilogo Totali per Cassa e Livello")
    totali = df.groupby(['Cassa', 'Livello'])['Pezzi'].sum().reset_index()
    st.table(totali)

    # 4. Creazione Excel
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Pezzi", "Livello"]
    for i, h in enumerate(headers): worksheet.write(0, i, h)
    
    for row_num, item in enumerate(st.session_state.inventario, start=1):
        img_data = io.BytesIO(item["Foto"])
        worksheet.insert_image(row_num, 0, "foto.jpg", {'image_data': img_data, 'x_scale': 0.1, 'y_scale': 0.1})
        worksheet.set_row(row_num, 60)
        worksheet.write(row_num, 1, item["Cassa"])
        worksheet.write(row_num, 2, item["Data"])
        worksheet.write(row_num, 3, item["Codice"])
        worksheet.write(row_num, 4, item["Cliente"])
        worksheet.write(row_num, 5, item["Pezzi"])
        worksheet.write(row_num, 6, item["Livello"])
    
    workbook.close()
    st.download_button("📥 Scarica Excel Completo", output.getvalue(), "inventario.xlsx", "application/vnd.ms-excel")
