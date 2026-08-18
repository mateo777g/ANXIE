import flet as ft
import os
import shutil
import json

class BibliotecaView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.padding = 0
        
        self.tipo_actual = "cuentas" # Por defecto arranca mostrando cuentas

        # --- PESTAÑAS (TABS) ---
        self.btn_tab_cuentas = ft.ElevatedButton("Cuentas", bgcolor="#B23A3A", color=ft.Colors.WHITE, on_click=lambda _: self.cambiar_tab("cuentas"))
        self.btn_tab_recibos = ft.ElevatedButton("Recibos", bgcolor="#333333", color=ft.Colors.WHITE54, on_click=lambda _: self.cambiar_tab("recibos"))

        self.grid_imagenes = ft.GridView(expand=True, runs_count=5, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20)
        self.area_galeria = ft.Container(expand=True, content=self.grid_imagenes)

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
                self._crear_boton_menu("Mi biblioteca", ft.Icons.INBOX, "biblioteca", activo=True), 
                self._crear_boton_menu("Ajustes", ft.Icons.SETTINGS, "ajustes"),
            ], spacing=10)
        )

        main_content = ft.Container(
            expand=True, padding=40,
            content=ft.Column([
                ft.Text("Mi Biblioteca", size=40, weight="w500", color=ft.Colors.WHITE),
                ft.Row([self.btn_tab_cuentas, self.btn_tab_recibos], spacing=10),
                ft.Divider(height=20, color=ft.Colors.WHITE12),
                self.area_galeria
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)

    def cambiar_tab(self, tipo):
        self.tipo_actual = tipo
        # Cambiamos colores para saber cuál está activo
        self.btn_tab_cuentas.bgcolor = "#B23A3A" if tipo == "cuentas" else "#333333"
        self.btn_tab_cuentas.color = ft.Colors.WHITE if tipo == "cuentas" else ft.Colors.WHITE54
        
        self.btn_tab_recibos.bgcolor = "#B23A3A" if tipo == "recibos" else "#333333"
        self.btn_tab_recibos.color = ft.Colors.WHITE if tipo == "recibos" else ft.Colors.WHITE54
        
        self.btn_tab_cuentas.update()
        self.btn_tab_recibos.update()
        self.cargar_biblioteca()

    def did_mount(self):
        self.page_ref = self.router.page
        self.cargar_biblioteca()

    def cargar_biblioteca(self):
        self.grid_imagenes.controls.clear()
        carpeta = os.path.join("biblioteca", self.tipo_actual)
        
        if os.path.exists(carpeta):
            archivos = [f for f in os.listdir(carpeta) if f.endswith(('.png', '.jpg', '.jpeg'))]
            for archivo in archivos:
                ruta_abs = os.path.abspath(os.path.join(carpeta, archivo))
                self.grid_imagenes.controls.append(self._crear_tarjeta_imagen(ruta_abs, archivo))
        
        self.area_galeria.update()

    def _crear_tarjeta_imagen(self, ruta_absoluta, nombre_archivo):
        return ft.Container(
            bgcolor="#151515", border_radius=10, padding=10, 
            border=ft.Border(top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12), left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)),
            content=ft.Column([
                ft.Container(expand=True, width=9999, content=ft.Column([ft.Image(src=f"biblioteca/{self.tipo_actual}/{nombre_archivo}", expand=True)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
                ft.Divider(height=10, color=ft.Colors.WHITE12),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.DOWNLOAD_ROUNDED, icon_color=ft.Colors.WHITE70, icon_size=22, on_click=lambda e, n=nombre_archivo, r=ruta_absoluta: self.descargar_imagen(n, r)),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#B23A3A", icon_size=22, on_click=lambda e, r=ruta_absoluta: self.borrar_imagen(r))
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ])
        )

    def borrar_imagen(self, ruta):
        if os.path.exists(ruta):
            os.remove(ruta)
            self.mostrar_snack("Eliminada.")
            self.cargar_biblioteca() 

    def descargar_imagen(self, nombre_archivo, ruta_origen):
        try:
            es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None
            if es_en_la_nube:
                self.page_ref.launch_url(f"/biblioteca/{self.tipo_actual}/{nombre_archivo}")
            else:
                clave_json = f"ruta_descargas_{self.tipo_actual}"
                ruta_guardada = None
                if os.path.exists("config.json"):
                    try:
                        with open("config.json", "r") as f:
                            ruta_guardada = json.load(f).get(clave_json)
                    except: pass
                carpeta_destino = ruta_guardada if ruta_guardada and os.path.exists(ruta_guardada) else os.path.join(os.path.expanduser("~"), "Downloads")
                shutil.copy(ruta_origen, os.path.join(carpeta_destino, f"copia_{nombre_archivo}"))
                self.mostrar_snack(f"¡Exportada con éxito!")
        except Exception as e:
            self.mostrar_snack(f"Error: {e}")

    def mostrar_snack(self, mensaje):
        self.page_ref.overlay.append(ft.SnackBar(ft.Text(mensaje), open=True))
        self.page_ref.update()

    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        return ft.Container(
            content=ft.Row([ft.Icon(icono, color=ft.Colors.WHITE, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14)]),
            bgcolor="#B23A3A" if activo else ft.Colors.TRANSPARENT, padding=12, border_radius=8,
            on_click=lambda _: self.router.cambiar_vista(ruta) if not activo else None
        )