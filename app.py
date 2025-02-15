import streamlit as st
import folium
from streamlit_folium import st_folium
import os
from aux_functions import (
                        load_data, 
                        save_data, 
                        authenticate,
                        obtener_coordenadas_desde_google_maps
)

# Cargar datos
sitios = load_data()

# Página de selección
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página", ["📍 Mapa", "🔑 Admin"])

if page == "📍 Mapa":
    st.title("Mapa de Sitios de Comida")
    
    # Mapa centrado en la primera ubicación válida o por defecto
    location = [39.4596968, -0.408261]  # Valencia, España
    
    if sitios:
        primer_sitio = next((s for s in sitios if "lat" in s and "lon" in s and s["lat"] is not None and s["lon"] is not None), None)
        if primer_sitio:
            location = [primer_sitio["lat"], primer_sitio["lon"]]
    
    m = folium.Map(location=location, zoom_start=12)
    
    for sitio in sitios:
        if "lat" in sitio and "lon" in sitio and sitio["lat"] is not None and sitio["lon"] is not None:
            folium.Marker(
                location=[sitio["lat"], sitio["lon"]],
                popup=f"<a href='{sitio['link']}' target='_blank'>{sitio['nombre']} ({sitio['puntuacion']}⭐)</a>",
                tooltip=sitio["nombre"],
                icon=folium.Icon(color="blue" if sitio["visitado"] else "gray")
            ).add_to(m)
    
    st_folium(m, width=700, height=500)

elif page == "🔑 Admin":
    # Verificar si el usuario ya está autenticado
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Página de Administración
    if not st.session_state.authenticated:
        st.title("🔑 Administración de Sitios")
        st.subheader("Autenticación requerida")
        st.text_input("Introduce la contraseña", type="password", key="password", on_change=authenticate)
        st.stop()  # Detiene la ejecución si no está autenticado

    # Si está autenticado, mostrar el contenido de la administración
    st.title("🔑 Administración de Sitios")
    st.success("¡Acceso concedido!")

    nombre = st.text_input("Nombre del sitio")
    etiquetas = st.text_input("Etiquetas (separadas por comas)")
    link = st.text_input("Enlace de Google Maps")
    # Inicializar variables para evitar errores
    lat, lon = None, None
    # Procesar la URL cuando el usuario la ingrese
    if link:
        coordenadas = obtener_coordenadas_desde_google_maps(link)
        if coordenadas:
            lat, lon = coordenadas
            st.success(f"Coordenadas extraídas: 🌍 Latitud: {lat}, Longitud: {lon}")
        else:
            st.error("No se pudieron obtener coordenadas del enlace.")
    #lat = st.number_input("Latitud", format="%.6f")
    #lon = st.number_input("Longitud", format="%.6f")
    visitado = st.checkbox("Visitado")
    puntuacion = st.slider("Puntuación", 1, 5, 3)

    if st.button("Añadir Sitio"):
        nuevo_sitio = {
            "nombre": nombre,
            "etiquetas": etiquetas,
            "link": link,
            "lat": lat,
            "lon": lon,
            "visitado": visitado,
            "puntuacion": puntuacion,
        }
        sitios.append(nuevo_sitio)
        save_data(sitios)
        st.success("Sitio añadido correctamente!")
        st.rerun()

    st.subheader("Sitios Guardados")
    for sitio in sitios:
        st.write(f"**{sitio['nombre']}** - {sitio['puntuacion']}⭐ - {'✔ Visitado' if sitio['visitado'] else '❌ No visitado'} - [Abrir en Google Maps]({sitio['link']})")

    # Botón para cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.experimental_rerun()

