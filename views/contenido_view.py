import flet as ft
import datetime

class ContenidoView(ft.Container):
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
                self._crear_boton_menu("Inicio", ft.Icons.HOME, "home", activo=False),
                self._crear_boton_menu("Crear contenido", ft.Icons.AUTO_AWESOME_OUTLINED, "contenido", activo=True),
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
                
                # Título de la sección
                ft.Text("Crear contenido", size=40, weight="w500", color=ft.Colors.WHITE),
                ft.Text("Selecciona una tarea para comenzar.", color=ft.Colors.WHITE54, size=14),
                
                ft.Container(height=30), # Espacio elegante para que respire la vista
                
                # --- NUEVA FILA DE TARJETAS REDISEÑADAS ---
                ft.Row([
                    # Tarjeta 1: Imagen para venta (Activa)
                    self._crear_bloque_atajo(
                        texto="Imagen Cuentas",
                        descripcion="Genera imagenes para cuentas",
                        icono=ft.Icons.IMAGE,
                        color_icono=ft.Colors.PURPLE_300,
                        ruta="generador_miniaturas",
                        bloqueado=False
                    ),
                    
                    # Tarjeta 2: Imagen Recibos (¡DESBLOQUEADA!)
                    self._crear_bloque_atajo(
                        texto="Imagen Recibos",
                        descripcion="Genera tickets de compra", 
                        icono=ft.Icons.RECEIPT_LONG, # Icono actualizado
                        color_icono=ft.Colors.BLUE_300, # Color actualizado
                        ruta="recibo", # Ruta asignada
                        bloqueado=False # Desbloqueado
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=20)
            ])
        )

        # UNIMOS TODO EN self.content
        self.content = ft.Row([
            sidebar,
            main_content
        ], expand=True, spacing=0)

    # --- NUEVO MÉTODO PARA BLOQUES DE ATAJO PREMIUM ---
    def _crear_bloque_atajo(self, texto, descripcion, icono, color_icono, ruta=None, bloqueado=False):
        return ft.Container(
            width=240,
            height=170,
            bgcolor="#1a1a1a" if not bloqueado else "#161616",
            border_radius=15,
            padding=20,
            # Cambia el borde sutilmente según el estado para dar profundidad
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.WHITE12 if not bloqueado else ft.Colors.WHITE10),
                bottom=ft.BorderSide(1, ft.Colors.WHITE12 if not bloqueado else ft.Colors.WHITE10),
                left=ft.BorderSide(1, ft.Colors.WHITE12 if not bloqueado else ft.Colors.WHITE10),
                right=ft.BorderSide(1, ft.Colors.WHITE12 if not bloqueado else ft.Colors.WHITE10)
            ),
            # Si está bloqueado, apagamos el efecto de click y desactivamos el contenedor
            ink=not bloqueado,
            on_click=lambda _: self.router.cambiar_vista(ruta) if (not bloqueado and ruta) else None,
            
            content=ft.Column([
                # Fila superior de la tarjeta (Icono principal + Candado si aplica)
                ft.Row([
                    ft.Icon(icono, size=30, color=color_icono),
                    ft.Icon(ft.Icons.LOCK_OUTLINED, size=16, color=ft.Colors.WHITE24) if bloqueado else ft.Container()
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=12), # Separación interna
                
                # Textos alineados a la izquierda (Look moderno de Dashboard)
                ft.Text(
                    texto, 
                    color=ft.Colors.WHITE if not bloqueado else ft.Colors.WHITE38, 
                    weight="bold", 
                    size=16
                ),
                ft.Container(height=4),
                ft.Text(
                    descripcion, 
                    color=ft.Colors.WHITE54 if not bloqueado else ft.Colors.WHITE24, 
                    size=12,
                    max_lines=2
                )
            ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.START)
        )

    # --- HELPER PARA BOTONES DEL MENÚ ---
    def _crear_boton_menu(self, texto, icono, ruta, activo=False):
        bg_color = "#B23A3A" if activo else ft.Colors.TRANSPARENT
        return ft.Container(
            content=ft.Row([
                ft.Icon(icono, color=ft.Colors.WHITE, size=20),
                ft.Text(texto, color=ft.Colors.WHITE, size=14)
            ]),
            bgcolor=bg_color,
            padding=12,
            border_radius=10,
            ink=True,
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )