import json
from cryptography.fernet import Fernet
import streamlit as st
import toml
import requests
import re

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

