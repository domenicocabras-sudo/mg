import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. INIZIALIZZAZIONE ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        st.session_state.archivio_dati = df.to_dict('records')

if 'casse_aperte' not in st.session_state:
    st.session_state.casse_aperte = ["Cassa 1"]

# --- 2. FUNZIONI ---
def salva_su_disco():
    pd.DataFrame(st.session_state.archivio_dati).to_csv(DB_FILE, index=False)

# --- 3. INTERFACCIA ---
st.title("Inventario Multi-Cassa")

if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

# Questa variabile conterrà il totale per la sidebar
totale_cassa_attiva_visualizzato = 0

for i, tab in enumerate(tabs):
    with tab:
        # INPUT (Usa sempre la KEY basata su 'i' per mantenere i valori quando cambi tab)
        num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{i}")
        codice = st.text_input("Codice Articolo:", key=f"codice_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cliente_{i}")
        
        # INPUT QUANTITÀ
        cols = st.columns(4)
        input_q = []
        for j in range(1, 5):
            val = cols[j-1].number_input(f"Q L{j}:", min_value=0, key=f"q_{i}_{j}")
            input_q.append(val)
        
        totale_nuovo_input = sum(input_q)
        
        # CALCOLO ARCHIVIO (Filtra solo i dati di questa tab 'i')
        dati_cassa_i = [item for item in st.session_state.archivio_dati if item.get('tab_index') == i]
        totale_archiviato = sum(int(item['Pezzi']) for item in dati_cassa_i)
        
        # Totale visualizzato nella TAB
        totale_totale = totale_nuovo_input + totale_archiviato
        st.subheader(f"Totale pezzi in questa cassa: {totale_totale}")
        
        # Se questa è la tab attiva, passiamo il valore alla sidebar
        if i == tabs.index(tab): # Logica per identificare la tab selezionata
            totale_cassa_attiva_visualizzato = totale_totale
            
        if st.button(f"Salva Dati {i+1}", key=f"btn_{i}"):
            for j, q in enumerate(input_q):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, 
                        "Cassa": num_cassa if j == 0 else "", 
                        "Data": datetime.now().strftime("%d/%m/%Y") if j == 0 else "",
                        "Codice": codice if j == 0 else "", 
                        "Pezzi": q
                    })
            salva_su_disco()
            st.rerun()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Archivio e Totali")
    st.metric("Totale Cassa Attiva", totale_cassa_attiva_visualizzato)
