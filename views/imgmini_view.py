import os
import flet as ft
import datetime
from controllers.app_controller import AppController

class CuentaPequenaView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page 
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.padding = 0

        self.controller = AppController(self, tipo="cuentas_mini")  # <-- Indicamos que es una cuenta mini

        # --- LÓGICA DE FECHA ---
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        hoy = datetime.datetime.now()
        fecha_texto = f"{dias[hoy.weekday()]}, {hoy.day} DE {meses[hoy.month - 1]}"

        # --- COMPONENTES VISUALES ---
        self.input_picos = ft.TextField(hint_text="Selecciona el archivo de Picos...", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, content_padding=10, text_size=12, read_only=True)
        self.input_skins = ft.TextField(hint_text="Selecciona el archivo de Skins...", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, content_padding=10, text_size=12, read_only=True)
        self.input_emotes = ft.TextField(hint_text="Selecciona el archivo de Emotes...", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, content_padding=10, text_size=12, read_only=True)
        
        self.txt_picos = ft.TextField(label="Texto Picos", value="¡PICOS!", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12)
        self.txt_skins = ft.TextField(label="Texto Skins", value="", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12)
        self.txt_emotes = ft.TextField(label="Texto Emotes", value="", expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12)

        self.input_nombre = ft.TextField(
            label="Nombre de la descarga", 
            value="cuenta", 
            bgcolor="#0e0e0e", 
            border_color=ft.Colors.WHITE24, 
            color=ft.Colors.WHITE, 
            text_size=12
        )

        # --- CONTENEDOR DE VISTA PREVIA ---
        self.texto_espera = ft.Text("Esperando Generación...", color=ft.Colors.WHITE54, size=14)
        self.preview_image = ft.Image(src="", expand=True, visible=False)

        self.image_container = ft.Container(
            expand=True,  # Magia vertical: ocupa todo el hueco hacia abajo
            width=9999,   # Magia horizontal: fuerza a Flet a ocupar todo el ancho disponible
            bgcolor="#0e0e0e",
            border_radius=10,
            border=ft.Border(
                top=ft.BorderSide(2, "#B23A3A"), bottom=ft.BorderSide(2, ft.Colors.WHITE12),
                left=ft.BorderSide(2, ft.Colors.WHITE12), right=ft.BorderSide(2, ft.Colors.WHITE12)
            ),
            content=ft.Column(
                [self.texto_espera, self.preview_image], 
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        # --- BOTONES ---
        self.btn_generar = ft.ElevatedButton(
            "Generar Imagen", 
            icon=ft.Icons.IMAGE, 
            bgcolor="#B23A3A", 
            color=ft.Colors.WHITE,
            expand=True,
            height=45,
            on_click=self.controller.procesar_clicks
        )

        self.btn_descargar = ft.ElevatedButton(
            "Descargar", 
            icon=ft.Icons.DOWNLOAD, 
            bgcolor="#333333", 
            color=ft.Colors.WHITE,
            expand=True,
            height=45,
            disabled=True, 
            on_click=self.controller.descargar_imagen
        )

        # --- SIDEBAR ---
        sidebar = ft.Container(
            width=250,
            bgcolor="#1a1a1a",
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(radius=25, background_image_src="assets/logo.jpg", bgcolor=ft.Colors.WHITE),
                    ft.Column([
                        ft.Text("ANXIE STORE", weight="bold", italic=True, size=18),
                        ft.Text("PANEL", color=ft.Colors.RED_700, size=10, weight="bold")
                    ], spacing=0)
                ]),
                ft.Divider(height=40, color=ft.Colors.WHITE24),
                self._crear_boton_menu("Inicio", ft.Icons.HOME, "home"),
                self._crear_boton_menu("Crear contenido", ft.Icons.AUTO_AWESOME_OUTLINED, "contenido", activo=True),
                self._crear_boton_menu("Mi biblioteca", ft.Icons.INBOX, "biblioteca"),
                self._crear_boton_menu("Ajustes", ft.Icons.SETTINGS, "ajustes"),
            ], spacing=10)
        )

        # --- PANEL IZQUIERDO ---
        left_panel = ft.Container(
            expand=1,
            content=ft.Column([
                ft.Row([
                    # 1. Tu columna de siempre, pero le ponemos expand=True para que ocupe lo que pueda
                    ft.Column([
                        ft.Text("Configuración de la imagen", color=ft.Colors.WHITE54, weight="bold"),
                        self._crear_bloque_input("Sección Picos", self.input_picos, self.txt_picos),
                        self._crear_bloque_input("Sección Skins", self.input_skins, self.txt_skins),
                        self._crear_bloque_input("Sección Emotes", self.input_emotes, self.txt_emotes),
                    ], spacing=15, expand=True),
                    
                    # 2. EL MURO INVISIBLE: Esto arrima la barra de scroll hacia la derecha
                    ft.Container(width=25)
                ])
            ], scroll=ft.ScrollMode.ADAPTIVE)
        )

        # --- PANEL DERECHO ---
        right_panel = ft.Container(
            expand=1,
            bgcolor="#1a1a1a",
            border_radius=15,
            padding=25,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12),
                left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)
            ),
            content=ft.Column([
                ft.Text("Vista Previa", color=ft.Colors.WHITE, size=20, weight="bold"),
                self.image_container, # Ahora sí, se va a estirar a lo bestia
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.input_nombre, 
                ft.Divider(height=15, color=ft.Colors.WHITE12),
                ft.Row([self.btn_generar, self.btn_descargar], spacing=15)
            ], spacing=15, expand=True) # <- Importante que este expand siga aquí
        )

        # --- ARMADO FINAL ---
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                ft.Text(fecha_texto, color=ft.Colors.RED_300, size=14, weight="w500"),
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ft.Colors.WHITE54, on_click=lambda _: self.router.cambiar_vista("contenido")),
                    ft.Text("Generar Imagen Pequeña", size=35, weight="w500", color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=20),
                ft.Row([left_panel, right_panel], expand=True, spacing=40, vertical_alignment=ft.CrossAxisAlignment.START)
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)


    # ==========================================
    # LÓGICA DE EXPLORADOR RESILIENTE (HÍBRIDO PC/RENDER)
    # ==========================================
    def abrir_explorador_nativo(self, text_field):
        # Detectamos si estamos en la nube (Render)
        es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None

        if es_en_la_nube:
            # En la nube no podemos abrir ventanas de Windows. 
            # Cambiamos temporalmente el input a modo edición para que puedas escribir o pegar la ruta/nombre.
            text_field.read_only = False
            text_field.hint_text = "Escribe el nombre o ruta del archivo..."
            text_field.update()
            self.mostrar_snack("Modo web: Escribe directamente el nombre del archivo en el campo, bro.")
            return

        # === SI ESTÁS EN TU PC (LOCAL): Abre tu explorador normal intacto ===
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Filtro para que solo busque imágenes fijas (.png, .jpg)
            archivo = filedialog.askopenfilename(
                title="Selecciona una imagen",
                filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")]
            )
            root.destroy()
            
            if archivo:
                # Limpiamos las barras diagonales estilo Windows
                archivo_limpio = os.path.normpath(archivo)
                text_field.value = archivo_limpio
                text_field.update()
        except Exception as ex:
            self.mostrar_snack(f"Error al abrir explorador local: {ex}")


    def actualizar_preview(self, ruta_absoluta):
        # 1. Apagamos el texto
        self.texto_espera.visible = False
        
        # 2. Le pasamos la ruta directa (al ser una ruta que Flet no conoce, se ve forzado a cargarla)
        self.preview_image.src = ruta_absoluta
        self.preview_image.visible = True
        
        # 3. Desbloqueamos el botón
        self.btn_descargar.disabled = False
        
        # 4. Actualizamos
        self.image_container.update()
        self.btn_descargar.update()


    def mostrar_snack(self, mensaje):
        self.page_ref.overlay.append(ft.SnackBar(ft.Text(mensaje), open=True))
        self.page_ref.update()


    # ==========================================
    # HELPERS
    # ==========================================
    def _crear_bloque_input(self, titulo, path_field, text_field):
        return ft.Container(
            bgcolor="#1a1a1a", padding=15, border_radius=10,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12),
                left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)
            ),
            content=ft.Column([
                ft.Text(titulo, color=ft.Colors.WHITE, weight="bold"),
                ft.Row([
                    path_field,
                    ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_color="#B23A3A", on_click=lambda _: self.abrir_explorador_nativo(path_field))
                ]),
                ft.Row([ft.Icon(ft.Icons.TEXT_FIELDS, color=ft.Colors.WHITE54, size=20), text_field])
            ])
        )


    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        return ft.Container(
            content=ft.Row([ft.Icon(icono, color=ft.Colors.WHITE, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14)]),
            bgcolor="#B23A3A" if activo else ft.Colors.TRANSPARENT, padding=12, border_radius=10, ink=True,
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )