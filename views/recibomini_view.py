import os
import flet as ft
from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, tarjeta_iphone, boton_atajo,
                          apagar_boton, campo, opcion_radio, hueco_imagen, aviso)
from views.tema import C
from controllers.app_controller import AppController

# El diseño del panel encima de lo que ya había, sin mover nada (regla 11 de DISENO.md): cada
# bloque, campo y botón sigue en su sitio, en su orden y de su tamaño.

class ReciboPequenoView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page 
        self.expand = True
        self.bgcolor = C.fondo
        self.gradient = fondo_pagina()
        self.padding = 0

        self.controller = AppController(self, tipo="recibos_mini")  # <-- Indicamos que es un recibo mini

        # --- COMPONENTES VISUALES ---
        # Los campos, con la letra y los colores del panel (campo(), en piezas.py): los mismos
        # textos, valores y relleno de siempre.
        self.input_skin = campo(pista="Selecciona el archivo de Skins...", relleno=10, solo_lectura=True)

        self.txt_correo1 = campo(etiqueta="Correo")
        self.txt_correo2 = campo(etiqueta="Contraseña")

        # === NUEVO SELECTOR NFA / FA ===
        # Sin rojo: la elegida en blanco puro y la otra al 54 % (opcion_radio(), en piezas.py).
        self.radio_tipo_cuenta = ft.RadioGroup(
            value="NFA",
            content=ft.Row([
                opcion_radio("NFA"),
                opcion_radio("FA")
            ])
        )

        # Ahora el usuario solo lleva el nombre
        self.txt_usuario = campo(etiqueta="Usuario")

        self.txt_fecha = campo(etiqueta="Fecha", pista="(Deja vacío para automático)")

        self.input_nombre = campo(etiqueta="Nombre de la descarga", valor="recibo", expand=False)

        # --- VISTA PREVIA ---
        self.texto_espera = ft.Text("Esperando Generación...", color=C.texto_suave, size=14,
                                    font_family="CreatoDisplayLight")
        self.preview_image = ft.Image(src="", expand=True, visible=False)

        # El hueco de la imagen (hueco_imagen(), en piezas.py): ocupa todo el alto que queda y
        # todo el ancho, como siempre.
        self.image_container = hueco_imagen(
            ft.Column([self.texto_espera, self.preview_image], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- BOTONES ---
        # Botones de atajo, con su animación, en la medida de siempre (45 de alto, a partes
        # iguales). "Descargar" va apagado (al 40 %, sin eventos) hasta que se genera un recibo.
        self.btn_generar = boton_atajo(ft.Icons.RECEIPT_LONG, "Generar Recibo", self.controller.procesar_clicks, alto=45)
        self.btn_descargar = boton_atajo(ft.Icons.DOWNLOAD, "Descargar", self.controller.descargar_imagen, alto=45)
        apagar_boton(self.btn_descargar, True)

        # --- SIDEBAR ---
        sidebar = crear_barra_lateral(self.router, "contenido")

        # --- PANEL IZQUIERDO ---
        left_panel = ft.Container(
            expand=1,
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Configuración del Recibo", color=C.texto_suave, font_family="CreatoDisplay"),
                        self._crear_bloque_input("Imagen Skins", self.input_skin),
                        # Tarjetas del panel en la medida de los bloques de antes (radio 10, y
                        # borde + padding 15), que no se estiran en la columna.
                        tarjeta_iphone(ft.Column([
                                ft.Text("Textos Superiores", color=C.texto, font_family="CreatoDisplay"),
                                self.txt_correo1, self.txt_correo2
                            ]), radio=10, padding=15, expand=None),
                        tarjeta_iphone(ft.Column([
                                ft.Text("Textos Inferiores", color=C.texto, font_family="CreatoDisplay"),
                                self.radio_tipo_cuenta,
                                self.txt_usuario,
                                self.txt_fecha
                            ]), radio=10, padding=15, expand=None)
                    ], spacing=15, expand=True),
                    ft.Container(width=25)
                ])
            ], scroll=ft.ScrollMode.ADAPTIVE)
        )

        # --- PANEL DERECHO Y ARMADO FINAL ---
        # Una tarjeta del panel en la medida del panel de antes: radio 15, y el borde de 1 px +
        # padding 25 dejan el contenido donde lo dejaban.
        right_panel = tarjeta_iphone(
            ft.Column([
                ft.Text("Vista Previa del Recibo", color=C.texto, size=20, font_family="CreatoDisplay"),
                self.image_container, ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.input_nombre, ft.Divider(height=15, color=C.linea),
                ft.Row([self.btn_generar, self.btn_descargar], spacing=15)
            ], spacing=15, expand=True),
            radio=15, padding=25
        )

        main_content = ft.Container(
            expand=True, padding=40,
            content=ft.Column([
                # La fecha de las otras vistas (fecha_vista(), en piezas.py)
                fecha_vista(),
                ft.Row([
                    # La flecha, un botón de atajo redondo de 40: la medida del botón de antes.
                    boton_atajo(ft.Icons.ARROW_BACK_IOS_NEW, None,
                                lambda _: self.router.cambiar_vista("contenido"), ancho=40, alto=40),
                    titulo_vista("Generar Recibo Pequeño", 35),
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
        apagar_boton(self.btn_descargar, False)
        self.image_container.update()
        self.btn_descargar.update()

    def mostrar_snack(self, mensaje):
        # Abajo del todo, entre los botones y el borde: a 40, como en las otras vistas,
        # taparía medio botón "Generar".
        aviso(self.page_ref, mensaje, abajo=9)

    def _crear_bloque_input(self, titulo, path_field):
        # Una tarjeta del panel en la medida del bloque de antes (radio 10, y borde + padding
        # 15), que no se estira en la columna. La carpeta, un botón de atajo redondo de 40.
        return tarjeta_iphone(ft.Column([
                ft.Text(titulo, color=C.texto, font_family="CreatoDisplay"),
                ft.Row([
                    path_field,
                    boton_atajo(ft.Icons.FOLDER_OPEN, None,
                                lambda _: self.abrir_explorador_nativo(path_field), ancho=40, alto=40)
                ])
            ]), radio=10, padding=15, expand=None)
