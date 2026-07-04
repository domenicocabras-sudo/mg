import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter
import os

st.set_page_config(layout="wide")

DB_FILE = "inventario_salvato.csv"

# --- INIZIALIZZAZIONE SICURA ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.archivio_dati = df.to_dict('records')
        except Exception:
            # Se il file è rotto, lo ignoriamo
            pass

if 'casse_aperte' not in st.session_state:
    st.session_state.casse_aperte = ["Cassa 1"]

# --- FUNZIONI ---
def salva_su_disco():
    dati_per_csv = [{k: v for k, v in item.items() if k != 'foto_bytes'} for item in st.session_state.archivio_dati]
    pd.DataFrame(dati_per_csv).to_csv(DB_FILE, index=False)

def genera_excel():
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
        for i, h in enumerate(headers): ws.write(0, i, h)
        
        for r, entry in enumerate(st.session_state.archivio_dati, 1):
            if entry.get('foto_bytes'):
                try:
                    ws.insert_image(r, 0, "foto.jpg", {'image_data': io.BytesIO(entry['foto_bytes'])})
                except: pass
            ws.write(r, 1, str(entry.get('Cassa', '')))
            ws.write(r, 2, str(entry.get('Data', '')))
            ws.write(r, 3, str(entry.get('Codice', '')))
            ws.write(r, 4, str(entry.get('Cliente', '')))
            ws.write(r, 5, str(entry.get('Livello', '')))
            ws.write(r, 6, entry.get('Pezzi', 0))
            ws.write(r, 7, str(entry.get('Totale_Cassa', '')))
    return output.getvalue()

# --- UI ---
st.title("Inventario")

if st.button("➕ Aggiungi Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)
for i, tab in enumerate(tabs):
    with tab:
        num_cassa = st.text_input("Cassa:", key=f"cassa_{i}")
        codice = st.text_input("Codice:", key=f"codice_{i}")
        cliente = st.text_input("Cliente:", key=f"cliente_{i}")
        
        cols = st.columns(4)
        input_data = []
        totale_cassa = 0
        for j in range(1, 5):
            q = cols[j-1].number_input(f"Q (L{j}):", min_value=0, key=f"q_{i}_{j}")
            if q > 0:
                input_data.append({"Livello": f"L{j}", "Pezzi": q})
                totale_cassa += q
        
        uploaded = st.file_uploader("Foto", key=f"up_{i}")
        if uploaded and st.button(f"Salva {i}", key=f"btn_{i}"):
            f_bytes = uploaded.getvalue()
            for idx, d in enumerate(input_data):
                st.session_state.archivio_dati.append({
                    "Cassa": num_cassa if idx==0 else "", "Data": datetime.now().strftime("%d/%m/%Y") if idx==0 else "",
                    "Codice": codice if idx==0 else "", "Cliente": cliente if idx==0 else "",
                    "Livello": d["Livello"], "Pezzi": d["Pezzi"], "Totale_Cassa": totale_cassa if idx==0 else "",
                    "foto_bytes": f_bytes if idx==0 else None
                })
            salva_su_disco()
            st.rerun()
