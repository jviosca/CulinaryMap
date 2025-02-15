import json
from cryptography.fernet import Fernet
import streamlit as st
import toml 

# Clave para cifrar y descifrar JSON (guardar en un lugar seguro en producción)
# Cargar los secretos manualmente si no están en Streamlit Cloud
if "SECRET_KEY" not in st.secrets:
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        SECRET_KEY = secrets["general"]["SECRET_KEY"].encode()
    except Exception as e:
        st.error(f"No se pudo cargar SECRET_KEY: {e}")
        SECRET_KEY = None
else:
    SECRET_KEY = st.secrets["SECRET_KEY"].encode()

# Si no hay clave, lanza un error
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no está configurada correctamente.")

cipher = Fernet(SECRET_KEY)

# Cargar datos desde JSON cifrado
def load_data():
    try:
        with open("sitios.json", "rb") as f:
            encrypted_data = f.read()
        decrypted_data = json.loads(cipher.decrypt(encrypted_data).decode())
    except:
        decrypted_data = []  # Si no hay datos, inicializar vacío
    return decrypted_data

# Guardar datos en JSON cifrado
def save_data(data):
    encrypted_data = cipher.encrypt(json.dumps(data).encode())
    with open("sitios.json", "wb") as f:
        f.write(encrypted_data)
