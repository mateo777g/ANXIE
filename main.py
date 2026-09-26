import os
import flet as ft
from models.entorno import EMPAQUETADO, CARPETA_PANEL
from controllers.main_controller import MainController

def main(page: ft.Page):
    MainController(page)

if __name__ == "__main__":
    # En el .exe, el panel se para en la carpeta del .exe: ahí viven biblioteca/, config.json y el
    # .env aunque lo abran desde un acceso directo con otra carpeta de inicio (los assets van
    # dentro del .exe, ver entorno.recurso). Con Python se sigue lanzando desde panel/.
    if EMPAQUETADO:
        os.chdir(CARPETA_PANEL)
    # Cambiado a "." para que Flet tenga acceso a todas las carpetas de la raíz
    ft.app(target=main, assets_dir=".")
