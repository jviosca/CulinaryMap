import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import pandas as pd
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

    # Mapa centrado en una ubicación por defecto (Valencia, España)
    location = [39.4596968, -0.408261]  
    
    if not sitios.empty:
        primer_sitio = sitios.dropna(subset=["lat", "lon"]).iloc[0] if not sitios.dropna(subset=["lat", "lon"]).empty else None
        if primer_sitio is not None:
            location = [primer_sitio["lat"], primer_sitio["lon"]]

    # Crear mapa con Folium
    m = folium.Map(location=location, zoom_start=12)

    # Agregar marcadores de sitios
    for _, sitio in sitios.iterrows():
        if pd.notna(sitio["lat"]) and pd.notna(sitio["lon"]):  # Asegura que lat/lon no sean NaN
            folium.Marker(
                location=[sitio["lat"], sitio["lon"]],
                popup=f"<a href='{sitio.get('enlace', '#')}' target='_blank'>{sitio['nombre']} ({sitio.get('puntuación', 'N/A')}⭐)</a>",
                tooltip=sitio["nombre"],
                icon=folium.Icon(color="blue" if sitio.get("visitado", False) else "gray")
            ).add_to(m)

    # Mostrar el mapa en Streamlit
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
    
    df = load_data()
    
    # ➕ Agregar un nuevo sitio
    with st.expander("➕ Agregar un nuevo sitio"):
        nombre = st.text_input("Nombre del sitio")
        etiquetas = st.text_input("Etiquetas (separadas por comas)")
        link = st.text_input("Enlace de Google Maps")
        lat, lon = None, None

        if link:
            coordenadas = obtener_coordenadas_desde_google_maps(link)
            if coordenadas:
                lat, lon = coordenadas
                st.success(f"Coordenadas extraídas: 🌍 Latitud: {lat}, Longitud: {lon}")
            else:
                st.error("No se pudieron obtener coordenadas del enlace.")

        visitado = st.checkbox("Visitado")
        # Slider de puntuación (solo aparece si el sitio fue visitado)
        puntuacion = 1  # Por defecto, 1
        if visitado:
            puntuacion = st.slider("Puntuación", 1, 5, 1)

        if st.button("Añadir Sitio"):
            nuevo_sitio = pd.DataFrame([{
                "nombre": nombre,
                "etiquetas": etiquetas,
                "enlace": link,
                "lat": lat,
                "lon": lon,
                "visitado": visitado,
                "puntuación": puntuacion
            }])
            df = pd.concat([df, nuevo_sitio], ignore_index=True)
            save_data(df)
            st.success("✅ Sitio añadido correctamente!")
            st.rerun()

    # 📋 Editar sitios
    st.subheader("📋 Editar Sitios")
    # Guardamos una copia de las coordenadas antes de eliminarlas
    lat_lon_data = df[["lat", "lon"]].copy()
    # Crear un DataFrame sin índice y sin las columnas lat/lon
    df_editable = df.drop(columns=["lat", "lon"], errors="ignore").reset_index(drop=True)

    edited_df = st.data_editor(
        df_editable,
        column_config={
            "visitado": st.column_config.CheckboxColumn("Visitado"),
            "puntuación": st.column_config.NumberColumn("Puntuación", min_value=1, max_value=5),
            "enlace": st.column_config.LinkColumn("Enlace a Google Maps")
        },
        use_container_width=True,
        hide_index=True 
    )

    if st.button("Guardar cambios"):
        # Restaurar las coordenadas antes de guardar
        edited_df = edited_df.merge(lat_lon_data, left_index=True, right_index=True, how="left")
        save_data(edited_df)
        st.success("✅ Datos guardados correctamente")
        st.rerun()

    # 🗑️ Eliminar un sitio
    st.subheader("🗑️ Eliminar un sitio")
    sitio_a_eliminar = st.selectbox("Selecciona un sitio para eliminar", df["nombre"].tolist())

    if st.button("Eliminar sitio"):
        df = df[df["nombre"] != sitio_a_eliminar]
        save_data(df)
        st.success(f"✅ Sitio '{sitio_a_eliminar}' eliminado")
        st.rerun()

    # 🔒 Cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.rerun()

