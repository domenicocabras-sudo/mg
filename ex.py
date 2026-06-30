import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'file_list' not in st.session_state: st.session_state.file_list = []
if 'archivio_dati' not in st.session_state: st.session_state.archivio_dati = []
if 'totale_globale' not in st.session_state: st.session_state.totale_globale = 0

# Sidebar
with st.sidebar:
    st.header("Archivio e Totali")
    st.metric("Totale Pezzi Globale", st.session_state.totale_globale)
    st.divider()
    for i, file_data in enumerate(st.session_state.file_list):
        st.download_button(f"Scarica Report Articolo {i+1}", file_data, f"Report_Cassa_{i+1}.xlsx")

st.title("Inventario")

# Input Dati
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
totale_cassa = 0

for i in range(1, 5):
    with cols[i-1]:
        q = st.number_input(f"Quantità (Livello {i}):", min_value=0, key=f"q_{i}_{st.session_state.reset_key}")
        if q > 0:
            input_data.append({"Livello": f"Livello {i}", "Pezzi": q})
            totale_cassa += q

st.metric("Totale Pezzi in questa Cassa", totale_cassa)
uploaded_file = st.file_uploader("Trascina Foto Articolo", type=['jpg', 'png', 'jpeg'], key=f"up_{st.session_state.reset_key}")

# Salvataggio
if uploaded_file and st.button("Conferma e Salva"):
    st.session_state.totale_globale += totale_cassa
    for det in input_data:
        st.session_state.archivio_dati.append({"Cassa": num_cassa, "Codice": codice_articolo, "Livello": det["Livello"], "Pezzi": det["Pezzi"]})
    
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        hdr = wb.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        
        # Larghezze colonne
        col_widths = [18, 12, 20, 15, 20, 15, 12, 15]
        for i, width in enumerate(col_widths): 
            ws.set_column(i, i, width)
        
        headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
        for i, h in enumerate(headers): 
            ws.write(0, i, h, hdr)
        
        num_rows = len(input_data)
        # Unione celle blocco
        ws.merge_range(1, 0, num_rows, 0, '', fmt)
        
        # Inserimento e centratura foto
        ws.insert_image(1, 0, "foto.jpg", {
            'image_data': io.BytesIO(uploaded_file.getvalue()), 
            'x_scale': 0.08, 'y_scale': 0.08,
            'x_offset': 25, 'y_offset': 10 
        })
        
        cols_merge = [1, 2, 3, 4, 7]
        vals = [num_cassa, datetime.now().strftime("%d/%m/%Y %H:%M"), codice_articolo, nome_cliente, totale_cassa]
        for idx, col in enumerate(cols_merge):
            ws.merge_range(1, col, num_rows, col, vals[idx], fmt)
            
        for i, det in enumerate(input_data):
            ws.write(1 + i, 5, det["Livello"], fmt)
            ws.write(1 + i, 6, det["Pezzi"], fmt)
            ws.set_row(1 + i, 60)
            
    st.session_state.file_list.append(output.getvalue())
    st.session_state.reset_key += 1
    st.rerun()

# Preview finale
st.write("---")
st.subheader("📋 Anteprima Dati")
if st.session_state.archivio_dati:
    st.dataframe(pd.DataFrame(st.session_state.archivio_dati), use_container_width=True)
else:
    st.info("Nessun dato inserito ancora.")
