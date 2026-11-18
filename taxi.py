
"""
App Streamlit: richiesta di passaggio in auto.
Riceve la richiesta, risponde con un messaggio di accettazione
e mostra sulla mappa l'indirizzo richiesto.

Avvio:  streamlit run app.py
"""

import datetime as dt
import uuid

import streamlit.components.v1 as components
import streamlit as st
from geopy.geocoders import ArcGIS, Nominatim, Photon

st.set_page_config(page_title="Richiesta passaggio", page_icon="🚗", layout="centered")

# User-agent univoco: Nominatim blocca gli user-agent generici/condivisi
USER_AGENT = f"richiesta-passaggio-{uuid.uuid4().hex[:8]}"


class IndirizzoNonTrovato(Exception):
    pass


# ---------------------------------------------------------------------------
# Geocoding con più servizi di riserva.
# Solo i risultati riusciti vengono messi in cache (un'eccezione non viene
# salvata da st.cache_data), così un errore temporaneo non resta "bloccato".
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def geocodifica(indirizzo: str, paese: str):
    """Restituisce (lat, lon, indirizzo_completo, servizio) o solleva un'eccezione."""
    query = f"{indirizzo}, {paese}" if paese and paese.lower() not in indirizzo.lower() else indirizzo

    servizi = [
        ("OpenStreetMap (Nominatim)",
         lambda: Nominatim(user_agent=USER_AGENT, timeout=10).geocode(query, language="it")),
        ("OpenStreetMap (Photon)",
         lambda: Photon(user_agent=USER_AGENT, timeout=10).geocode(query, language="it")),
        ("ArcGIS",
         lambda: ArcGIS(user_agent=USER_AGENT, timeout=10).geocode(query)),
    ]

    errori = []
    for nome, cerca in servizi:
        try:
            luogo = cerca()
        except Exception as e:  # rete, SSL, proxy, 403, 429, timeout...
            errori.append(f"{nome}: {type(e).__name__} – {e}")
            continue
        if luogo is not None:
            return luogo.latitude, luogo.longitude, luogo.address, nome
        errori.append(f"{nome}: nessun risultato")

    # Se tutti hanno risposto "nessun risultato" l'indirizzo non esiste;
    # altrimenti è un problema di connessione ai servizi.
    if all(err.endswith("nessun risultato") for err in errori):
        raise IndirizzoNonTrovato(indirizzo)
    raise ConnectionError("\n".join(errori))


def trova(indirizzo: str, paese: str, etichetta: str):
    """Chiama la geocodifica e mostra un errore chiaro. Restituisce il risultato o None."""
    try:
        return geocodifica(indirizzo, paese)
    except IndirizzoNonTrovato:
        st.error(
            f"{etichetta}: indirizzo **«{indirizzo}»** non trovato. "
            "Prova a scriverlo in modo più completo (via, numero civico, città)."
        )
    except ConnectionError as e:
        st.error(
            f"{etichetta}: non riesco a contattare il servizio delle mappe. "
            "Controlla la connessione a internet (o il proxy/firewall) e riprova."
        )
        with st.expander("Dettagli tecnici"):
            st.code(str(e))
    return None


def messaggio_accettazione(nome, partenza, arrivo, data, ora, passeggeri, note):
    testo = (
        f"Ciao **{nome}**! 👋\n\n"
        f"La tua richiesta di passaggio è stata **accettata** ✅\n\n"
        f"- 📍 **Ritiro:** {partenza}\n"
    )
    if arrivo:
        testo += f"- 🏁 **Destinazione:** {arrivo}\n"
    testo += (
        f"- 📅 **Data:** {data.strftime('%d/%m/%Y')}\n"
        f"- 🕒 **Ora:** {ora.strftime('%H:%M')}\n"
        f"- 👥 **Passeggeri:** {passeggeri}\n"
    )
    if note:
        testo += f"- 📝 **Note:** {note}\n"
    testo += "\nTi aspetto all'indirizzo indicato. Buon viaggio! 🚗"
    return testo


