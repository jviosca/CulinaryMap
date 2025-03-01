import streamlit as st
st.set_page_config(
    page_title="CulinaryMap",  # Título de la pestaña en el navegador
    page_icon="🍽️",  # Icono de la pestaña
    layout="wide",  # Configuración amplia
    initial_sidebar_state="collapsed"  # Barra lateral expandida por defecto
)

import folium
#from streamlit_folium import folium_static
from streamlit_folium import st_folium
import os
import pandas as pd
import numpy as np
from streamlit_js_eval import get_geolocation
import time
from aux_functions import (
                        load_data, 
                        save_data, 
                        authenticate,
                        obtener_coordenadas_desde_google_maps,
                        reparar_datos_guardados,
                        calcular_conteo_etiquetas
)

#if st.button("🔄 Reparar datos guardados"): # si etiquetas no tienen id, no se muestran todas
#    reparar_datos_guardados()

# Cargar datos
sitios, etiquetas = load_data()
sitios = sitios.sort_values(by="nombre", ascending=True)
etiquetas = etiquetas.sort_values(by="nombre", ascending=True)

# Inicializar el estado de la página si no existe
if "page" not in st.session_state:
    st.session_state["page"] = "📍 Mapa"  # Página predeterminada

# Asegurar que "sidebar_navigation" existe en session_state antes de usarlo
if "sidebar_navigation" not in st.session_state:
    st.session_state["sidebar_navigation"] = "📍 Mapa"

# Si hay una página pendiente de cambio, aplicarla antes de mostrar el sidebar
if "next_page" in st.session_state:
    st.session_state["page"] = st.session_state["next_page"]
    del st.session_state["next_page"]  # Borrar variable después de usarla
    st.rerun()  # 🔥 Recargar para aplicar el cambio en el `radio`

# 📌 Forzar actualización del `radio` usando `key`
page = st.sidebar.radio(
    "Selecciona una página", 
    ["📍 Mapa", "🔑 Admin"], 
    index=["📍 Mapa", "🔑 Admin"].index(st.session_state["page"]),
    key="sidebar_navigation"  # Agregar un `key` evita conflictos en `st.session_state`
)

# Guardar la selección actual en `st.session_state["page"]`
st.session_state["page"] = page


#page = st.sidebar.radio("Selecciona una página", ["📍 Mapa", "🔑 Admin"])
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.markdown("### Más info en [GitHub](https://github.com/jviosca/CulinaryMap)")

import streamlit as st
import pandas as pd
import time
import folium
from streamlit_js_eval import get_geolocation  # Importación de geolocalización

