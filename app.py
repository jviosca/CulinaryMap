import streamlit as st
import folium
from streamlit_folium import st_folium
import os
from aux_functions import load_data, save_data

# Cargar datos
sitios = load_data()

# Página de selección
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página", ["📍 Mapa", "🔑 Admin"])

if page == "📍 Mapa":
    st.title("Mapa de Sitios de Comida")
    
    # Mapa centrado en la primera ubicación o por defecto
    location = [40.416775, -3.703790]  # Madrid, España
    if sitios:
        location = [sitios[0]["lat"], sitios[0]["lon"]]
    
    m = folium.Map(location=location, zoom_start=12)
    for sitio in sitios:
        folium.Marker(
            location=[sitio["lat"], sitio["lon"]],
            popup=f"<a href='{sitio['link']}' target='_blank'>{sitio['nombre']} ({sitio['puntuacion']}⭐)</a>",
            tooltip=sitio["nombre"],
            icon=folium.Icon(color="blue" if sitio["visitado"] else "gray")
        ).add_to(m)
    
    st_folium(m, width=700, height=500)

elif page == "🔑 Admin":
    st.title("Administración de Sitios")
    
    # Autenticación simple
    PASSWORD_FILE = "admin_password.txt"
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            correct_password = f.read().strip()
    else:
        correct_password = "admin123"  # Contraseña por defecto si no existe el archivo
    
    password = st.text_input("Introduce la contraseña", type="password")
    
    if password == correct_password:
        st.success("Acceso concedido")
        nombre = st.text_input("Nombre del sitio")
        etiquetas = st.text_input("Etiquetas (separadas por comas)")
        link = st.text_input("Enlace de Google Maps")
        lat = st.number_input("Latitud", format="%.6f")
        lon = st.number_input("Longitud", format="%.6f")
        visitado = st.checkbox("Visitado")
        puntuacion = st.slider("Puntuación", 1, 5, 3)
        
        if st.button("Añadir Sitio"):
            nuevo_sitio = {"nombre": nombre, "etiquetas": etiquetas, "link": link, "lat": lat, "lon": lon, "visitado": visitado, "puntuacion": puntuacion}
            sitios.append(nuevo_sitio)
            save_data(sitios)
            st.success("Sitio añadido correctamente!")
            st.experimental_rerun()
        
        st.subheader("Sitios Guardados")
        for sitio in sitios:
            st.write(f"**{sitio['nombre']}** - {sitio['puntuacion']}⭐ - {'✔ Visitado' if sitio['visitado'] else '❌ No visitado'} - [Abrir en Google Maps]({sitio['link']})")
    else:
        st.error("Contraseña incorrecta")
