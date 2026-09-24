import os
import flet as ft
from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, tarjeta_iphone, boton_atajo,
                          apagar_boton, campo, hueco_imagen, aviso)
from controllers.app_controller import AppController

# El diseño del panel encima de lo que ya había, sin mover nada (regla 11 de DISENO.md): cada
# bloque, campo y botón sigue en su sitio, en su orden y de su tamaño.

class Image1View(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page 
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.padding = 0

        self.controller = AppController(self, tipo="cuentas")

        # --- COMPONENTES VISUALES ---
        # Los campos, con la letra y los colores del panel (campo(), en piezas.py): los mismos
        # textos, valores y relleno de siempre.
        self.input_picos = campo(pista="Selecciona el archivo de Picos...", relleno=10, solo_lectura=True)
        self.input_skins = campo(pista="Selecciona el archivo de Skins...", relleno=10, solo_lectura=True)
        self.input_emotes = campo(pista="Selecciona el archivo de Emotes...", relleno=10, solo_lectura=True)

        self.txt_picos = campo(etiqueta="Texto Picos", valor="¡PICOS!")
        self.txt_skins = campo(etiqueta="Texto Skins")
        self.txt_emotes = campo(etiqueta="Texto Emotes")

        self.input_nombre = campo(etiqueta="Nombre de la descarga", valor="cuenta", expand=False)

        # --- CONTENEDOR DE VISTA PREVIA ---
        self.texto_espera = ft.Text("Esperando Generación...", color=ft.Colors.WHITE54, size=14,
                                    font_family="CreatoDisplayLight")
        self.preview_image = ft.Image(src="", expand=True, visible=False)

        # El hueco de la imagen (hueco_imagen(), en piezas.py): ocupa todo el alto que queda y
        # todo el ancho, como siempre.
        self.image_container = hueco_imagen(ft.Column(
            [self.texto_espera, self.preview_image],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ))

        # --- BOTONES ---
        # Botones de atajo, con su animación, en la medida de siempre (45 de alto, a partes
        # iguales). "Descargar" va apagado (al 40 %, sin eventos) hasta que se genera una imagen.
        self.btn_generar = boton_atajo(ft.Icons.IMAGE, "Generar Imagen",
                                       self.controller.procesar_clicks, alto=45)

        self.btn_descargar = boton_atajo(ft.Icons.DOWNLOAD, "Descargar",
                                         self.controller.descargar_imagen, alto=45)
        apagar_boton(self.btn_descargar, True)

        # --- SIDEBAR ---
        sidebar = crear_barra_lateral(self.router, "contenido")

        # --- PANEL IZQUIERDO ---
        left_panel = ft.Container(
            expand=1,
            content=ft.Column([
                ft.Row([
                    # 1. Tu columna de siempre, pero le ponemos expand=True para que ocupe lo que pueda
                    ft.Column([
                        ft.Text("Configuración de la imagen", color=ft.Colors.WHITE54, font_family="CreatoDisplay"),
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
        # Una tarjeta del panel en la medida del panel de antes: radio 15, y el borde de 1 px +
        # padding 25 dejan el contenido donde lo dejaban.
        right_panel = tarjeta_iphone(
            ft.Column([
                ft.Text("Vista Previa", color=ft.Colors.WHITE, size=20, font_family="CreatoDisplay"),
                self.image_container, # Ahora sí, se va a estirar a lo bestia
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.input_nombre, 
                ft.Divider(height=15, color=ft.Colors.WHITE12),
                ft.Row([self.btn_generar, self.btn_descargar], spacing=15)
            ], spacing=15, expand=True), # <- Importante que este expand siga aquí
            radio=15, padding=25
        )

        # --- ARMADO FINAL ---
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                fecha_vista(),
                ft.Row([
                    # La flecha, un botón de atajo redondo de 40: la medida del botón de antes.
                    boton_atajo(ft.Icons.ARROW_BACK_IOS_NEW, None,
                                lambda _: self.router.cambiar_vista("contenido"), ancho=40, alto=40),
                    titulo_vista("Generar Imagen de Venta", 35),
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
        apagar_boton(self.btn_descargar, False)
        
        # 4. Actualizamos
        self.image_container.update()
        self.btn_descargar.update()


    def mostrar_snack(self, mensaje):
        # Abajo del todo, entre los botones y el borde: a 40, como en las otras vistas,
        # taparía medio botón "Generar".
        aviso(self.page_ref, mensaje, abajo=9)


    # ==========================================
    # HELPERS
    # ==========================================
    def _crear_bloque_input(self, titulo, path_field, text_field):
        # Una tarjeta del panel en la medida del bloque de antes (radio 10, y borde + padding
        # 15), que no se estira en la columna. La carpeta, un botón de atajo redondo de 40.
        return tarjeta_iphone(ft.Column([
                ft.Text(titulo, color=ft.Colors.WHITE, font_family="CreatoDisplay"),
                ft.Row([
                    path_field,
                    boton_atajo(ft.Icons.FOLDER_OPEN, None,
                                lambda _: self.abrir_explorador_nativo(path_field), ancho=40, alto=40)
                ]),
                ft.Row([ft.Icon(ft.Icons.TEXT_FIELDS, color=ft.Colors.WHITE54, size=20), text_field])
            ]), radio=10, padding=15, expand=None)
