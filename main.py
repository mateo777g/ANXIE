import flet as ft
from controllers.main_controller import MainController

def main(page: ft.Page):
    MainController(page)

if __name__ == "__main__":
    # Cambiado a "." para que Flet tenga acceso a todas las carpetas de la raíz
    ft.app(target=main, assets_dir=".")