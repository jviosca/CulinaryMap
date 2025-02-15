import json
from cryptography.fernet import Fernet
import streamlit as st
import toml
import requests
import re
import base64
import pandas as pd


SECRETS_FILE = ".streamlit/secrets.toml"

def get_secret_key():
    """Obtiene la clave secreta, ya sea desde Streamlit Cloud o desde el archivo local."""
    
    # 🌐 Modo Streamlit Cloud: Usar `st.secrets`
    if "general" in st.secrets and "SECRET_KEY" in st.secrets["general"]:
        return st.secrets["general"]["SECRET_KEY"]

    # 🖥️ Modo Local: Usar `.streamlit/secrets.toml`
    if os.path.exists(SECRETS_FILE):
        secrets = toml.load(SECRETS_FILE)
        if "general" in secrets and "SECRET_KEY" in secrets["general"]:
            return secrets["general"]["SECRET_KEY"]

    # 🚨 Si estamos en Streamlit Cloud y no hay clave, lanzar error
    if not os.path.exists(SECRETS_FILE) and st.secrets._file_path is None:
        st.error("❌ ERROR: Debes configurar SECRET_KEY en Streamlit Cloud (Settings > Secrets)")
        st.stop()

    # 🔐 Generar nueva clave en local si no existe
    secret_key = Fernet.generate_key().decode()
    secrets = {"general": {"SECRET_KEY": secret_key}}

    with open(SECRETS_FILE, "w") as f:
        toml.dump(secrets, f)

    print(f"✅ Nueva clave generada y guardada en {SECRETS_FILE}")
    return secret_key

# 🔑 Obtener la clave secreta
SECRET_KEY = get_secret_key()

# 📌 Inicializar Fernet con la clave correcta
FERNET = Fernet(SECRET_KEY.encode())
st.write("🔐 Clave de cifrado cargada correctamente.")


def authenticate():
    """Verifica la contraseña ingresada."""
    # Cargar la contraseña desde `secrets.toml`
    correct_password = st.secrets["authentication"]["admin_password"]
    
    if "password" in st.session_state and st.session_state.password == correct_password:
        st.session_state.authenticated = True
        st.session_state.pop("password")  # Borrar la contraseña por seguridad
    else:
        st.error("Contraseña incorrecta. Intenta nuevamente.")

# Cargar datos desde JSON cifrado
def load_data_old():
    try:
        with open("sitios.json", "rb") as f:
            encrypted_data = f.read()
        decrypted_data = json.loads(cipher.decrypt(encrypted_data).decode())
    except:
        decrypted_data = []  # Si no hay datos, inicializar vacío
    return decrypted_data
    
def load_data_old2():
    try:
        with open("sitios.json", "rb") as file:
            encrypted_data = file.read()
        decrypted_data = FERNET.decrypt(encrypted_data).decode()
        return pd.DataFrame(json.loads(decrypted_data))
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame(columns=["nombre", "etiquetas", "enlace", "lat", "lon", "visitado", "puntuación"])

def load_data():
    try:
        with open("sitios.json", "rb") as file:
            encrypted_data = file.read()
        decrypted_data = FERNET.decrypt(encrypted_data).decode()
        df = pd.DataFrame(json.loads(decrypted_data))

        # ✅ Asegurar que la columna "enlace" y otras siempre existan
        for col in ["nombre", "etiquetas", "enlace", "lat", "lon", "visitado", "puntuación"]:
            if col not in df.columns:
                df[col] = "" if col == "enlace" else None  # Valor por defecto

        return df
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame(columns=["nombre", "etiquetas", "enlace", "lat", "lon", "visitado", "puntuación"])

# Guardar datos en JSON cifrado
def save_data_old(df):
    data = df.to_dict(orient="records")
    encrypted_data = cipher.encrypt(json.dumps(data).encode())
    encrypted_data = FERNET.encrypt(json.dumps(data, indent=4, ensure_ascii=False).encode())
    with open("sitios.json", "wb") as f:
        f.write(encrypted_data)

# 🔐 Función para encriptar y guardar datos
def save_data(df):
    data = df.to_dict(orient="records")
    encrypted_data = FERNET.encrypt(json.dumps(data, indent=4, ensure_ascii=False).encode())
    with open("sitios.json", "wb") as file:
        file.write(encrypted_data)

def obtener_coordenadas_desde_google_maps(url):
    """
    Extrae las coordenadas (latitud, longitud) desde un enlace de Google Maps.
    Soporta enlaces largos y cortos de la app móvil.
    """
    
    print(f"URL de entrada: {url}")  # Debugging: Verificar URL de entrada
    
    # Paso 1: Si es un enlace corto, resolverlo
    if "maps.app.goo.gl" in url:
        try:
            respuesta = requests.get(url, allow_redirects=True)
            url = respuesta.url  # Obtener la URL final
            st.write(f"URL resuelta: {url}")  # Debugging: Verificar URL después de la redirección
        except requests.RequestException as e:
            st.write("Error al resolver URL corta:", e)
            return None
    
    # Paso 2: Buscar coordenadas en la URL
    patron = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
    match = re.search(patron, url)
    
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        st.write(f"Coordenadas encontradas con el primer patrón: {lat}, {lon}")  # Debugging
        return lat, lon
    
    # Alternativa para otra estructura de URL
    patron_alt = r'/place/(-?\d+\.\d+),(-?\d+\.\d+)'
    match_alt = re.search(patron_alt, url)
    
    if match_alt:
        lat, lon = float(match_alt.group(1)), float(match_alt.group(2))
        st.write(f"Coordenadas encontradas con el segundo patrón: {lat}, {lon}")  # Debugging
        return lat, lon
    
    st.write("No se encontraron coordenadas en la URL.")  # Debugging: Caso en que no se encuentran coordenadas
    return None

