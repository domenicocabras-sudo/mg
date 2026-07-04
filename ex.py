import streamlit as st
import io
import pandas as pd
from datetime import datetime
import xlsxwriter

st.set_page_config(layout="wide")

# --- INIZIALIZZAZIONE STATO (Persistenza Dati) ---
if 'archivio_dati' not in st.session_state: 
    st.session_state.archivio_dati = []
if 'casse_aperte' not in st.session_state: 
    st.session_state.casse_aperte = ["Cassa 1"]
if 'file_riepilogo' not in st.session_state: 
    st.session_state.file_riepilogo = None

# Funzione per calcolare il totale globale dinamicamente dai dati esistenti
def calcola_totale_globale():
    return sum(item['Pezzi'] for item in st.session_state.archivio_dati)

# --- FUNZIONE GENERAZIONE EXCEL ---
def genera_excel():
    output = io.BytesIO()
    with xlsxwriter.Workbook(output, {'in_memory': True}) as wb:
        ws = wb.add_worksheet("Inventario")
        fmt = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        hdr = wb.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        
        ws.set_column(0, 7, 15)
        headers = ["Foto", "Cassa", "Data", "Codice", "Cliente", "Livello", "Pezzi", "Totale Cassa"]
        for i, h in enumerate(headers): ws.write(0, i, h, hdr)
        
        row = 1
        for entry in st.session_state.archivio_dati:
            ws.insert_image(row, 0, "foto.jpg", {
                'image_data': io.BytesIO(entry['foto_bytes']), 
                'x_scale': 0.05, 'y_scale': 0.05
            })
            ws.write(row, 1, entry['Cassa'], fmt)
            ws.write(row, 2, entry['Data'], fmt)
            ws.write(row, 3, entry['Codice'], fmt)
            ws.write(row, 4, entry['Cliente'], fmt)
            ws.write(row, 5, entry['Livello'], fmt)
            ws.write(row, 6, entry['Pezzi'], fmt)
            ws.write(row, 7, entry['Totale_Cassa'], fmt)
            ws.set_row(row, 60)
            row += 1
    return output.getvalue()

# --- SIDEBAR (Sempre presente) ---
with st.sidebar:
    st.header("Archivio e Totali")
    # Calcolo dinamico: non si perde mai perché legge da st.session_state.archivio_dati
    totale_globale = calcola_totale_globale()
    st.metric("Totale Pezzi Globale", totale_globale)
    st.divider()
    if st.session_state.file_riepilogo:
        st.download_button("📥 Scarica Report Globale Aggiornato", st.session_state.file_riepilogo, "Riepilogo_Inventario.xlsx")

# --- INTERFACCIA PRINCIPALE ---
st.title("Inventario Multi-Cassa")

if st.button("➕ Aggiungi Nuova Cassa"):
    st.session_state.casse_aperte.append(f"Cassa {len(st.session_state.casse_aperte) + 1}")
    st.rerun()

tabs = st.tabs(st.session_state.casse_aperte)

for i, tab in enumerate(tabs):
    with tab:
        col_a, col_b, col_c = st.columns([1, 2, 2])
        num_cassa = col_a.text_input("Numero Cassa:", key=f"cassa_{i}")
        codice_articolo = col_b.text_input("Codice Articolo:", key=f"codice_{i}")
        nome_cliente = col_c.text_input("Nome Cliente:", key=f"cliente_{i}")

        cols = st.columns(4)
        input_data = []
        totale_cassa = 0
        for j in range(1, 5):
            q = cols[j-1].number_input(f"Quantità (Livello {j}):", min_value=0, key=f"q_{i}_{j}")
            if q > 0:
                input_data.append({"Livello": f"Livello {j}", "Pezzi": q})
                totale_cassa += q

        uploaded_file = st.file_uploader(f"Trascina Foto {st.session_state.casse_aperte[i]}", type=['jpg', 'png'], key=f"up_{i}")

        if uploaded_file and st.button(f"Conferma e Salva {st.session_state.casse_aperte[i]}"):
            foto_bytes = uploaded_file.getvalue()
            
            for det in input_data:
                st.session_state.archivio_dati.append({
                    "Cassa": num_cassa, "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Codice": codice_articolo, "Cliente": nome_cliente,
                    "Livello": det["Livello"], "Pezzi": det["Pezzi"],
                    "Totale_Cassa": totale_cassa, "foto_bytes": foto_bytes
                })
            
            st.session_state.file_riepilogo = genera_excel()
            st.success("Dati salvati!")
            st.rerun()
