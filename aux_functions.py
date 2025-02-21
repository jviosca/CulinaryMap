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

    st.write(f"✅ Nueva clave generada y guardada en {SECRETS_FILE}")
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

@st.cache_data(ttl=0)
def load_data():
    try:
        with open("sitios.json", "rb") as file:
            encrypted_data = file.read()
        decrypted_data = json.loads(FERNET.decrypt(encrypted_data).decode())

        df_sitios = pd.DataFrame(decrypted_data.get("sitios", []))
        df_etiquetas = pd.DataFrame(decrypted_data.get("etiquetas", []))

        # Asegurar que la columna `id` es un número entero y no NULL
        if "id" not in df_etiquetas.columns or df_etiquetas["id"].isnull().all():
            df_etiquetas["id"] = pd.Series(range(1, len(df_etiquetas) + 1))
        else:
            df_etiquetas["id"] = pd.to_numeric(df_etiquetas["id"], errors="coerce").fillna(
                pd.Series(range(1, len(df_etiquetas) + 1))
            ).astype(int)

        # 🔍 Verificación de datos corregidos
        #st.write("🚀 Etiquetas después de cargar (con IDs corregidos):", df_etiquetas.to_dict("records"))

        return df_sitios, df_etiquetas

    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error cargando los datos: {e}")
        return pd.DataFrame(columns=["nombre", "etiquetas", "ubicación", "web", "lat", "lon", "visitado", "puntuación"]), \
               pd.DataFrame(columns=["id", "nombre", "descripcion"])


# 🔐 Función para encriptar y guardar datos
def save_data(df_sitios, df_etiquetas):
    # 🛠️ Asegurar que las etiquetas tengan un id único antes de guardar
    if "id" not in df_etiquetas.columns:
        df_etiquetas["id"] = range(1, len(df_etiquetas) + 1)
    else:
        df_etiquetas["id"] = df_etiquetas["id"].fillna(pd.Series(range(1, len(df_etiquetas) + 1)))

    # Asegurar que etiquetas en `df_sitios` sean listas
    df_sitios["etiquetas"] = df_sitios["etiquetas"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    # 🔍 Depuración: Verificar qué datos se guardarán
    #st.write("🔍 Datos a guardar en sitios.json:", df_sitios.to_dict(orient="records"))
    #st.write("🔍 Datos a guardar en etiquetas.json:", df_etiquetas.to_dict(orient="records"))

    data = {
        "sitios": df_sitios.to_dict(orient="records"),
        "etiquetas": df_etiquetas.to_dict(orient="records")
    }

    encrypted_data = FERNET.encrypt(json.dumps(data, indent=4, ensure_ascii=False).encode())
    with open("sitios.json", "wb") as file:
        file.write(encrypted_data)
    st.cache_data.clear()
    

def reparar_datos_guardados():
    try:
        with open("sitios.json", "rb") as file:
            encrypted_data = file.read()
        decrypted_data = json.loads(FERNET.decrypt(encrypted_data).decode())

        df_sitios = pd.DataFrame(decrypted_data.get("sitios", []))
        df_etiquetas = pd.DataFrame(decrypted_data.get("etiquetas", []))

        # 🛠️ Reparar IDs en `df_etiquetas`
        if "id" not in df_etiquetas.columns or df_etiquetas["id"].isnull().all():
            df_etiquetas["id"] = range(1, len(df_etiquetas) + 1)
        else:
            df_etiquetas["id"] = pd.to_numeric(df_etiquetas["id"], errors="coerce").fillna(range(1, len(df_etiquetas) + 1)).astype(int)

        # 🔍 Verificar cambios
        st.write("✅ Datos corregidos en etiquetas:", df_etiquetas.to_dict("records"))

        # Volver a guardar los datos reparados
        save_data(df_sitios, df_etiquetas)
        st.success("✅ Datos en sitios.json reparados con éxito!")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error al intentar reparar datos: {e}")


def obtener_coordenadas_desde_google_maps(url):
    """
    Extrae las coordenadas (latitud, longitud) desde un enlace de Google Maps.
    Soporta enlaces largos y cortos de la app móvil.
    """
    
    st.write(f"URL de entrada: {url}")  # Debugging: Verificar URL de entrada
    
    # Paso 1: Si es un enlace corto, resolverlo
    if "maps.app.goo.gl" in url or "goo.gl/maps" in url or "g.co/kgs" in url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/",
        }
        try:
            respuesta = requests.get(url, allow_redirects=True, headers=headers)
            url = respuesta.url  # Obtener la URL final
            st.write(f"URL resuelta: {url}")  # Debugging: Verificar URL después de la redirección
        except requests.RequestException as e:
            st.write("Error al resolver URL corta:", e)
            return None
    
    # Paso 2: Buscar coordenadas en la URL con varios patrones
    patrones = [
        r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',  # Formato !3dlat!4dlon (coordenadas reales)
        #r'@(-?\d+\.\d+),(-?\d+\.\d+)',       # Formato @lat,lon
        #r'@(-?\d+\.\d+),(-?\d+\.\d+),\d+z', # Formato @lat,lon,zoomz
        #r'/place/(-?\d+\.\d+),(-?\d+\.\d+)', # Formato /place/lat,lon
        #r'q=(-?\d+\.\d+),(-?\d+\.\d+)',      # Formato q=lat,lon
        #r'll=(-?\d+\.\d+),(-?\d+\.\d+)',     # Formato ll=lat,lon
        #r'daddr=(-?\d+\.\d+),(-?\d+\.\d+)',  # Formato daddr=lat,lon (destino en rutas)
        #r'center=(-?\d+\.\d+),(-?\d+\.\d+)', # Formato center=lat,lon (mapa estático)
        #r'markers=(-?\d+\.\d+),(-?\d+\.\d+)' # Formato markers=lat,lon
    ]
    
    for i, patron in enumerate(patrones):
        match = re.search(patron, url)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            st.write(f"Coordenadas encontradas con el patrón {i + 1}: {lat}, {lon}")  # Debugging
            return lat, lon
    
    st.warning("No se encontraron coordenadas en la URL.")  # Debugging: Caso en que no se encuentran coordenadas
    return None

