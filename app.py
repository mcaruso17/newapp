import streamlit as st
from auth import Authenticator
from permission import puo_modificare, puo_visualizzare, is_admin, richiedi_permesso
from database import init_database
from database import init_database, get_connection

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
if not st.session_state.authenticated:
    pagina_login()
elif st.session_state.deve_cambiare_password:
    pagina_cambio_password()
else:
    pagina_principale()
