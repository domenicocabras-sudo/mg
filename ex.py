import streamlit as st
import pandas as pd
import io
import xlsxwriter
import os

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. GESTIONE ARCHIVIO ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        try:
            st.session_state.archivio_dati = pd.read_csv(DB_FILE).to_dict('records')
        except: pass

def salva_su_disco():
    pd.DataFrame(st.session_state.archivio_dati).to_csv(DB_FILE, index=False)

# --- 2. INTERFACCIA ---
if 'casse_aperte' not in st.session_state: st.session_state.casse_aperte = ["Cassa 1"]

# Layout superiore: Titolo e Bottone Aggiungi Cassa a destra
col_titolo, col_btn = st.columns([4, 1])
with col_titolo:
    st.title("Inventario Multi-Cassa")
with col_btn:
    st.write("") # Spazio per allineamento
    if st.button("➕ Aggiungi Cassa"):
        st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
        st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        num_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        # Logica contatore locale
        totale_archiviato = sum(item['Pezzi'] for item in st.session_state.archivio_dati if item.get('tab_index') == i)
        totale_corrente = sum(quantita) + totale_archiviato
        
        st.metric(f"Totale pezzi {st.session_state.casse_aperte[i]}", totale_corrente)
        
        if st.button(f"Salva Dati {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, 
                        "Cassa": num_cassa, "Codice": codice, 
                        "Cliente": cliente, "Livello": f"L{j+1}", "Pezzi": q
                    })
            salva_su_disco()
            st.rerun()

# --- 3. SIDEBAR (ARCHIVIO E PULIZIA) ---
with st.sidebar:
    st.header("Archivio e Controlli")
    
    if st.button("🧹 Pulisci Archivio Cassa Attiva"):
        # Rimuove solo i dati della cassa selezionata (indice i corrente non disponibile qui, quindi pulisce tutto)
        st.session_state.archivio_dati = []
        salva_su_disco()
        st.rerun()

    st.divider()
    if st.session_state.archivio_dati:
        output = io.BytesIO()
        with xlsxwriter.Workbook(output) as wb:
            ws = wb.add_worksheet("Inventario")
            ws.write_row(0, 0, ["Cassa", "Codice", "Cliente", "Livello", "Pezzi"])
            for r, entry in enumerate(st.session_state.archivio_dati, 1):
                ws.write_row(r, 0, [entry['Cassa'], entry['Codice'], entry['Cliente'], entry['Livello'], entry['Pezzi']])
        
        st.download_button("📥 Scarica Report Excel", output.getvalue(), "Inventario.xlsx")
