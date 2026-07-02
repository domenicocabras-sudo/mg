import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato
if 'file_list' not in st.session_state: st.session_state.file_list = []
if 'archivio_dati' not in st.session_state: st.session_state.archivio_dati = []
if 'totale_globale' not in st.session_state: st.session_state.totale_globale = 0

st.title("Inventario Gestione")

# Creazione dei Tab
tab1, tab2, tab3 = st.tabs(["➕ Nuovo Inserimento", "📋 Archivio Dati", "📊 Riepilogo"])

with tab1:
    col_a, col_b, col_c = st.columns([1, 2, 2])
    with col_a: num_cassa = st.text_input("Numero Cassa:")
    with col_b: codice_articolo = st.text_input("Codice Articolo:")
    with col_c: nome_cliente = st.text_input("Nome Cliente:")

    cols = st.columns(4)
    input_data = []
    totale_cassa = 0
    for i in range(1, 5):
        with cols[i-1]:
            q = st.number_input(f"Quantità (Livello {i}):", min_value=0, key=f"q_{i}")
            if q > 0:
                input_data.append({"Livello": f"Livello {i}", "Pezzi": q})
                totale_cassa += q

    st.metric("Totale Pezzi in questa Cassa", totale_cassa)
    uploaded_file = st.file_uploader("Trascina Foto Articolo", type=['jpg', 'png', 'jpeg'])

    if uploaded_file and st.button("Conferma e Salva"):
        st.session_state.totale_globale += totale_cassa
        for det in input_data:
            st.session_state.archivio_dati.append({
                "Cassa": num_cassa, "Codice": codice_articolo, 
                "Livello": det["Livello"], "Pezzi": det["Pezzi"]
            })
        st.success("Dato salvato!")
        st.rerun()

with tab2:
    st.subheader("📋 Storico Inserimenti")
    if st.session_state.archivio_dati:
        st.dataframe(pd.DataFrame(st.session_state.archivio_dati), use_container_width=True)
    else:
        st.info("Nessun dato inserito.")

with tab3:
    st.subheader("📊 Totali")
    st.metric("Totale Pezzi Globale", st.session_state.totale_globale)
    if st.session_state.file_list:
        for i, file_data in enumerate(st.session_state.file_list):
            st.download_button(f"Scarica Report Cassa {i+1}", file_data, f"Report_{i+1}.xlsx")
