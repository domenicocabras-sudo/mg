import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# Inizializzazione stato
if 'archivio_dati' not in st.session_state: st.session_state.archivio_dati = []
if 'totale_globale' not in st.session_state: st.session_state.totale_globale = 0
# Gestione Casse dinamiche
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

st.title("Gestione Inventario Multi-Cassa")

# Bottone per aggiungere una nuova cassa
if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

# Creazione tab dinamica
tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        st.subheader(f"Inserimento Dati per {st.session_state.casse_aperte[i]}")
        
        # Form di input
        c1, c2, c3 = st.columns(3)
        num_cassa = c1.text_input(f"ID Cassa {i}", key=f"cassa_{i}")
        codice = c2.text_input(f"Codice Articolo {i}", key=f"codice_{i}")
        cliente = c3.text_input(f"Cliente {i}", key=f"cliente_{i}")
        
        cols = st.columns(4)
        input_data = []
        totale_cassa = 0
        for j in range(1, 5):
            q = cols[j-1].number_input(f"Livello {j}", min_value=0, key=f"q_{i}_{j}")
            if q > 0:
                input_data.append({"Livello": f"Livello {j}", "Pezzi": q})
                totale_cassa += q
        
        uploaded_file = st.file_uploader(f"Foto {st.session_state.casse_aperte[i]}", type=['jpg', 'png'], key=f"up_{i}")
        
        if uploaded_file and st.button(f"Salva {st.session_state.casse_aperte[i]}", key=f"save_{i}"):
            st.session_state.totale_globale += totale_cassa
            # Logica salvataggio identica alla tua...
            st.success("Dati salvati!")

# --- RIEPILOGO E LINK XLS ---
st.divider()
st.subheader("📊 Riepilogo Globale")

if st.session_state.archivio_dati:
    df_totale = pd.DataFrame(st.session_state.archivio_dati)
    
    # Generazione file Excel unico di riepilogo
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_totale.to_excel(writer, index=False, sheet_name='Riepilogo')
    
    st.download_button(
        label="📥 Scarica Riepilogo Totale (Excel)",
        data=buffer,
        file_name="Inventario_Completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.dataframe(df_totale, use_container_width=True)
else:
    st.info("Nessun dato inserito.")
