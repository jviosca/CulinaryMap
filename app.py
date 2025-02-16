import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import pandas as pd
import numpy as np
from aux_functions import (
                        load_data, 
                        save_data, 
                        authenticate,
                        obtener_coordenadas_desde_google_maps
)

# Cargar datos
sitios, etiquetas = load_data()

# Página de selección
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página", ["📍 Mapa", "🔑 Admin"])
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.markdown("### Más info en [GitHub](https://github.com/jviosca/CulinaryMap)")

if page == "📍 Mapa":
    st.title("CulinaryMap")
    st.subheader("Recomendaciones culinarias")

    # Mapa centrado en una ubicación por defecto (Valencia, España)
    location = [39.4596968, -0.408261]  
    
    if not sitios.empty:
        primer_sitio = sitios.dropna(subset=["lat", "lon"]).iloc[0] if not sitios.dropna(subset=["lat", "lon"]).empty else None
        if primer_sitio is not None:
            location = [primer_sitio["lat"], primer_sitio["lon"]]
    col1, col2, col3 = st.columns(3)
    
    # Filtro de etiquetas arriba del mapa
    with col1:
        etiquetas_dict = {etiqueta['id']: etiqueta['nombre'] for etiqueta in etiquetas.to_dict('records')} if isinstance(etiquetas, pd.DataFrame) else {etiqueta['id']: etiqueta['nombre'] for etiqueta in etiquetas} if isinstance(etiquetas, list) and all(isinstance(etiqueta, dict) for etiqueta in etiquetas) else {}
        etiquetas_seleccionadas = st.multiselect("Filtrar por etiquetas", list(etiquetas_dict.values()))
    with col2: 
        puntuacion_minima = st.selectbox("Puntuación mínima", options=[None, 1, 2, 3, 4, 5], index=0, format_func=lambda x: "Sin filtro" if x is None else str(x))
    with col3:
        visitado = st.checkbox("Mostrar solo visitados")
    # Aplicar filtros
    if etiquetas_seleccionadas:
        sitios = sitios[sitios["etiquetas"].apply(lambda x: any(tag in x for tag in etiquetas_seleccionadas))]
    if puntuacion_minima is not None:
        sitios = sitios[(sitios["puntuación"].notna()) & (sitios["puntuación"] >= puntuacion_minima)]
    if visitado:
        sitios = sitios[sitios["visitado"] == True]    
    

    # Crear mapa con Folium
    m = folium.Map(location=location, zoom_start=12)

    # Agregar marcadores de sitios
    for _, sitio in sitios.iterrows():
        if pd.notna(sitio["lat"]) and pd.notna(sitio["lon"]):  # Asegura que lat/lon no sean NaN
            # Construir el popup dinámicamente
            popup_text = f"<a href='{sitio.get('ubicación', '#')}' target='_blank'>{sitio['nombre']}</a>"
            # Agregar estrellas solo si la puntuación no es None o NaN
            if pd.notna(sitio.get("puntuación")):
                popup_text += f" ({sitio['puntuación']}⭐)"
            if pd.notna(sitio.get("web")):
                popup_text += f"<a href='{sitio.get('web', '#')}' target='_blank'>{sitio['web']}</a>"
            folium.Marker(
                location=[sitio["lat"], sitio["lon"]],
                popup = popup_text,
                tooltip = sitio["nombre"],
                icon = folium.Icon(color="blue" if sitio.get("visitado", False) else "gray")
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
    
    df_sitios, df_etiquetas = load_data()

    # ➕ Agregar una etiqueta
    with st.expander("➕ Agregar una nueva etiqueta"):
        nombre_etiqueta = st.text_input("Nombre de la etiqueta")
        descripcion_etiqueta = st.text_input("Descripción de la etiqueta")
        if st.button("Añadir Etiqueta"):
            nueva_etiqueta = pd.DataFrame([{ "id": len(df_etiquetas) + 1, "nombre": nombre_etiqueta, "descripcion": descripcion_etiqueta }])
            df_etiquetas = pd.concat([df_etiquetas, nueva_etiqueta], ignore_index=True)
            save_data(df_sitios, df_etiquetas)
            st.success("✅ Etiqueta añadida correctamente!")
            st.rerun()
    
    # ➕ Agregar un nuevo sitio
    with st.expander("➕ Agregar un nuevo sitio"):
        nombre = st.text_input("Nombre del sitio")
        etiquetas_seleccionadas = st.multiselect("Etiquetas", df_etiquetas["nombre"].tolist())
        map_link = st.text_input("Enlace de Google Maps", key="link")
        web = st.text_input("Web del Sitio (opcional)")
        lat, lon = None, None

        if map_link:
            coordenadas = obtener_coordenadas_desde_google_maps(map_link)
            if coordenadas:
                lat, lon = coordenadas
                st.success(f"Coordenadas extraídas: 🌍 Latitud: {lat}, Longitud: {lon}")
            else:
                st.error("No se pudieron obtener coordenadas del enlace.")

        visitado = st.checkbox("Visitado")
        # Slider de puntuación (solo aparece si el sitio fue visitado)
        puntuacion = None  # Por defecto, 1
        if visitado:
            puntuacion = st.slider("Puntuación", 1, 5, value=1, step=0.5)

        if st.button("Añadir Sitio"):
            if not map_link or lat is None or lon is None:
                st.error("No se puede añadir un sitio sin un enlace válido de Google Maps con coordenadas extraídas.")
            else:
                nuevo_sitio = pd.DataFrame([{
                    "nombre": nombre,
                    "etiquetas": etiquetas_seleccionadas,
                    "ubicación": map_link,
                    "web": web,
                    "lat": lat,
                    "lon": lon,
                    "visitado": visitado,
                    "puntuación": puntuacion
                }])
                df_sitios = pd.concat([df_sitios, nuevo_sitio], ignore_index=True)
                save_data(df_sitios, df_etiquetas)
                st.success("✅ Sitio añadido correctamente!")
                st.rerun()

    # Mostrar y editar etiquetas
    st.subheader("📋 Editar Etiquetas")
    edited_etiquetas = st.data_editor(df_etiquetas.reset_index(drop=True), use_container_width=True, hide_index=True)
    if st.button("Guardar cambios en etiquetas"):
        df_etiquetas = edited_etiquetas  # Asegurar que los cambios se reflejen en el dataframe principal
        save_data(df_sitios, df_etiqueta)
        st.success("✅ Etiquetas actualizadas correctamente!")
        st.rerun()

    # 📋 Editar sitios
    st.subheader("📋 Editar Sitios")
    # Guardamos una copia de las coordenadas antes de eliminarlas
    lat_lon_data = df_sitios[["lat", "lon"]].copy()
    # Crear un DataFrame sin índice y sin las columnas lat/lon
    df_editable = df_sitios.drop(columns=["lat", "lon"], errors="ignore").reset_index(drop=True)

    edited_df = st.data_editor(
        df_editable,
        column_config={
            "visitado": st.column_config.CheckboxColumn("Visitado"),
            "puntuación": st.column_config.NumberColumn("Puntuación", min_value=1, max_value=5),
            "ubicación": st.column_config.LinkColumn("Enlace a Google Maps", width="small"),
            "web": st.column_config.LinkColumn("Web del Sitio", width="small") 
        },
        use_container_width=True,
        hide_index=True 
    )
    # Ajustar puntuación a None si "Visitado" es False
    for i in range(len(edited_df)):
        if not edited_df.at[i, "visitado"]:  # Si "visitado" es False
            edited_df.at[i, "puntuación"] = None  # Poner puntuación en None

    if st.button("Guardar cambios"):
        # Restaurar las coordenadas antes de guardar
        edited_df = edited_df.merge(lat_lon_data, left_index=True, right_index=True, how="left")
        df_sitios = edited_df  # Asegurar que es el df principal actualizado
        save_data(df_sitios, df_etiquetas)
        st.success("✅ Datos guardados correctamente")
        st.rerun()

    # 🗑️ Eliminar un sitio
    st.subheader("🗑️ Eliminar un sitio")
    if not df_sitios.empty:
        sitio_a_eliminar = st.selectbox("Selecciona un sitio para eliminar", df_sitios["nombre"].tolist())

        if st.button("Eliminar sitio"):
            df_sitios = df_sitios[df_sitios["nombre"] != sitio_a_eliminar]
            save_data(df_sitios,df_etiquetas)
            st.success(f"✅ Sitio '{sitio_a_eliminar}' eliminado")
            st.rerun()
    else:
        st.info("No hay sitios para eliminar.")

    # 🔒 Cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.rerun()

