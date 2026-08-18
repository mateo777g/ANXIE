import flet as ft
import os
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

class LoginView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e" # Tu fondo oscuro premium

        # --- COMPONENTES VISUALES AL ESTILO GITHUB ---
        
        # El logo de Anxie Store en círculo imitando al Octocat de GitHub
        self.logo = ft.CircleAvatar(
            radius=25, 
            background_image_src="assets/logo.jpg", 
            bgcolor=ft.Colors.WHITE
        )
        
        # Título serio y minimalista en español
        self.titulo = ft.Text(
            "Iniciar sesión", 
            color=ft.Colors.WHITE, 
            size=20, 
            weight="regular"
        )
        
        # Etiqueta arriba del input
        self.label_pin = ft.Text(
            "Master PIN", 
            color=ft.Colors.WHITE, 
            size=14, 
            weight="bold"
        )
        
        # Input que ocupa el ancho completo de la tarjeta
        self.input_pin = ft.TextField(
            hint_text="Ingresa tu PIN",
            password=True,
            can_reveal_password=True,
            text_align="left",
            width=270, # Ajustado al ancho interno de la tarjeta
            bgcolor="#0e0e0e", # Fondo más oscuro para el input
            border_color=ft.Colors.WHITE24,
            color=ft.Colors.WHITE,
            on_submit=self.verificar_acceso
        )

        # Botón de acceso estilizado en español
        self.btn_entrar = ft.ElevatedButton(
            "Iniciar sesión",
            bgcolor="#B23A3A", # Tu color rojo de acento
            color=ft.Colors.WHITE,
            width=270,
            height=40,
            on_click=self.verificar_acceso
        )

        # La tarjeta contenedora (Estructura idéntica al cuadrito de login de GitHub)
        tarjeta_login = ft.Container(
            bgcolor="#1a1a1a",
            padding=20,
            border_radius=6, # Bordes limpios y serios
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.WHITE12), 
                bottom=ft.BorderSide(1, ft.Colors.WHITE12),
                left=ft.BorderSide(1, ft.Colors.WHITE12), 
                right=ft.BorderSide(1, ft.Colors.WHITE12)
            ),
            content=ft.Column(
                [
                    self.label_pin,
                    self.input_pin,
                    ft.Container(height=10), # Separación limpia
                    self.btn_entrar
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START, # Alineado a la izquierda por dentro
                spacing=5
            ),
            width=310 # Ancho fijo para la tarjeta estilo bloque
        )

        # Bloque central que junta el Logo, Título y la Tarjeta (Estructura vertical de GitHub)
        cuerpo_login = ft.Column(
            [
                self.logo,
                ft.Container(height=5),
                self.titulo,
                ft.Container(height=10),
                tarjeta_login
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, # Todo centrado uno abajo del otro
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Centramos todo el esqueleto en la pantalla usando tu Fila/Columna infinita
        self.content = ft.Row(
            [
                ft.Column(
                    [cuerpo_login],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )

    def verificar_acceso(self, e):
        pin_correcto = os.getenv("PIN_SECRETO", "1234")
        
        if self.input_pin.value == pin_correcto:
            self.router.cambiar_vista("home")
        else:
            # Advertencia traducida al español bro
            self.mostrar_snack("PIN incorrecto. Acceso denegado.")
            self.input_pin.value = ""
            self.input_pin.update()

    def mostrar_snack(self, mensaje):
        self.page_ref.overlay.append(ft.SnackBar(ft.Text(mensaje), open=True))
        self.page_ref.update()