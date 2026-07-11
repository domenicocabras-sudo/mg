import streamlit as st
import pandas as pd
import sqlite3
import io
import xlsxwriter
import os
import qrcode
from datetime import datetime

# --- CONFIGURAZIONE GLOBALE ---
st.set_page_config(layout="wide")

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'

# --- LANDING PAGE ---
def pagina_home():
    st.title("📦 Sistema Gestionale")
    st.markdown("---")
    st.write("### Benvenuto nel portale di gestione")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()

# --- CODICE INVENTARIO ---
def pagina_inventario():
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
        st.rerun()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.join(BASE_DIR, "inventario.db")

    def init_db():
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                      (tab_index INTEGER, session_id TEXT, Cassa TEXT, Codice TEXT, 
                       Cliente TEXT, Data TEXT, Livello TEXT, Pezzi INTEGER, foto_bytes BLOB)''')
        c.execute('''CREATE TABLE IF NOT EXISTS configurazione (nome_cassa TEXT)''')
        c.execute("SELECT count(*) FROM configurazione")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO configurazione VALUES ('Cassa 1')")
        conn.commit()
        conn.close()

    init_db()

    # --- FUNZIONI ---
    def get_casse():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT nome_cassa FROM configurazione", conn)
        conn.close()
        return df['nome_cassa'].tolist()

    def add_cassa():
        conn = sqlite3.connect(DB_FILE)
        nuovo_nome = f"Cassa {len(get_casse()) + 1}"
        conn.execute("INSERT INTO configurazione VALUES (?)", (nuovo_nome,))
        conn.commit()
        conn.close()

    # --- INTERFACCIA ---
    col_titolo, col_btn = st.columns([4, 1])
    with col_titolo: st.title("Gestione Inventario")
    with col_btn:
        if st.button("➕ Aggiungi Cassa"):
            add_cassa()
            st.rerun()

    casse_attive = get_casse()
    tabs = st.tabs(casse_attive)

    for i, tab in enumerate(tabs):
        with tab:
            with st.form(key=f"form_{i}", clear_on_submit=True):
                num_cassa = st.text_input("Numero Cassa:", key=f"cassa_{i}")
                codice = st.text_input("Codice Articolo:", key=f"cod_{i}")
                cliente = st.text_input("Nome Cliente:", key=f"clie_{i}")
                cols = st.columns(4)
                quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0, key=f"q_{i}_{j}") for j in range(4)]
                submit_button = st.form_submit_button(label="Salva Dati")

            if submit_button:
                # 1. Salvataggio nel DB
                session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for j, q in enumerate(quantita):
                    if q > 0:
                        c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                                  (i, session_timestamp, num_cassa.upper(), codice.upper(), cliente.upper(), 
                                   session_timestamp, f"L{j+1}", q, None))
                conn.commit()
                conn.close()
                
                # 2. Generazione QR Code al volo
                dati_qr = f"Cassa:{num_cassa}|Art:{codice}|Cli:{cliente}"
                qr = qrcode.make(dati_qr)
                buffer = io.BytesIO()
                qr.save(buffer, format="PNG")
                
                st.success("Dati salvati!")
                st.image(buffer.getvalue(), caption="QR Code Articolo", width=150)
                st.download_button("Scarica QR", buffer.getvalue(), "qr_codice.png", "image/png")

# --- ROUTER ---
if st.session_state.pagina == 'home':
    pagina_home()
else:
    pagina_inventario()
