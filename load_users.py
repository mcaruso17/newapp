import pandas as pd
import secrets
import string
from database import get_connection, init_database
from auth import Authenticator
from config import PASSWORD_LENGTH, EMAIL_DOMAIN, RUOLI, UFFICI

def genera_email(nominativo: str) -> str:
    """Da 'Rossi Mario' genera 'm.rossi@mef.gov.it'"""
    parti = nominativo.strip().split()
    cognome = parti[0].lower()
    nome = parti[1].lower() if len(parti) > 1 else ""
    return f"{nome[0]}.{cognome}@{EMAIL_DOMAIN}"

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
