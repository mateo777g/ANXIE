import flet as ft
import datetime
import os
import json

ARCHIVO_CONFIG = "config.json"

class AjustesView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.padding = 0
        
        self.es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None

        # --- RUTAS ---
        self.ruta_default = os.path.join(os.path.expanduser("~"), "Downloads")
        rutas_guardadas = self.leer_configuracion()
        
        if self.es_en_la_nube:
            ruta_c = "Descargas automáticas del navegador"
            ruta_r = "Descargas automáticas del navegador"
        else:
            ruta_c = rutas_guardadas.get("cuentas", self.ruta_default)
            ruta_r = rutas_guardadas.get("recibos", self.ruta_default)
        
        self.input_ruta_cuentas = self._crear_input_ruta(ruta_c)
        self.input_ruta_recibos = self._crear_input_ruta(ruta_r)

        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        hoy = datetime.datetime.now()
        fecha_texto = f"{dias[hoy.weekday()]}, {hoy.day} DE {meses[hoy.month - 1]}"

        # --- SIDEBAR ---
        sidebar = ft.Container(
            width=250, bgcolor="#1a1a1a", padding=20,
            content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(radius=25, background_image_src="assets/logo.jpg", bgcolor=ft.Colors.WHITE),
                    ft.Column([ft.Text("ANXIE STORE", weight="bold", italic=True, size=18), ft.Text("PANEL", color=ft.Colors.RED_700, size=10, weight="bold")], spacing=0)
                ]),
                ft.Divider(height=40, color=ft.Colors.WHITE24),
                self._crear_boton_menu("Inicio", ft.Icons.HOME, "home"),
                self._crear_boton_menu("Crear contenido", ft.Icons.AUTO_AWESOME_OUTLINED, "contenido"),
                self._crear_boton_menu("Mi biblioteca", ft.Icons.INBOX, "biblioteca"),
                self._crear_boton_menu("Ajustes", ft.Icons.SETTINGS, "ajustes", activo=True),
            ], spacing=10)
        )

        self.btn_guardar = ft.ElevatedButton(
            "Guardar Ajustes", icon=ft.Icons.SAVE, bgcolor="#B23A3A" if not self.es_en_la_nube else "#333333",
            color=ft.Colors.WHITE, disabled=self.es_en_la_nube, on_click=self.guardar_configuracion
        )

        # --- PANEL DE AJUSTES DUAL ---
        panel_ajustes = ft.Container(
            bgcolor="#1a1a1a", padding=30, border_radius=15, expand=True,
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12), left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)),
            content=ft.Column([
                ft.Text("Configuración de Descargas Locales", size=20, weight="bold", color=ft.Colors.WHITE),
                ft.Divider(height=30, color=ft.Colors.WHITE12),
                
                ft.Text("Ruta para exportar imagenes de Cuentas:", color=ft.Colors.WHITE, size=14, weight="w500"),
                ft.Row([self.input_ruta_cuentas, ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_color="#B23A3A", disabled=self.es_en_la_nube, on_click=lambda e: self.seleccionar_carpeta_tk("cuentas"))]),
                
                ft.Container(height=15),
                
                ft.Text("Ruta para exportar imagenes de Recibos:", color=ft.Colors.WHITE, size=14, weight="w500"),
                ft.Row([self.input_ruta_recibos, ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_color="#B23A3A", disabled=self.es_en_la_nube, on_click=lambda e: self.seleccionar_carpeta_tk("recibos"))]),
                
                ft.Container(height=20),
                ft.Row([self.btn_guardar], alignment=ft.MainAxisAlignment.END)
            ], spacing=10)
        )

        main_content = ft.Container(
            expand=True, padding=40,
            content=ft.Column([
                ft.Text(fecha_texto, color=ft.Colors.RED_300, size=14, weight="w500"),
                ft.Text("Ajustes", size=40, weight="w500", color=ft.Colors.WHITE),
                ft.Container(height=30),
                ft.Row([panel_ajustes], expand=True)
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)

    def _crear_input_ruta(self, valor):
        return ft.TextField(value=valor, expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12, read_only=True)

    def leer_configuracion(self):
        if os.path.exists(ARCHIVO_CONFIG):
            try:
                with open(ARCHIVO_CONFIG, "r") as f:
                    datos = json.load(f)
                    return {
                        "cuentas": datos.get("ruta_descargas_cuentas", self.ruta_default),
                        "recibos": datos.get("ruta_descargas_recibos", self.ruta_default)
                    }
            except: pass
        return {"cuentas": self.ruta_default, "recibos": self.ruta_default}

    def guardar_configuracion(self, e):
        if self.es_en_la_nube: return
        try:
            with open(ARCHIVO_CONFIG, "w") as f:
                json.dump({
                    "ruta_descargas_cuentas": self.input_ruta_cuentas.value,
                    "ruta_descargas_recibos": self.input_ruta_recibos.value
                }, f)
            self.mostrar_snack("¡Ambas rutas guardadas correctamente!")
        except Exception as ex:
            self.mostrar_snack(f"Error: {ex}")

    def seleccionar_carpeta_tk(self, tipo):
        if self.es_en_la_nube: return
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            carpeta = filedialog.askdirectory(title=f"Carpeta para {tipo}")
            root.destroy()
            if carpeta:
                if tipo == "cuentas":
                    self.input_ruta_cuentas.value = os.path.normpath(carpeta)
                    self.input_ruta_cuentas.update()
                else:
                    self.input_ruta_recibos.value = os.path.normpath(carpeta)
                    self.input_ruta_recibos.update()
        except Exception as ex:
            self.mostrar_snack(f"Error al abrir explorador: {ex}")

    def mostrar_snack(self, mensaje):
        self.page_ref.overlay.append(ft.SnackBar(ft.Text(mensaje), open=True))
        self.page_ref.update()

    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        return ft.Container(
            content=ft.Row([ft.Icon(icono, color=ft.Colors.WHITE, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14)]),
            bgcolor="#B23A3A" if activo else ft.Colors.TRANSPARENT, padding=12, border_radius=10, ink=True,
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )