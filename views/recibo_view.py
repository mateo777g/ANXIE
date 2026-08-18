import os
import datetime  # <-- Agregamos esta importación
import flet as ft
from controllers.app_controller import AppController

class ReciboView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page 
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.padding = 0

        self.controller = AppController(self, tipo="recibos")

        # --- LÓGICA DE FECHA ---
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        hoy = datetime.datetime.now()
        fecha_texto = f"{dias[hoy.weekday()]}, {hoy.day} DE {meses[hoy.month - 1]}"

        # --- COMPONENTES VISUALES ---
        self.input_skin = ft.TextField(
            hint_text="Selecciona el archivo de Skins...", 
            expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, content_padding=10, text_size=12, read_only=True
        )
        
        self.txt_correo1 = ft.TextField(
            label="Correo", value="", 
            expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12
        )
        self.txt_correo2 = ft.TextField(
            label="Contraseña", value="", 
            expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12
        )
        
        # === NUEVO SELECTOR NFA / FA ===
        self.radio_tipo_cuenta = ft.RadioGroup(
            value="NFA",
            content=ft.Row([
                ft.Radio(value="NFA", label="NFA", fill_color=ft.Colors.RED_300),
                ft.Radio(value="FA", label="FA", fill_color=ft.Colors.RED_300)
            ])
        )

        # Ahora el usuario solo lleva el nombre
        self.txt_usuario = ft.TextField(
            label="Usuario", value="", 
            expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12
        )
        
        self.txt_fecha = ft.TextField(
            label="Fecha", value="", hint_text="(Deja vacío para automático)",
            expand=True, bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12
        )

        self.input_nombre = ft.TextField(
            label="Nombre de la descarga", 
            value="recibo", 
            bgcolor="#0e0e0e", border_color=ft.Colors.WHITE24, color=ft.Colors.WHITE, text_size=12
        )

        # --- VISTA PREVIA ---
        self.texto_espera = ft.Text("Esperando Generación...", color=ft.Colors.WHITE54, size=14)
        self.preview_image = ft.Image(src="", expand=True, visible=False)

        self.image_container = ft.Container(
            expand=True, width=9999, bgcolor="#0e0e0e", border_radius=10,
            border=ft.Border(top=ft.BorderSide(2, "#B23A3A"), bottom=ft.BorderSide(2, ft.Colors.WHITE12), left=ft.BorderSide(2, ft.Colors.WHITE12), right=ft.BorderSide(2, ft.Colors.WHITE12)),
            content=ft.Column([self.texto_espera, self.preview_image], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- BOTONES ---
        self.btn_generar = ft.ElevatedButton("Generar Recibo", icon=ft.Icons.RECEIPT_LONG, bgcolor="#B23A3A", color=ft.Colors.WHITE, expand=True, height=45, on_click=self.controller.procesar_clicks)
        self.btn_descargar = ft.ElevatedButton("Descargar", icon=ft.Icons.DOWNLOAD, bgcolor="#333333", color=ft.Colors.WHITE, expand=True, height=45, disabled=True, on_click=self.controller.descargar_imagen)

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
                    ft.Column([
                        ft.Text("Configuración del Recibo", color=ft.Colors.WHITE54, weight="bold"),
                        self._crear_bloque_input("Imagen Skins", self.input_skin),
                        ft.Container(
                            bgcolor="#1a1a1a", padding=15, border_radius=10, border=ft.Border.all(1, ft.Colors.WHITE12),
                            content=ft.Column([
                                ft.Text("Textos Superiores", color=ft.Colors.WHITE, weight="bold"),
                                self.txt_correo1, self.txt_correo2
                            ])
                        ),
                        ft.Container(
                            bgcolor="#1a1a1a", padding=15, border_radius=10, border=ft.Border.all(1, ft.Colors.WHITE12),
                            content=ft.Column([
                                ft.Text("Textos Inferiores", color=ft.Colors.WHITE, weight="bold"),
                                self.radio_tipo_cuenta, 
                                self.txt_usuario, 
                                self.txt_fecha
                            ])
                        )
                    ], spacing=15, expand=True),
                    ft.Container(width=25)
                ])
            ], scroll=ft.ScrollMode.ADAPTIVE)
        )

        # --- PANEL DERECHO Y ARMADO FINAL ---
        right_panel = ft.Container(
            expand=1, bgcolor="#1a1a1a", border_radius=15, padding=25, border=ft.Border.all(1, ft.Colors.WHITE12),
            content=ft.Column([
                ft.Text("Vista Previa del Recibo", color=ft.Colors.WHITE, size=20, weight="bold"),
                self.image_container, ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.input_nombre, ft.Divider(height=15, color=ft.Colors.WHITE12),
                ft.Row([self.btn_generar, self.btn_descargar], spacing=15)
            ], spacing=15, expand=True) 
        )

        main_content = ft.Container(
            expand=True, padding=40,
            content=ft.Column([
                # 🔥 ACÁ HICIMOS EL CAMBIO PARA MOSTRAR LA FECHA DINÁMICA 🔥
                ft.Text(fecha_texto, color=ft.Colors.RED_300, size=14, weight="w500"),
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ft.Colors.WHITE54, on_click=lambda _: self.router.cambiar_vista("contenido")),
                    ft.Text("Generar Recibo de Venta", size=35, weight="w500", color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=20),
                ft.Row([left_panel, right_panel], expand=True, spacing=40, vertical_alignment=ft.CrossAxisAlignment.START)
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)

    # ================= FUNCIONES SECUNDARIAS =================
    
    def abrir_explorador_nativo(self, text_field):
        es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None
        if es_en_la_nube:
            text_field.read_only = False
            text_field.hint_text = "Escribe el nombre o ruta del archivo..."
            text_field.update()
            self.mostrar_snack("Modo web: Escribe directamente el nombre del archivo en el campo, bro.")
            return

        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            archivo = filedialog.askopenfilename(
                title="Selecciona una imagen",
                filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")]
            )
            root.destroy()
            
            if archivo:
                archivo_limpio = os.path.normpath(archivo)
                text_field.value = archivo_limpio
                text_field.update()
        except Exception as ex:
            self.mostrar_snack(f"Error al abrir explorador local: {ex}")

    def actualizar_preview(self, ruta_absoluta):
        self.texto_espera.visible = False
        self.preview_image.src = ruta_absoluta
        self.preview_image.visible = True
        self.btn_descargar.disabled = False
        self.image_container.update()
        self.btn_descargar.update()

    def mostrar_snack(self, mensaje):
        self.page_ref.overlay.append(ft.SnackBar(ft.Text(mensaje), open=True))
        self.page_ref.update()

    def _crear_bloque_input(self, titulo, path_field):
        return ft.Container(
            bgcolor="#1a1a1a", padding=15, border_radius=10, border=ft.Border.all(1, ft.Colors.WHITE12),
            content=ft.Column([
                ft.Text(titulo, color=ft.Colors.WHITE, weight="bold"),
                ft.Row([
                    path_field,
                    ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_color="#B23A3A", on_click=lambda _: self.abrir_explorador_nativo(path_field))
                ])
            ])
        )

    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        return ft.Container(
            content=ft.Row([ft.Icon(icono, color=ft.Colors.WHITE, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14)]),
            bgcolor="#B23A3A" if activo else ft.Colors.TRANSPARENT, padding=12, border_radius=10, ink=True,
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )