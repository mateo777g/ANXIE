"""
models/entorno.py
Lee las llaves del panel desde su .env (Supabase y, más adelante, R2).

El .env vive en la carpeta del panel, junto a main.py; con el .exe, al lado del .exe. Nunca
va a git (está en el .gitignore: el repo del panel es público). Se busca por la carpeta del
panel y no por la de la terminal, así que da igual desde dónde se lance.

Si falta, el panel abre igual (los generadores no necesitan internet): solo la vista Cuentas
avisa de que no puede conectarse (ver supabase_client.FaltaConfiguracion).
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Empaquetado con flet pack (PyInstaller), __file__ vive en una carpeta temporal que se borra
# al cerrar: la carpeta de verdad es la del .exe.
EMPAQUETADO = getattr(sys, "frozen", False)
if EMPAQUETADO:
    CARPETA_PANEL = Path(sys.executable).resolve().parent
else:
    CARPETA_PANEL = Path(__file__).resolve().parent.parent

RUTA_ENV = CARPETA_PANEL / ".env"
load_dotenv(RUTA_ENV)


def recurso(ruta):
    # Dónde está de verdad un archivo de assets/ ("assets/fondo.png"). El .exe es de un solo
    # archivo (el dueño, 26/09): los assets viajan DENTRO y PyInstaller los saca en cada arranque
    # a una carpeta temporal (sys._MEIPASS), mientras que biblioteca/, config.json y el .env viven
    # al lado del .exe (main.py se para ahí). Así que en el .exe, ruta absoluta a esa carpeta
    # temporal (Flet acepta rutas absolutas en src y en page.fonts); con Python, la misma ruta
    # relativa de siempre, sin cambiar nada.
    if EMPAQUETADO:
        return os.path.join(sys._MEIPASS, ruta)
    return ruta


def leer(clave):
    # El valor de una llave del .env, sin espacios; "" si no está.
    return (os.getenv(clave) or "").strip()
