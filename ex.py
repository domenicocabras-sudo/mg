import streamlit as st
import pandas as pd
import io
import xlsxwriter
import os
from datetime import datetime

st.set_page_config(layout="wide")
DB_FILE = "inventario_salvato.csv"

# --- 1. GESTIONE ARCHIVIO ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    # Nota: Le immagini non vanno nel CSV, le teniamo in memoria nella sessione
    if os.path.exists(DB_FILE):
        try:
            st.session_state.archivio_dati = pd.read_csv(DB_FILE).to_dict('records')
        except: pass

def salva_su_disco():
    # Salviamo solo i dati testuali nel CSV
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

for i, tab in enumerate(tabs):
    with tab:
        num_cassa = st.text_input("Numero Cassa:", key=f"id_{i}")
        codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cli_{i}")
        foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'], key=f"foto_{i}")
        
        cols = st.columns(4)
        quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
        
        totale_archiviato = sum(item['Pezzi'] for item in st.session_state.archivio_dati if item.get('tab_index') == i)
        st.metric(f"Totale pezzi salvati ({st.session_state.casse_aperte[i]})", totale_archiviato)
        
        if st.button(f"Salva Dati {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foto_bytes = foto_upload.getvalue() if foto_upload else None
            
            for j, q in enumerate(quantita):
                if q > 0:
                    st.session_state.archivio_dati.append({
                        "tab_index": i, "session_id": session_timestamp,
                        "Cassa": num_cassa, "Codice": codice, "Cliente": cliente, 
                        "Data": session_timestamp, "Livello": f"L{j+1}", "Pezzi": q,
                        "foto_bytes": foto_bytes if j == 0 else None # Solo primo record ha la foto
                    })
            salva_su_disco()
            st.rerun()

        # SIDEBAR DINAMICA
        with st.sidebar:
            st.header(f"Archivio: {st.session_state.casse_aperte[i]}")
            if st.button(f"🔄 Azzerare {st.session_state.casse_aperte[i]}", key=f"reset_{i}"):
                st.session_state.archivio_dati = [d for d in st.session_state.archivio_dati if d.get('tab_index') != i]
                salva_su_disco()
                st.rerun()

            dati_filtrati = [d for d in st.session_state.archivio_dati if d.get('tab_index') == i]
            if dati_filtrati:
                output = io.BytesIO()
                with xlsxwriter.Workbook(output) as wb:
                    ws = wb.add_worksheet("Inventario")
                    ws.set_column('A:F', 15)
                    ws.write_row(0, 0, ["Foto", "Cassa", "Codice", "Cliente", "Data", "Livello", "Pezzi"])
                    
                    last_session = None
                    for r, entry in enumerate(dati_filtrati, 1):
                        # Inserimento foto solo se presente e nuova sessione
                        if entry.get('foto_bytes'):
                            ws.insert_image(r, 0, 'foto.jpg', {'image_data': io.BytesIO(entry['foto_bytes']), 'x_scale': 0.1, 'y_scale': 0.1})
                        
                        if entry['session_id'] != last_session:
                            ws.write_row(r, 1, [entry['Cassa'], entry['Codice'], entry['Cliente'], entry['Data'], entry['Livello'], entry['Pezzi']])
                        else:
                            ws.write(r, 5, entry['Livello'])
                            ws.write(r, 6, entry['Pezzi'])
                        last_session = entry['session_id']
                        ws.set_row(r, 60) # Altezza riga per la foto
                
                st.download_button(f"📥 Scarica Report {st.session_state.casse_aperte[i]}", 
                                   output.getvalue(), f"Report_{st.session_state.casse_aperte[i]}.xlsx")
