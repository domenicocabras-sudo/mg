import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter
import os

st.set_page_config(layout="wide")

DB_FILE = "inventario_salvato.csv"

# --- INIZIALIZZAZIONE ---
if 'archivio_dati' not in st.session_state:
    st.session_state.archivio_dati = []
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.archivio_dati = df.to_dict('records')
        except: pass

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
        fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        for r, entry in enumerate(st.session_state.archivio_dati, 1):
            ws.write(r, 1, str(entry.get('Cassa', '')), fmt)
            ws.write(r, 2, str(entry.get('Data', '')), fmt)
            ws.write(r, 3, str(entry.get('Codice', '')), fmt)
            ws.write(r, 4, str(entry.get('Cliente', '')), fmt)
            ws.write(r, 5, str(entry.get('Livello', '')), fmt)
            ws.write(r, 6, entry.get('Pezzi', 0), fmt)
            ws.write(r, 7, str(entry.get('Totale_Cassa', '')), fmt)
    return output.getvalue()

# --- INTERFACCIA ---
st.title("Inventario Multi-Cassa")

if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

# Variabile per il totale della cassa attiva
totale_cassa_attiva = 0

for i, tab in enumerate(tabs):
    with tab:
        # Recupero i dati se già inseriti per questa cassa specifica
        num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{i}")
        codice = st.text_input("Codice Articolo:", key=f"codice_{i}")
        cliente = st.text_input("Nome Cliente:", key=f"cliente_{i}")
        
        cols = st.columns(4)
        input_data = []
        totale_parziale = 0
        for j in range(1, 5):
            q = cols[j-1].number_input(f"Quantità L{j}:", min_value=0, key=f"q_{i}_{j}")
            if q > 0:
                input_data.append({"Livello": f"Livello {j}", "Pezzi": q})
                totale_parziale += q
        
        # LOGICA CONTEGGIO: Conta solo ciò che appartiene a questa cassa nell'archivio
        # Usiamo 'num_cassa' come filtro principale
        totale_archiviato = sum(int(item['Pezzi']) for item in st.session_state.archivio_dati 
                                 if str(item.get('Cassa', '')) == num_cassa and num_cassa != "")
        
        totale_cassa_attiva = totale_parziale + totale_archiviato
        st.info(f"Totale pezzi in archivio per {num_cassa if num_cassa else 'questa cassa'}: {totale_archiviato}")

        uploaded = st.file_uploader("Carica Foto", key=f"up_{i}")
        
        if uploaded and st.button(f"Salva {st.session_state.casse_aperte[i]}", key=f"btn_{i}"):
            f_bytes = uploaded.getvalue()
            for idx, d in enumerate(input_data):
                st.session_state.archivio_dati.append({
                    "Cassa": num_cassa if idx == 0 else "", 
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M") if idx == 0 else "",
                    "Codice": codice if idx == 0 else "", 
                    "Cliente": cliente if idx == 0 else "",
                    "Livello": d["Livello"], 
                    "Pezzi": d["Pezzi"], 
                    "Totale_Cassa": totale_parziale if idx == 0 else "",
                    "foto_bytes": f_bytes if idx == 0 else None
                })
            salva_su_disco()
            st.success("Dati salvati!")
            st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Archivio e Totali")
    st.metric("Totale Cassa Attiva", totale_cassa_attiva)
    if st.session_state.archivio_dati:
        st.download_button("📥 Scarica Report Excel", genera_excel(), "Inventario.xlsx")
