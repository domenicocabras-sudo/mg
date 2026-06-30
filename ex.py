import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")
st.title("📦 Inventario Rapido: Multi-Input")

# 1. Dati Generali
with st.container():
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a:
        num_cassa = st.text_input("Numero Cassa:")
    with col_b:
        codice_articolo = st.text_input("Codice Articolo:")
    with col_c:
        nome_cliente = st.text_input("Nome Cliente:")

st.write("---")

# 2. Input 4 campi quantità (Livello 1 - 4)
cols = st.columns(4)
input_data = []

for i in range(1, 5):
    with cols[i-1]:
        q = st.number_input(f"Quantità {i} (Livello {i}):", min_value=0, key=f"q_{i}")
        if q > 0:
            input_data.append({"Livello": f"Livello {i}", "Pezzi": q})

# 3. Caricamento Foto
uploaded_file = st.file_uploader("Trascina qui la foto della cassa", type=['jpg', 'png', 'jpeg'])

if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio
if uploaded_file and st.button("Conferma e Salva in Lista"):
    img_bytes = uploaded_file.getvalue()
    for entry in input_data:
        st.session_state.inventario.append({
            "Cassa": num_cassa,
            "Data": datetime.now().strftime("%H:%M:%S"),
            "Codice": codice_articolo,
            "Cliente": nome_cliente,
            "Livello": entry["Livello"],
            "Pezzi": entry["Pezzi"],
            "Foto": img_bytes
        })
    st.success("Dati salvati!")

# 4. Tabella e Download
if st.session_state.inventario:
    df = pd.DataFrame(st.session_state.inventario)
    st.write("### Riepilogo")
    st.table(df.drop(columns=['Foto']))

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi"]
    for i, h in enumerate(headers): worksheet.write(0, i, h)
    
    for row_num, item in enumerate(st.session_state.inventario, start=1):
        img_data = io.BytesIO(item["Foto"])
        worksheet.insert_image(row_num, 0, "foto.jpg", {'image_data': img_data, 'x_scale': 0.1, 'y_scale': 0.1})
        worksheet.set_row(row_num, 60)
        worksheet.write(row_num, 1, item["Cassa"])
        worksheet.write(row_num, 2, item["Data"])
        worksheet.write(row_num, 3, item["Codice"])
        worksheet.write(row_num, 4, item["Cliente"])
        worksheet.write(row_num, 5, item["Livello"])
        worksheet.write(row_num, 6, item["Pezzi"])
    
    workbook.close()
    st.download_button("📥 Scarica Excel", output.getvalue(), "inventario.xlsx")
