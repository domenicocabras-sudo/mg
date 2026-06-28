import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📸 Inventario Rapido: Foto e Dati")

# Sezione di input dati su una singola riga
with st.container():
    # Definiamo le proporzioni: Codice e Cliente sono più larghi, Pezzi e Livello più stretti
    col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1.5])
    
    with col1:
        codice_articolo = st.text_input("Codice Articolo:")
    with col2:
        nome_cliente = st.text_input("Nome Cliente:")
    with col3:
        num_pezzi = st.number_input("Pezzi:", min_value=0, step=1)
    with col4:
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
            "Codice_Articolo": codice_articolo,
            "Cliente": nome_cliente,
            "Numero_Pezzi": num_pezzi,
            "Livello": livello
        }
        st.session_state.inventario.append(nuova_riga)
        st.success(f"Dati salvati per l'articolo {codice_articolo}.")

# Visualizzazione tabella e download
if st.session_state.inventario:
    st.write("### Riepilogo Inventario")
    df = pd.DataFrame(st.session_state.inventario)
    st.table(df)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    
    st.download_button(
        label="📥 Scarica Excel Completo",
        data=output.getvalue(),
        file_name="inventario_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
