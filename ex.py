import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. GESTIONE STATO ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        st.session_state.archivio_dati = pd.read_csv(DB_FILE).to_dict('records')

def salva():
    pd.DataFrame(st.session_state.archivio_dati).to_csv(DB_FILE, index=False)

# --- 2. INTERFACCIA ---
st.title("Inventario Multi-Cassa")

if st.button("➕ Aggiungi Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

tabs = st.tabs(st.session_state.casse_aperte)

# Questa variabile memorizza il totale della cassa selezionata per la sidebar
totale_sidebar = 0

for i, tab in enumerate(tabs):
    with tab:
        st.subheader(f"Gestione {st.session_state.casse_aperte[i]}")
        
        # Campi Input (Le chiavi con {i} mantengono i dati unici per ogni tab)
        cassa_id = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        # Calcolo Totali
        totale_input = sum(quantita)
        totale_archivio = sum(d['Pezzi'] for d in st.session_state.archivio_dati if d.get('tab_index') == i)
        
        st.info(f"Totale pezzi salvati in questa cassa: {totale_archivio}")
        
        # Pulsante Salva
        if st.button(f"Salva dati Cassa {i+1}", key=f"btn_{i}"):
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i,
                        "Cassa": cassa_id,
                        "Codice": codice,
                        "Cliente": cliente,
                        "Livello": f"L{j+1}",
                        "Pezzi": q
                    })
            salva()
            st.rerun()
            
        # Aggiorna il totale per la sidebar solo se questa è la tab corrente
        if st.session_state.get("active_tab") == i:
            totale_sidebar = totale_input + totale_archivio

# --- 3. SIDEBAR ---
with st.sidebar:
    st.metric("Totale Cassa Attiva", totale_sidebar)
    if st.button("Pulisci Archivio"):
        st.session_state.archivio_dati = []
        salva()
        st.rerun()
