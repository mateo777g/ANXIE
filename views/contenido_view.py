import flet as ft

from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo_suelto)

# Las cuatro tareas: título, subtítulo, icono (el mismo que su botón de atajo en Inicio) y la
# ruta de MainController.cambiar_vista a la que lleva.
TAREAS = [
    ("IMAGEN CUENTAS", "Genera imágenes para cuentas.", ft.Icons.IMAGE, "generador_miniaturas"),
    ("IMAGEN RECIBOS", "Genera tickets de compra.", ft.Icons.RECEIPT_LONG, "recibo"),
    ("CUENTA PEQUEÑA", "Genera imágenes de cuenta en formato reducido.", ft.Icons.IMAGE_ASPECT_RATIO, "cuenta_pequena"),
    ("RECIBO PEQUEÑO", "Genera tickets de compra en formato reducido.", ft.Icons.RECEIPT, "recibo_pequeno"),
]


class ContenidoView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.padding = 0

        # --- CONTENIDO PRINCIPAL ---
        # La cabecera de Inicio (fecha, título, hueco de 25) y las cuatro tareas en la fila de
        # sus tarjetas: 250 de alto y separación 10. Así el hueco del medio cae justo donde el
        # de las dos tarjetas de Inicio, y títulos, subtítulos y botones en el mismo píxel.
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                fecha_vista(),
                titulo_vista("Crear contenido"),
                ft.Container(height=25),
                ft.Row(
                    [self._crear_tarea(*tarea) for tarea in TAREAS],
                    height=250,
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH
                )
            ])
        )

        self.content = ft.Row([crear_barra_lateral(self.router, "contenido"), main_content],
                              expand=True, spacing=0)

    def _crear_tarea(self, titulo, subtitulo, icono, ruta, bloqueado=False):
        # Una tarjeta por tarea: la cabecera de siempre y, abajo, el botón de atajo de Inicio
        # (mismo icono). La tarjeta entera se pulsa: con el cursor en cualquier parte de ella,
        # su botón se enciende como un atajo, y al pulsar se hunde y abre la tarea. La tarjeta
        # no se mueve.
        boton, _, encender, hundir = boton_atajo_suelto(icono, "Abrir")
        # El botón va abajo, y 7 px por encima del fondo: en Inicio, cabecera y franja de
        # botones miden 191 de los 198 que caben en la tarjeta, y sobran 7 bajo la segunda
        # fila. Así el botón acaba justo donde esa fila (y queda el mismo aire abajo que arriba).
        contenido = ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera_tarjeta(titulo, subtitulo),
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=ft.Row([boton])),
        ], spacing=10))
        if bloqueado:
            # Hoy no hay ninguna bloqueada: apagada y sin eventos.
            return ft.Container(expand=1, opacity=0.4, content=tarjeta_iphone(contenido))
        return tarjeta_iphone(
            contenido,
            on_hover=lambda e: encender(e.data in (True, "true")),
            on_tap_down=lambda _: hundir(),
            on_click=lambda _: self.router.cambiar_vista(ruta)
        )
