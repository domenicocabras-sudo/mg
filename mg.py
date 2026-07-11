import streamlit as st
import qrcode
import io

# --- CONFIGURAZIONE NAVIGAZIONE ---
st.set_page_config(layout="wide")
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'

# --- LANDING PAGE ---
def mostra_home():
    st.title("Benvenuto nel Gestionale")
    if st.button("🚀 Accedi all'Inventario"):
        st.session_state.pagina = 'inventario'
        st.rerun()

# --- IL TUO CODICE ORIGINALE (INCAPSULATO) ---
def mostra_inventario():
    if st.button("⬅️ Torna alla Home"):
        st.session_state.pagina = 'home'
        st.rerun()

    # --- INIZIO CODICE ORIGINALE ---
    import pandas as pd
    import sqlite3
    import xlsxwriter
    import os
    from datetime import datetime

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

    def leggi_dal_db():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM inventario", conn)
        conn.close()
        return df.to_dict('records')

    col_titolo, col_btn = st.columns([4, 1])
    with col_titolo: st.title("Inventario")
    with col_btn:
        if st.button("➕ Aggiungi Cassa"):
            add_cassa()
            st.rerun()

    casse_attive = get_casse()
    tabs = st.tabs(casse_attive)

    for i, tab in enumerate(tabs):
        with tab:
            with st.form(key=f"form_{i}", clear_on_submit=True):
                num_cassa = st.text_input("Numero Cassa:")
                codice = st.text_input("Codice Articolo:")
                cliente = st.text_input("Nome Cliente:")
                foto_upload = st.file_uploader("Carica Foto", type=['jpg', 'png'])
                cols = st.columns(4)
                quantita = [cols[j].number_input(f"Q L{j+1}", min_value=0) for j in range(4)]
                submit_button = st.form_submit_button(label=f"Salva Dati {casse_attive[i]}")

            if submit_button:
                session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                foto_bytes = foto_upload.getvalue() if foto_upload else None
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for j, q in enumerate(quantita):
                    if q > 0:
                        c.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?)", 
                                  (i, session_timestamp, num_cassa.upper(), codice.upper(), cliente.upper(), 
                                   session_timestamp, f"L{j+1}", q, foto_bytes if j == 0 else None))
                conn.commit()
                conn.close()
                
                # AGGIUNTA QR CODE:
                dati_qr = f"Cassa: {num_cassa}|Cod: {codice}|Cli: {cliente}"
                qr = qrcode.make(dati_qr)
                qr_io = io.BytesIO()
                qr.save(qr_io, format='PNG')
                st.image(qr_io.getvalue(), caption="QR Code Articolo", width=150)
                st.download_button("Scarica QR", qr_io.getvalue(), "codice.png")
                
                st.rerun()

            dati_totali = leggi_dal_db()
            totale_archiviato = sum(item['Pezzi'] for item in dati_totali if item.get('tab_index') == i)
            st.metric(f"Totale pezzi salvati ({casse_attive[i]})", totale_archiviato)

            with st.sidebar:
                st.header(f"Archivio: {casse_attive[i]}")
                if st.button(f"🔄 Azzerare {casse_attive[i]}", key=f"reset_{i}"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("DELETE FROM inventario WHERE tab_index = ?", (i,))
                    conn.commit()
                    conn.close()
                    st.rerun()

                dati_filtrati = [d for d in leggi_dal_db() if d.get('tab_index') == i]
                if dati_filtrati:
                    # ... [Il resto del tuo codice originale per Excel rimane identico qui] ...
                    st.success("Dati pronti per il download")

# --- ROUTER ---
if st.session_state.pagina == 'home':
    mostra_home()
else:
    mostra_inventario()