# ---------------------------------------------------------------------------
# Interfaccia
# ---------------------------------------------------------------------------
st.title("🚗 Richiesta di passaggio in auto")
st.write("Compila il modulo: riceverai la conferma e vedrai il punto di ritiro sulla mappa.")

with st.form("richiesta"):
    nome = st.text_input("Il tuo nome *")
    partenza = st.text_input("Indirizzo di ritiro *", placeholder="Es. Piazza del Duomo, Milano")
    arrivo = st.text_input("Destinazione (facoltativa)", placeholder="Es. Stazione Centrale, Milano")
    col1, col2 = st.columns(2)
    data = col1.date_input("Data", value=dt.date.today(), min_value=dt.date.today(), format="DD/MM/YYYY")
    ora = col2.time_input("Ora", value=dt.time(9, 0))
    passeggeri = st.number_input("Numero di passeggeri", min_value=1, max_value=8, value=1)
    note = st.text_area("Messaggio / note", placeholder="Es. Ho una valigia grande")
    paese = st.text_input("Paese", value="Italia", help="Aggiunto alla ricerca per trovare l'indirizzo più facilmente")
    inviato = st.form_submit_button("Invia richiesta", type="primary")

if inviato:
    if not nome.strip() or not partenza.strip():
        st.error("Inserisci almeno il nome e l'indirizzo di ritiro.")
        st.stop()

    with st.spinner("Cerco l'indirizzo sulla mappa..."):
        geo_partenza = trova(partenza.strip(), paese.strip(), "Ritiro")
        geo_arrivo = trova(arrivo.strip(), paese.strip(), "Destinazione") if arrivo.strip() else None

    if geo_partenza is None:
        st.session_state.pop("risultato", None)
        st.stop()

    # Salvo il risultato: resta visibile anche dopo i rerun di Streamlit
    st.session_state["risultato"] = {
        "messaggio": messaggio_accettazione(
            nome.strip(), geo_partenza[2], geo_arrivo[2] if geo_arrivo else arrivo.strip(),
            data, ora, passeggeri, note.strip(),
        ),
        "partenza": geo_partenza,
        "arrivo": geo_arrivo,
    }


def mappa_osm(lat, lon, lat2=None, lon2=None, altezza=450):
    """Mappa OpenStreetMap incorporata con un segnaposto sull'indirizzo di ritiro."""
    if lat2 is None:
        d = 0.006  # circa 600 m attorno al punto
        bbox = (lon - d, lat - d * 0.7, lon + d, lat + d * 0.7)
    else:
        m = 0.01
        bbox = (min(lon, lon2) - m, min(lat, lat2) - m, max(lon, lon2) + m, max(lat, lat2) + m)
    url = (
        "https://www.openstreetmap.org/export/embed.html"
        f"?bbox={bbox[0]:.6f}%2C{bbox[1]:.6f}%2C{bbox[2]:.6f}%2C{bbox[3]:.6f}"
        f"&layer=mapnik&marker={lat:.6f}%2C{lon:.6f}"
    )
    components.iframe(url, height=altezza)


ris = st.session_state.get("risultato")
if ris:
    lat, lon, indirizzo, servizio = ris["partenza"]

    st.success("Richiesta accettata!")
    st.markdown(ris["messaggio"])

    st.subheader("📍 Punto di ritiro sulla mappa")
    if ris["arrivo"]:
        mappa_osm(lat, lon, ris["arrivo"][0], ris["arrivo"][1])
        st.caption("Il segnaposto indica il ritiro; la mappa è inquadrata per includere anche la destinazione.")
    else:
        mappa_osm(lat, lon)

    c1, c2 = st.columns(2)
    c1.link_button("Apri in Google Maps", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                   use_container_width=True)
    c2.link_button("Apri in OpenStreetMap", f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}",
                   use_container_width=True)
    st.caption(f"Coordinate: {lat:.5f}, {lon:.5f} · indirizzo trovato tramite {servizio}")
