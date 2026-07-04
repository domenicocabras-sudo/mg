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

col_titolo, col_btn = st.columns([4, 1])
with col_titolo: st.title("Inventario Multi-Cassa")
with col_btn:
    if st.button("➕ Aggiungi Cassa"):
        st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
        st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

# --- 3. LOGICA DINAMICA SIDEBAR ---
for i, tab in enumerate(tabs):
    with tab:
        num_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        totale_archiviato = sum(item['Pezzi'] for item in st.session_state.archivio_dati if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({st.session_state.casse_aperte[i]})", totale_archiviato)
        
        if st.button(f"Salva Dati {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, "Cassa": num_cassa, "Codice": codice, 
                        "Cliente": cliente, "Livello": f"L{j+1}", "Pezzi": q
                    })
            salva_su_disco()
            st.rerun()

        # SIDEBAR DENTRO IL LOOP: si aggiorna solo quando questa tab è attiva
        with st.sidebar:
            st.header(f"Archivio: {st.session_state.casse_aperte[i]}")
            
            # Bottone Azzeramento
            if st.button(f"🔄 Azzerare {st.session_state.casse_aperte[i]}", key=f"reset_{i}"):
                st.session_state.archivio_dati = [d for d in st.session_state.archivio_dati if d.get('tab_index') != i]
                salva_su_disco()
                st.rerun()

            # Bottone Excel dinamico
            dati_filtrati = [d for d in st.session_state.archivio_dati if d.get('tab_index') == i]
            if dati_filtrati:
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    ws = wb.add_worksheet("Inventario")
                    ws.write_row(0, 0, ["Cassa", "Codice", "Cliente", "Livello", "Pezzi"])
                    for r, entry in enumerate(dati_filtrati, 1):
                        ws.write_row(r, 0, [entry['Cassa'], entry['Codice'], entry['Cliente'], entry['Livello'], entry['Pezzi']])
                
                st.download_button(f"📥 Scarica Report {st.session_state.casse_aperte[i]}", 
                                   output.getvalue(), f"Report_{st.session_state.casse_aperte[i]}.xlsx")
            else:
                st.info("Nessun dato da scaricare.")
