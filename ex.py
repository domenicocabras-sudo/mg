import streamlit as st
import io
from datetime import datetime
import xlsxwriter

# Impostazione pagina larga per ottimizzare lo spazio
st.set_page_config(layout="wide")
st.title("📸 Inventario Rapido: Foto e Dati")

# 1. Sezione di input su una riga
with st.container():
    col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1.5])
    with col1:
        codice_articolo = st.text_input("Codice Articolo:")
    with col2:
        nome_cliente = st.text_input("Nome Cliente:")
    with col3:
        num_pezzi = st.number_input("Pezzi:", min_value=0, step=1)
    with col4:
        livello = st.selectbox("Livello:", ["A", "B", "C", "D"])

# 2. Sezione Fotocamera
img_file_buffer = st.camera_input("Scatta una foto della cassa")

# 3. Gestione Inventario in memoria
if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio dati
if img_file_buffer and st.button("Conferma e Salva in Lista"):
    img_bytes = img_file_buffer.getvalue()
    
    nuova_riga = {
        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Codice": codice_articolo,
        "Cliente": nome_cliente,
        "Pezzi": num_pezzi,
        "Livello": livello,
        "Foto": img_bytes
    }
    st.session_state.inventario.append(nuova_riga)
    st.success("Dati salvati con successo!")

# 4. Visualizzazione tabella e download Excel
if st.session_state.inventario:
    st.write("### Riepilogo Inventario")
    
    # Creazione Excel
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Inventario")
    
    # Intestazioni (Foto per prima)
    headers = ["Foto", "Data", "Codice", "Cliente", "Pezzi", "Livello"]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)
    
    # Scrittura righe
    for row_num, item in enumerate(st.session_state.inventario, start=1):
        # Inserimento immagine nella prima colonna (0)
        img_data = io.BytesIO(item["Foto"])
        worksheet.insert_image(row_num, 0, "foto.jpg", {'image_data': img_data, 'x_scale': 0.15, 'y_scale': 0.15})
        
        # Impostazione altezza riga per la foto
        worksheet.set_row(row_num, 70)
        
        # Scrittura dati nelle colonne successive
        worksheet.write(row_num, 1, item["Data"])
        worksheet.write(row_num, 2, item["Codice"])
        worksheet.write(row_num, 3, item["Cliente"])
        worksheet.write(row_num, 4, item["Pezzi"])
        worksheet.write(row_num, 5, item["Livello"])
    
    workbook.close()
    
    st.download_button(
        label="📥 Scarica Excel con Foto",
        data=output.getvalue(),
        file_name="inventario_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
