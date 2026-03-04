import pandas as pd
import secrets
import string
from database import get_connection, init_database
from auth import Authenticator
from config import PASSWORD_LENGTH, EMAIL_DOMAIN, RUOLI, UFFICI

def genera_email(nominativo: str) -> str:
    """Da 'Rossi Mario' genera 'mario.rossi@mef.gov.it'"""
    nominativo = str(nominativo).strip()
    parti = nominativo.split()
    cognome = parti[0].lower()
    nome = parti[1].lower() if len(parti) > 1 else ""
    return f"{nome}.{cognome}@{EMAIL_DOMAIN}"

def genera_password(length: int = PASSWORD_LENGTH) -> str:
    """Genera una password casuale sicura"""
    caratteri = string.ascii_letters + string.digits + "!@#$%"
    while True:
        password = ''.join(secrets.choice(caratteri) for _ in range(length))
        # Verifica che abbia almeno una maiuscola, una minuscola, un numero e un simbolo
        if (any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%" for c in password)):
            return password
def carica_utenti(file_excel: str):
    """Legge l'Excel e carica gli utenti nel database"""
    # Inizializza il database (crea la tabella se non esiste)
    init_database()

    # Legge l'Excel
    df = pd.read_excel(file_excel)

    # Lista per salvare le credenziali da comunicare agli utenti
    credenziali = []

    for _, riga in df.iterrows():
        nominativo = riga["nominativo"]
        email = genera_email(nominativo)
        password = genera_password()

        # Hasha la password
        pw_hash, salt = Authenticator.hash_password(password)
        stored = f"{pw_hash}:{salt}"

        with get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO users 
                    (nominativo, email, password_hash, ruolo, ufficio, stanza, interno, cellulare)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        nominativo,
                        email,
                        stored,
                        riga["ruolo"],
                        str(riga["ufficio"]),
                        str(riga.get("stanza", "")),
                        str(riga.get("interno", "")),
                        str(riga.get("cellulare", ""))
                    )
                )
                credenziali.append({
                    "nominativo": nominativo,
                    "email": email,
                    "password": password  # in chiaro, solo per comunicarla
                })
                print(f"Creato: {nominativo} -> {email}")
            except Exception as e:
                print(f"Errore per {nominativo}: {e}")

    # Salva le credenziali in un file da stampare e poi eliminare
    if credenziali:
        df_cred = pd.DataFrame(credenziali)
        df_cred.to_excel("credenziali_temporanee.xlsx", index=False)
        print(f"\nCaricati {len(credenziali)} utenti")
        print("Credenziali salvate in 'credenziali_temporanee.xlsx'")
        print("IMPORTANTE: stampa questo file, distribuiscilo e poi ELIMINALO!")

if __name__ == "__main__":
    carica_utenti("personale.xlsx")
