import streamlit as st
from auth import Authenticator
from permission import puo_modificare, puo_visualizzare, is_admin, richiedi_permesso
from database import init_database
from database import init_database, get_connection
import pandas as pd
from load_users import genera_email, genera_password
from config import ADMIN_USERNAME, ADMIN_PASSWORD

# Inizializza database e autenticatore
init_database()
auth = Authenticator()

st.set_page_config(page_title="Ispettorato", layout="wide")

def pagina_login():
    """Mostra il form di login"""
    st.title("Accesso Ispettorato")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Accedi"):
        successo, messaggio = auth.login(email, password)
        if successo:
            st.rerun()
        else:
            st.error(messaggio)
          
def pagina_cambio_password():
    """Forza il cambio password al primo accesso"""
    st.title("Cambio password obbligatorio")
    st.warning("Devi cambiare la password prima di continuare")

    attuale = st.text_input("Password attuale", type="password")
    nuova = st.text_input("Nuova password", type="password")
    conferma = st.text_input("Conferma password", type="password")

    if st.button("Cambia password"):
        if nuova != conferma:
            st.error("Le password non coincidono")
        else:
            successo, messaggio = auth.cambia_password(attuale, nuova)
            if successo:
                st.success(messaggio)
                st.rerun()
            else:
                st.error(messaggio)
def pagina_principale():
    """Pagina principale dopo il login"""
    st.sidebar.write(f"Utente: {st.session_state.nominativo}")
    st.sidebar.write(f"Ufficio: {st.session_state.ufficio}")
    st.sidebar.write(f"Ruolo: {st.session_state.ruolo}")

    if st.sidebar.button("Logout"):
        auth.logout()
        st.rerun()

    st.title("Ispettorato - Area Riservata")
    st.write(f"Benvenuto, {st.session_state.nominativo}!")

    # Pannello admin visibile solo ai DIR.
    if is_admin():
        pannello_admin()
def pagina_carica_utenti():
    """Permette all'admin di caricare utenti da Excel"""
    st.title("Caricamento Utenti (Area Riservata)")

    # Stato admin
    if "admin_autenticato" not in st.session_state:
        st.session_state.admin_autenticato = False
    if "credenziali_generate" not in st.session_state:
        st.session_state.credenziali_generate = None

    # Login admin
    if not st.session_state.admin_autenticato:
        username = st.text_input("Username admin")
        password = st.text_input("Password admin", type="password")
        if st.button("Accedi come admin"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_autenticato = True
                st.rerun()
            else:
                st.error("Credenziali admin non valide")
        return

    st.success("Accesso admin confermato")

    # Se ci sono credenziali già generate, mostrali
    if st.session_state.credenziali_generate is not None:
        st.subheader("Credenziali generate")
        df_cred = pd.DataFrame(st.session_state.credenziali_generate)
        st.dataframe(df_cred)
        st.download_button(
            "Scarica credenziali CSV",
            df_cred.to_csv(index=False),
            "credenziali_temporanee.csv",
            "text/csv"
        )
        st.warning("Scarica il file, distribuisci le password e poi eliminalo!")
        if st.button("Pulisci credenziali dalla schermata"):
            st.session_state.credenziali_generate = None
            st.rerun()
        return

    # Caricamento file
    file = st.file_uploader("Carica il file Excel del personale", type=["xlsx"])

    if file and st.button("Carica utenti"):
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip().str.lower()
        df = df.dropna(subset=["nominativo"])
        credenziali = []

        for _, riga in df.iterrows():
            nominativo = riga["nominativo"]
            email = genera_email(nominativo)
            password_utente = genera_password()

            pw_hash, salt = Authenticator.hash_password(password_utente)
            stored = f"{pw_hash}:{salt}"

            with get_connection() as conn:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO users 
                        (nominativo, email, password_hash, ruolo, ufficio, stanza, interno, cellulare)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nominativo, email, stored,
                            riga["ruolo"], str(riga["ufficio"]),
                            str(riga.get("stanza", "")),
                            str(riga.get("interno", "")),
                            str(riga.get("cellulare", ""))
                        )
                    )
                    credenziali.append({
                        "nominativo": nominativo,
                        "email": email,
                        "password": password_utente
                    })
                except Exception as e:
                    st.error(f"Errore per {nominativo}: {e}")

        if credenziali:
            st.session_state.credenziali_generate = credenziali
            st.success(f"Caricati {len(credenziali)} utenti!")
            st.rerun()
def pannello_admin():
    """Pannello per il direttore"""
    with st.expander("Gestione Utenti"):
        st.subheader("Reset Password")

        with get_connection() as conn:
            utenti = conn.execute(
                "SELECT id, nominativo, email FROM users WHERE attivo = 1"
            ).fetchall()

        utente_scelto = st.selectbox(
            "Seleziona utente",
            utenti,
            format_func=lambda u: f"{u['nominativo']} ({u['email']})"
        )

        if st.button("Reset Password"):
            nuova_pw = Authenticator.reset_password(utente_scelto["id"])
            st.success(f"Nuova password temporanea: {nuova_pw}")
            st.warning("Comunicala all'utente e poi chiudi questa pagina")
# Flusso principale
# Flusso principale
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Carica Utenti"])
    with tab1:
        pagina_login()
    with tab2:
        pagina_carica_utenti()
elif st.session_state.deve_cambiare_password:
    pagina_cambio_password()
else:
    pagina_principale()
