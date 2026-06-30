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

# Sidebar: Archivio e Totale Globale
with st.sidebar:
    st.header("📊 Archivio e Totali")
    st.metric("Totale Pezzi Globale", st.session_state.totale_globale)
    st.divider()
    # Mostriamo solo l'ultimo file generato per semplicità, o puoi scorrere la lista
    for i, file_data in enumerate(st.session_state.file_list):
        st.download_button(f"Scarica Report Cassa {i+1}", file_data, f"Report_Cassa_{i+1}.xlsx")

st.title("📦 Inventario Rapido: Report e Anteprima")

# 1. Input Dati
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
uploaded_file = st.file_uploader("Trascina foto cassa", type=['jpg', 'png', 'jpeg'], key=f"up_{st.session_state.reset_key}")

# 2. Salvataggio
if uploaded_file and st.button("Conferma e Salva"):
    # Aggiorna totale globale
    st.session_state.totale_globale += totale_cassa
    
    # Salva dati per la preview
    for det in input_data:
        st.session_state.archivio_dati.append({
            "Cassa": num_cassa, "Codice": codice_articolo, "Livello": det["Livello"], "Pezzi": det["Pezzi"]
        })
    
    # Crea Excel
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        ws.write(0, 0, "Cassa"); ws.write(0, 1, num_cassa)
        ws.write(1, 0, "Totale Pezzi"); ws.write(1, 1, totale_cassa)
    
    st.session_state.file_list.append(output.getvalue())
    
    # Reset e Ricarica
    st.session_state.reset_key += 1
    st.rerun()

# 3. Anteprima in fondo alla pagina (sempre visibile se ci sono dati)
st.write("---")
st.subheader("📋 Anteprima Report (Dati raccolti finora)")
if st.session_state.archivio_dati:
    df_preview = pd.DataFrame(st.session_state.archivio_dati)
    st.dataframe(df_preview, use_container_width=True)
else:
    st.info("Nessun dato inserito ancora.")
