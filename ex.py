import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.title("📸 Inventario Rapido: Foto e Dati")

# Sezione di input dati
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        nome_cliente = st.text_input("Nome Cliente:")
    with col2:
        num_pezzi = st.number_input("Numero Pezzi:", min_value=0, step=1)
    with col3:
        livello = st.selectbox("Livello:", ["A", "B", "C", "D"])

# Sezione Fotocamera
img_file_buffer = st.camera_input("Scatta una foto della cassa")

# Gestione Inventario
if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Salvataggio dati
if img_file_buffer and nome_cliente:
    if st.button("Conferma e Salva in Lista"):
        nuova_riga = {
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Cliente": nome_cliente,
            "Numero_Pezzi": num_pezzi,
            "Livello": livello
        }
        st.session_state.inventario.append(nuova_riga)
        st.success(f"Dati salvati per {nome_cliente} (Livello {livello}): {num_pezzi} pezzi.")

# Visualizzazione tabella e download
if st.session_state.inventario:
    st.write("### Riepilogo Inventario")
    df = pd.DataFrame(st.session_state.inventario)
    st.table(df)
    
    # Preparazione file Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    
    st.download_button(
        label="📥 Scarica Excel Completo",
        data=output.getvalue(),
        file_name="inventario_clienti.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