if page == "📍 Mapa":
    st.title("CulinaryMap")
    st.subheader("Recomendaciones culinarias")

    # Mensaje destacado
    st.markdown("""
    ---
    **❗ ¿Ubicación incorrecta?**  
    *Si encuentras un sitio mal ubicado en el mapa, envíame un 
    📩 [correo](mailto:jviosca@gmail.com)*
    """)

    # Checkbox para mostrar ubicación del usuario
    mostrar_mi_ubicacion = st.checkbox("📍 Mostrar mi ubicación (en móvil activar GPS)", 
                                       value=st.session_state.get("mostrar_mi_ubicacion", False))

    # Guardar la preferencia del usuario
    st.session_state["mostrar_mi_ubicacion"] = mostrar_mi_ubicacion

    # Obtener geolocalización solo si el usuario lo activa y aún no la tenemos
    if mostrar_mi_ubicacion:
        if "user_location" not in st.session_state:
            ubicacion = get_geolocation()

            if ubicacion and isinstance(ubicacion, dict) and "coords" in ubicacion:
                coords = ubicacion["coords"]
                if "latitude" in coords and "longitude" in coords:
                    st.session_state["user_location"] = [coords["latitude"], coords["longitude"]]
                    st.success("✅ Ubicación obtenida correctamente.")
                else:
                    st.warning("⏳ Ubicación en proceso... Si tarda demasiado, revisa los permisos del navegador.")
            else:
                st.warning("⏳ Esperando ubicación... Puede que necesites habilitar el GPS.")
            time.sleep(1)

    # 📌 Asegurarse de que centro_mapa esté en session_state
    if "centro_mapa" not in st.session_state:
        st.session_state["centro_mapa"] = [39.4699, -0.3763]  # Valor por defecto (Valencia)

    # 1️⃣ Si el usuario buscó un sitio, actualizar centro_mapa
    if "busqueda_ubicacion" in st.session_state:
        st.session_state["centro_mapa"] = [
            st.session_state["busqueda_ubicacion"]["lat"], 
            st.session_state["busqueda_ubicacion"]["lon"]
        ]
        del st.session_state["busqueda_ubicacion"]  # ✅ Borrar después de usar para evitar conflictos

    # 2️⃣ Si el usuario activó "Mostrar mi ubicación", actualizar centro_mapa
    elif mostrar_mi_ubicacion and "user_location" in st.session_state:
        st.session_state["centro_mapa"] = st.session_state["user_location"]


    # Filtro de etiquetas arriba del mapa
    col1, col2, col3 = st.columns(3)
    with col1:
        #etiquetas_dict = {etiqueta['id']: etiqueta['nombre'] for etiqueta in etiquetas.to_dict('records')} if isinstance(etiquetas, pd.DataFrame) else {etiqueta['id']: etiqueta['nombre'] for etiqueta in etiquetas} if isinstance(etiquetas, list) and all(isinstance(etiqueta, dict) for etiqueta in etiquetas) else {}
        if isinstance(etiquetas, pd.DataFrame):
            etiquetas_dict = {etiqueta["id"]: etiqueta["nombre"] for etiqueta in etiquetas.to_dict("records")}
        elif isinstance(etiquetas, list) and all(isinstance(etiqueta, dict) for etiqueta in etiquetas):
            etiquetas_dict = {etiqueta["id"]: etiqueta["nombre"] for etiqueta in etiquetas}
        else:
            etiquetas_dict = {}
        #st.write("Etiquetas disponibles en el filtro:", etiquetas_dict)
        etiquetas_seleccionadas = st.multiselect("Filtrar por etiquetas", list(etiquetas_dict.values()))
    with col2: 
        puntuacion_minima = st.selectbox("Puntuación mínima", options=[None, 1, 2, 3, 4, 5], index=0, format_func=lambda x: "Sin filtro" if x is None else str(x))
    with col3:
        #visitado = st.checkbox("Mostrar solo visitados")
        filtro_visitados = st.selectbox("Filtrar por visitas", 
                ["No filtrar", "Visitados", "No visitados"])
                
    # Aplicar filtros al DataFrame de sitios
    sitios_filtrados = sitios.copy() # Mantener una copia sin modificar para que muestre todos si no se busca nada
    # Aplicar filtros
    if etiquetas_seleccionadas:
        sitios_filtrados = sitios_filtrados[sitios_filtrados["etiquetas"].apply(lambda x: isinstance(x, list) and any(tag in x for tag in etiquetas_seleccionadas))]
    if puntuacion_minima is not None:
        sitios_filtrados = sitios_filtrados[(sitios_filtrados["puntuación"].notna()) & (sitios_filtrados["puntuación"] >= puntuacion_minima)]
    if filtro_visitados == "Visitados":
        sitios_filtrados = sitios_filtrados[sitios_filtrados["visitado"] == True]
    elif filtro_visitados == "No visitados":
        sitios_filtrados = sitios_filtrados[sitios_filtrados["visitado"] == False]

    # 📍 Campo de búsqueda de sitios
    busqueda = st.text_input("🔍 Buscar sitio por nombre:")
    if busqueda:
        sitios_filtrados = sitios_filtrados[sitios_filtrados["nombre"].str.contains(busqueda, case=False, na=False)]
        if not sitios_filtrados.empty:
            # Actualizar centro_mapa directamente sin usar mapa_centrado
            st.session_state["centro_mapa"] = [sitios_filtrados.iloc[0]["lat"], sitios_filtrados.iloc[0]["lon"]]
            st.session_state["busqueda_ubicacion"] = {
                "lat": sitios_filtrados.iloc[0]["lat"],
                "lon": sitios_filtrados.iloc[0]["lon"]
            }
        else:
            st.warning("❌ No se encontró ningún sitio con ese nombre.")

    
    # Mostrar cuántos sitios coinciden con la búsqueda
    st.write(f"Resultados encontrados: {len(sitios_filtrados)}")

    # 📍 Crear el mapa con Folium con la última ubicación registrada en centro_mapa
    m = folium.Map(location=st.session_state["centro_mapa"], zoom_start=13)

    # Agregar marcadores de sitios
    for _, sitio in sitios_filtrados.iterrows():
        if pd.notna(sitio["lat"]) and pd.notna(sitio["lon"]):  # Asegura que lat/lon no sean NaN
            # Construir el popup dinámicamente con valores seguros
            popup_text = f"<a href='{sitio.get('ubicación', '#') or '#'}' target='_blank'>{sitio['nombre']}</a>"

            # Agregar estrellas solo si la puntuación no es None o NaN
            if pd.notna(sitio.get("puntuación")):
                popup_text += f" ({sitio['puntuación']}⭐)"

            # Agregar enlace a la web solo si está presente
            if pd.notna(sitio.get("web")) and sitio.get("web"):
                popup_text += f"<br><a href='{sitio.get('web')}' target='_blank'>🌍 Sitio Web</a>"

            # Agregar etiquetas si existen
            etiquetas = sitio.get("etiquetas")
            if isinstance(etiquetas, list) and etiquetas:  # Asegura que sea una lista válida
                etiquetas_text = ", ".join(etq.strip() for etq in etiquetas if isinstance(etq, str))
                popup_text += f"<br>🏷️ {etiquetas_text}"

            # Agregar marcador al mapa
            folium.Marker(
                location=[sitio["lat"], sitio["lon"]],
                popup=popup_text,
                tooltip=sitio["nombre"],
                icon=folium.Icon(color="blue" if sitio.get("visitado", False) else "gray")
            ).add_to(m)


    # Mostrar el mapa en Streamlit
    col1, col2, col3 = st.columns([0.2,0.6,0.2])
    # Inyectar CSS para establecer el ancho máximo
    st.markdown("""
    <style>
        .map-container {
            width: 90%;
            max-width: 900px;  /* Ajusta esto si quieres un límite en PC */
            margin: auto;
        }
        iframe {
            width: 100% !important;
            height: 500px !important;  /* Ajustar altura */
        }
        @media (max-width: 768px) {
            iframe {
                height: 350px !important;  /* Reducir altura en móviles */
            }
        }
    </style>
    """, unsafe_allow_html=True)
    with col2:
        # Envolver el mapa en un div con la clase "map-container"
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        #folium_static(m)
        st_folium(m)
        st.markdown('</div>', unsafe_allow_html=True)


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
    
    #df_sitios, df_etiquetas = load_data()
    df_sitios = sitios
    df_etiquetas = etiquetas

    # ➕ Agregar una etiqueta
    with st.expander("➕ Agregar una nueva etiqueta"):
        nombre_etiqueta = st.text_input("Nombre de la etiqueta")
        descripcion_etiqueta = st.text_input("Descripción de la etiqueta")
        if st.button("Añadir Etiqueta"):
            # Verificar si la etiqueta ya existe (ignorando mayúsculas/minúsculas)
            if nombre_etiqueta.lower() in df_etiquetas["nombre"].str.lower().tolist():
                st.warning("⚠️ Esta etiqueta ya existe. Intenta con otro nombre.")
            elif nombre_etiqueta:  # Evitar añadir etiquetas vacías
                nueva_etiqueta = pd.DataFrame([{ "id": len(df_etiquetas) + 1, "nombre": nombre_etiqueta, "descripcion": descripcion_etiqueta }])
                df_etiquetas = pd.concat([df_etiquetas, nueva_etiqueta], ignore_index=True)
                save_data(df_sitios, df_etiquetas)
                st.success("✅ Etiqueta añadida correctamente!")
                time.sleep(2)
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
            puntuacion = st.slider("Puntuación", 1, 5, value=1, step=1)

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
                time.sleep(2)
                # Guardar coordenadas en `st.session_state`
                #st.session_state["mapa_centrado"] = {"lat": lat, "lon": lon}
                st.session_state["centro_mapa"] = [lat, lon]
                # 🔥 Borrar ubicaciones anteriores para evitar sobreescrituras
                st.session_state.pop("busqueda_ubicacion", None)
                st.session_state.pop("user_location", None)
                # Cambiar de página
                st.session_state["next_page"] = "📍 Mapa"
                st.rerun()  # Refrescar la app

    # Mostrar y editar etiquetas
    with st.expander("📋 Editar Etiquetas"):
        df_conteo = calcular_conteo_etiquetas(df_sitios)
        # Fusionar con df_etiquetas, manteniendo solo las etiquetas existentes
        df_etiquetas = df_etiquetas.drop(columns=["descripcion"], errors="ignore").merge(
            df_conteo, left_on="nombre", right_on="etiqueta", how="left"
        ).fillna(0)  # En caso de que alguna etiqueta no tenga conteo
        
        # Eliminar columna duplicada "etiqueta" si es lo mismo que "nombre"
        if "etiqueta" in df_etiquetas.columns and "nombre" in df_etiquetas.columns:
            df_etiquetas = df_etiquetas.drop(columns=["etiqueta"])
        # **Si hay múltiples columnas de "Número de sitios", quedarnos solo con una**
        columnas_duplicadas = [col for col in df_etiquetas.columns if "Número de sitios" in col]
        if len(columnas_duplicadas) > 1:
            df_etiquetas = df_etiquetas.drop(columns=columnas_duplicadas[:-1])  # Dejamos solo una columna
        id_data = df_etiquetas[["id"]].copy()
        # Ordenar antes de eliminar "id"
        df_etiquetas = df_etiquetas.sort_values(by="nombre", ascending=True)        
        df_etiquetas_editable = df_etiquetas.drop(columns=["id"], errors="ignore").reset_index(drop=True)
        edited_etiquetas = st.data_editor(df_etiquetas_editable, 
                            use_container_width=True, 
                            hide_index=True,
                            disabled={"Número de sitios":True}
        )
        if st.button("Guardar cambios en etiquetas"):
            edited_etiquetas = edited_etiquetas.merge(id_data, left_index=True, right_index=True, how="left")
            df_etiquetas = edited_etiquetas  # Asegurar que los cambios se reflejen en el dataframe principal
            save_data(df_sitios, df_etiquetas)
            st.success("✅ Etiquetas actualizadas correctamente!")
            time.sleep(2)
            st.rerun()


    # 📋 Editar sitios
    with st.expander("📋 Editar Sitios (excepto etiquetas)"):
        # Guardar la versión original de los enlaces en session_state si no existe
        if "original_links" not in st.session_state:
            st.session_state["original_links"] = df_sitios.set_index("nombre")["ubicación"].to_dict()
        # Guardamos una copia de las coordenadas antes de eliminarlas
        lat_lon_data = df_sitios[["nombre", "lat", "lon"]].copy()
        # Crear un DataFrame sin índice y sin las columnas lat/lon
        df_editable = df_sitios.drop(columns=["lat", "lon"], errors="ignore").reset_index(drop=True)
        # 🚀 Asegurar que "nombre" esté presente en `df_editable`
        if "nombre" not in df_editable.columns:
            st.error("Error: La columna 'nombre' no está en los datos. Verifica la carga de datos.")
            st.stop()
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
        if st.button("Guardar cambios"):
            # Ajustar puntuación a None si "Visitado" es False
            for i in range(len(edited_df)):
                if not edited_df.at[i, "visitado"]:  # Si "visitado" es False
                    edited_df.at[i, "puntuación"] = None  # Poner puntuación en None
            
            # Detectar si se ha cambiado algún enlace de Google Maps
            cambios_detectados = {}
            
            for i in range(len(edited_df)):
                sitio_nombre = edited_df.at[i, "nombre"]
                nuevo_link = edited_df.at[i, "ubicación"]
                # 🔥 Extraer el enlace anterior de la copia original con el nombre correcto
                antiguo_link = st.session_state["original_links"].get(sitio_nombre, None)

                if nuevo_link != antiguo_link:  # Detectar si el enlace cambió
                    cambios_detectados[sitio_nombre] = nuevo_link  # Guardamos por nombre (evita errores de índice)

            if cambios_detectados:  # Solo llamar a la función si hay cambios
                for sitio_nombre, nuevo_link in cambios_detectados.items():
                    coordenadas = obtener_coordenadas_desde_google_maps(nuevo_link)
                    if coordenadas:
                        lat, lon = coordenadas
                        st.success(f"🌍 Coordenadas actualizadas para {edited_df.at[i, 'nombre']}: Lat {lat}, Lon {lon}")
                        #lat_lon_data.at[i, "lat"] = lat
                        #lat_lon_data.at[i, "lon"] = lon
                        lat_lon_data.loc[lat_lon_data["nombre"] == sitio_nombre, ["lat", "lon"]] = [lat, lon]
                    else:
                        st.warning(f"⚠️ No se pudieron extraer coordenadas para {edited_df.at[i, 'nombre']}.")

            
            # Restaurar las coordenadas antes de guardar
            #edited_df = edited_df.merge(lat_lon_data, left_index=True, right_index=True, how="left")
            edited_df = edited_df.merge(lat_lon_data, on="nombre", how="left")  # 🔥 Usar "nombre" para alinear correctamente
            df_sitios = edited_df  # Asegurar que es el df principal actualizado
            # 🔥 Actualizar `original_links` con los nuevos enlaces
            st.session_state["original_links"] = df_sitios.set_index("nombre")["ubicación"].to_dict()
            save_data(df_sitios, df_etiquetas)
            st.success("✅ Datos guardados correctamente")
            time.sleep(2)
            st.rerun()

    # 📋 Editar etiquetas de un sitio específico
    with st.expander("📝 Editar Etiquetas de un Sitio"):
        # Selector de sitio
        sitio_nombres = df_sitios["nombre"].tolist()
        sitio_seleccionado = st.selectbox("Selecciona un sitio para editar sus etiquetas:", sitio_nombres)

        # Obtener las etiquetas actuales del sitio seleccionado
        sitio_index = df_sitios[df_sitios["nombre"] == sitio_seleccionado].index[0]  # Obtener el sitio como Series
        etiquetas_actuales = df_sitios.at[sitio_index, "etiquetas"] if isinstance(df_sitios.at[sitio_index, "etiquetas"], list) else []

        # Obtener todas las etiquetas disponibles
        etiquetas_disponibles = df_etiquetas["nombre"].tolist()

        # Multiselect para editar etiquetas del sitio seleccionado
        etiquetas_editadas = st.multiselect(
            "Selecciona las etiquetas para este sitio:",
            options=etiquetas_disponibles,
            default=etiquetas_actuales
        )

        if st.button("Guardar etiquetas del sitio"):
            # Actualizar el DataFrame con las nuevas etiquetas
            df_sitios.at[sitio_index, "etiquetas"] = etiquetas_editadas
            save_data(df_sitios, df_etiquetas)  # Guardar cambios
            st.success(f"✅ Etiquetas actualizadas para {sitio_seleccionado}")
            time.sleep(2)
            st.rerun()

    # 🗑️ Eliminar un sitio
    with st.expander("🗑️ Eliminar un sitio"):
        if not df_sitios.empty:
            sitio_a_eliminar = st.selectbox("Selecciona un sitio para eliminar", df_sitios["nombre"].tolist())

            if st.button("Eliminar sitio"):
                df_sitios = df_sitios[df_sitios["nombre"] != sitio_a_eliminar]
                save_data(df_sitios,df_etiquetas)
                st.success(f"✅ Sitio '{sitio_a_eliminar}' eliminado")
                time.sleep(2)
                st.rerun()
        else:
            st.info("No hay sitios para eliminar.")

    # 🔒 Cerrar sesión
    if st.button("Cerrar sesión"):
        st.session_state.authenticated = False
        st.rerun()

