"""
models/perfil.py
El perfil de quien usa el panel: su nombre completo y cómo quiere que Fragmentless lo llame
(la ventana "Perfil", al pulsar el pie de la barra lateral). Lo segundo sale en el pie de la barra
("Miguel · Básico", con su inicial en el círculo) y en el saludo de Inicio.

Se guarda en config.json, junto a las carpetas de Ajustes (el dueño, 26/09: "algo parecido a
config.json"), con las claves "nombre_completo" y "como_llamarte". config.json está en el
.gitignore del panel: el nombre completo nunca llega al repo, que es público.
Quien escribe en config.json lee lo que ya hay y cambia solo lo suyo (aquí y en Ajustes): si no,
guardar una carpeta borraría el nombre, y al revés.
"""
import json
import os

ARCHIVO_CONFIG = "config.json"

# Mientras no se haya elegido otro: el de siempre.
POR_DEFECTO = "Miguel"


def leer_config():
    # Todo config.json como diccionario ({} si no existe o no se puede leer).
    try:
        with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def guardar_config(cambios):
    # Cambia solo las claves de `cambios` y deja las demás como estaban. Escribe en un archivo
    # temporal y lo cambia por el bueno: si algo falla a medias, config.json no queda cortado.
    datos = leer_config()
    datos.update(cambios)
    temporal = ARCHIVO_CONFIG + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    os.replace(temporal, ARCHIVO_CONFIG)


def nombre_completo():
    return (leer_config().get("nombre_completo") or "").strip()


def como_llamarte():
    # Cómo lo llama el panel: lo que eligió; si no eligió nada, POR_DEFECTO.
    return (leer_config().get("como_llamarte") or "").strip() or POR_DEFECTO


def guardar(nombre, llamarte):
    guardar_config({"nombre_completo": nombre.strip(), "como_llamarte": llamarte.strip()})
