import flet as ft
import datetime
import os

class HomeView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.padding = 0
        
        # --- LÓGICA PARA LA FECHA DINÁMICA ---
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        hoy = datetime.datetime.now()
        fecha_texto = f"{dias[hoy.weekday()]}, {hoy.day} DE {meses[hoy.month - 1]}"

        # --- TEXTOS DE LOS CONTADORES ---
        self.texto_cuentas = ft.Text("0 cuentas creadas", color=ft.Colors.WHITE, size=14, weight="w500")
        self.texto_recibos = ft.Text("0 recibos creados", color=ft.Colors.WHITE, size=14, weight="w500")

        # --- BARRA LATERAL (SIDEBAR) ---
        sidebar = ft.Container(
            width=250,
            bgcolor="#1a1a1a",
            padding=20,
            content=ft.Column([
                # Logo y Título
                ft.Row([
                    ft.CircleAvatar(radius=25, background_image_src="assets/logo.jpg", bgcolor=ft.Colors.WHITE),
                    ft.Column([
                        ft.Text("ANXIE STORE", weight="bold", italic=True, size=18),
                        ft.Text("PANEL", color=ft.Colors.RED_700, size=10, weight="bold")
                    ], spacing=0)
                ]),
                ft.Divider(height=40, color=ft.Colors.WHITE24),
                
                # Menú de navegación
                self._crear_boton_menu("Inicio", ft.Icons.HOME, "home", activo=True),
                self._crear_boton_menu("Crear contenido", ft.Icons.AUTO_AWESOME_OUTLINED, "contenido"),
                self._crear_boton_menu("Mi biblioteca", ft.Icons.INBOX, "biblioteca"),
                self._crear_boton_menu("Ajustes", ft.Icons.SETTINGS, "ajustes"),
            ], spacing=10)
        )

        # --- CONTENIDO PRINCIPAL ---
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                # Fecha
                ft.Text(fecha_texto, color=ft.Colors.RED_300, size=14, weight="w500"),
                
                # Saludo
                ft.Row([
                    ft.Text("Buenos días,", size=40, weight="w500"),
                    ft.Text("Miguel", size=40, color=ft.Colors.RED_700, weight="w500")
                ], spacing=10),
                
                ft.Container(height=25), # Más separación del saludo para que respire
                
                # --- FILA DE TARJETAS ---
                ft.Row([
                    # Bloque 1: ¿Qué hacemos hoy?
                    ft.Container(
                        expand=1,
                        bgcolor="#1a1a1a",
                        border_radius=15,
                        padding=25,
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12),
                            left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)
                        ),
                        content=ft.Column([
                            ft.Text("¿Qué hacemos hoy?", size=22, weight="bold", italic=True),
                            ft.Text("Atajos a las tareas que mas usas.", color=ft.Colors.RED_400, size=12),
                            ft.Container(height=15), 
                            
                            # PRIMERA FILA DE BOTONES (Los Originales)
                            ft.Row([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.IMAGE, color=ft.Colors.PURPLE_300, size=20),
                                        ft.Text("Imagen Cuentas", color=ft.Colors.WHITE, weight="w600", size=13)
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                    bgcolor="#333333", height=48, border_radius=10, expand=True, ink=True,
                                    on_click=lambda _: self.router.cambiar_vista("generador_miniaturas")
                                ),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.BLUE_300, size=20),
                                        ft.Text("Imagen Recibos", color=ft.Colors.WHITE, weight="w600", size=13)
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                    bgcolor="#333333", height=48, border_radius=10, expand=True, ink=True,
                                    on_click=lambda _: self.router.cambiar_vista("recibo") 
                                )
                            ], spacing=12),

                            # 🔥 SEGUNDA FILA DE BOTONES (Los Nuevos Pequeños) 🔥
                            ft.Row([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.IMAGE_ASPECT_RATIO, color=ft.Colors.PURPLE_200, size=20),
                                        ft.Text("Cuenta Pequeña", color=ft.Colors.WHITE, weight="w600", size=13)
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                    bgcolor="#333333", height=48, border_radius=10, expand=True, ink=True,
                                    on_click=lambda _: self.router.cambiar_vista("cuenta_pequena")
                                ),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.RECEIPT, color=ft.Colors.BLUE_200, size=20),
                                        ft.Text("Recibo Pequeño", color=ft.Colors.WHITE, weight="w600", size=13)
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                                    bgcolor="#333333", height=48, border_radius=10, expand=True, ink=True,
                                    on_click=lambda _: self.router.cambiar_vista("recibo_pequeno")
                                )
                            ], spacing=12)

                        ], alignment=ft.MainAxisAlignment.CENTER) 
                    ),
                    
                    # Bloque 2: Contenido Generado (Vuelve a ser UN SOLO BLOQUE)
                    ft.Container(
                        expand=1,
                        bgcolor="#1a1a1a",
                        border_radius=15,
                        padding=25,
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.WHITE12), bottom=ft.BorderSide(1, ft.Colors.WHITE12),
                            left=ft.BorderSide(1, ft.Colors.WHITE12), right=ft.BorderSide(1, ft.Colors.WHITE12)
                        ),
                        content=ft.Column([
                            ft.Text("CONTENIDO GENERADO", size=16, weight="bold", color=ft.Colors.WHITE),
                            ft.Text("Estadísticas de tus cuentas actuales.", color=ft.Colors.WHITE54, size=12),
                            ft.Container(height=15),
                            
                            # Contadores estéticos alineados
                            ft.Row([
                                ft.Icon(ft.Icons.IMAGE, color=ft.Colors.WHITE54, size=20),
                                self.texto_cuentas
                            ], spacing=10),
                            
                            ft.Row([
                                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.WHITE54, size=20),
                                self.texto_recibos
                            ], spacing=10)
                            
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    )
                ], 
                height=250, 
                vertical_alignment=ft.CrossAxisAlignment.STRETCH
                )
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)

    # --- MÉTODO DE LECTURA DE BIBLIOTECA HISTÓRICA ---
    def did_mount(self):
        self.cargar_total_biblioteca()

    def cargar_total_biblioteca(self):
        carpeta_cuentas = os.path.join("biblioteca", "cuentas")
        carpeta_recibos = os.path.join("biblioteca", "recibos")
        
        total_cuentas = 0
        total_recibos = 0
        
        if os.path.exists(carpeta_cuentas):
            archivos_c = [f for f in os.listdir(carpeta_cuentas) if f.endswith(('.png', '.jpg', '.jpeg'))]
            total_cuentas = len(archivos_c)
            
        if os.path.exists(carpeta_recibos):
            archivos_r = [f for f in os.listdir(carpeta_recibos) if f.endswith(('.png', '.jpg', '.jpeg'))]
            total_recibos = len(archivos_r)
        
        self.texto_cuentas.value = f"{total_cuentas} cuenta{'s' if total_cuentas != 1 else ''} subida{'s' if total_cuentas != 1 else ''}"
        self.texto_recibos.value = f"{total_recibos} cuenta{'s' if total_recibos != 1 else ''} vendida{'s' if total_recibos != 1 else ''}"
            
        self.texto_cuentas.update()
        self.texto_recibos.update()

    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        bg_color = "#B23A3A" if activo else ft.Colors.TRANSPARENT
        return ft.Container(
            content=ft.Row([
                ft.Icon(icono, color=ft.Colors.WHITE, size=20),
                ft.Text(texto, color=ft.Colors.WHITE, size=14)
            ]),
            bgcolor=bg_color, padding=12, border_radius=10, ink=True,
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )