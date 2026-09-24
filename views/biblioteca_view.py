import json
import os
import re
import shutil

import flet as ft

from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo, boton_atajo_suelto, interruptor, globo,
                          aviso)

# Las dos pestañas: texto, icono (el mismo que su atajo en Inicio y su contador) y carpeta.
PESTANAS = [
    ("Cuentas", ft.Icons.IMAGE, "cuentas"),
    ("Recibos", ft.Icons.RECEIPT_LONG, "recibos"),
]

# Cómo se reparte cada pestaña: columnas, forma de sus imágenes (ancho / alto) y a qué ancho
# se decodifican. Las cuentas (3840 × 2160, 16:9) van en las dos columnas de las tarjetas de
# Inicio, y los recibos (2160 × 3840, 9:16) en las cuatro de Crear contenido. Las imágenes se
# decodifican ya pequeñas (cache_width): enteras ocupan 33 MB de memoria cada una para
# enseñarse a unos 400 px.
FORMATOS = {
    "cuentas": (2, 16 / 9, 1280),
    "recibos": (4, 9 / 16, 720),
}

# Lo que mide "Descargar" con su icono (84 px, medido) y 8 de aire a cada lado. Si el botón
# queda más estrecho (recibos en una ventana de menos de unos 1210 px), se queda con el icono.
ANCHO_DESCARGAR = 100


class BibliotecaView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.padding = 0

        self.tipo_actual = "cuentas"  # Por defecto arranca mostrando cuentas

        # --- CABECERA ---
        # La de Inicio (fecha, título, hueco de 25), y el interruptor en la línea del título,
        # centrado en la vista: así las tarjetas empiezan a la misma altura que las de Inicio
        # y Crear contenido. El título manda el alto de la fila; el interruptor va encima,
        # centrado en todo el ancho.
        interruptor_pestanas = interruptor([(texto, icono) for texto, icono, _ in PESTANAS], 0,
                                           self._al_cambiar_pestana)
        cabecera = ft.Stack([
            ft.Row([titulo_vista("Mi biblioteca")]),
            ft.Container(left=0, top=0, right=0, bottom=0, alignment=ft.Alignment.CENTER,
                         content=interruptor_pestanas),
        ], clip_behavior=ft.ClipBehavior.NONE)

        # --- GALERÍA ---
        # Filas de tarjetas con la separación de Inicio (10 entre tarjetas y entre filas).
        self.galeria = ft.Column(spacing=10)

        # Toda la vista se desplaza junta, cabecera incluida: con la cabecera fija, las
        # tarjetas se cortarían en seco bajo el título.
        main_content = ft.Column([
            ft.Container(padding=40, content=ft.Column([
                fecha_vista(),
                cabecera,
                ft.Container(height=25),
                self.galeria,
            ]))
        ], expand=True, scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        # STRETCH: una columna con scroll dentro de una fila se encoge a su contenido y la fila
        # la centraba en vertical. Estirada mide lo que la ventana, y el contenido va arriba
        # como en Inicio. La barra ya medía el alto entero: no cambia.
        self.content = ft.Row([crear_barra_lateral(self.router, "biblioteca"), main_content],
                              expand=True, spacing=0,
                              vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def did_mount(self):
        self.page_ref = self.router.page
        # Al cambiar el ancho de la ventana, "Descargar" puede dejar de caber (o volver a caber).
        self.page_ref.on_resize = self._al_cambiar_tamano
        self.page_ref.update()
        self.cargar_biblioteca()

    def will_unmount(self):
        if self.page_ref.on_resize == self._al_cambiar_tamano:
            self.page_ref.on_resize = None

    def _al_cambiar_tamano(self, e):
        # Solo se rehace la galería si cambia algo: arrastrando el borde llega un evento por píxel.
        if self._descargar_cabe() != self.descargar_con_texto:
            self.cargar_biblioteca()

    def _descargar_cabe(self):
        # ¿Cabe el texto en el botón "Descargar"? La ventana menos la barra (250) y los márgenes
        # (80), repartida en columnas con separación 10; y de cada tarjeta, su borde y padding
        # (52), el botón redondo (48) y la separación entre los dos (12).
        columnas = FORMATOS[self.tipo_actual][0]
        contenido = (self.page_ref.width or 1264) - 250 - 80
        tarjeta = (contenido - 10 * (columnas - 1)) / columnas
        return tarjeta - 52 - 48 - 12 >= ANCHO_DESCARGAR

    def _al_cambiar_pestana(self, indice):
        self.tipo_actual = PESTANAS[indice][2]
        self.cargar_biblioteca()

    def cargar_biblioteca(self):
        carpeta = os.path.join("biblioteca", self.tipo_actual)
        archivos = []
        if os.path.exists(carpeta):
            archivos = [f for f in os.listdir(carpeta) if f.endswith(('.png', '.jpg', '.jpeg'))]
        # Las más nuevas primero: la que se acaba de generar sale arriba a la izquierda.
        archivos.sort(key=lambda f: _momento(carpeta, f), reverse=True)

        self.descargar_con_texto = self._descargar_cabe()
        if archivos:
            columnas = FORMATOS[self.tipo_actual][0]
            tarjetas = [self._crear_tarjeta_imagen(os.path.abspath(os.path.join(carpeta, f)), f)
                        for f in archivos]
            self.galeria.controls = _en_filas(tarjetas, columnas)
        else:
            self.galeria.controls = [self._crear_vacia()]
        self.galeria.update()

    def _crear_tarjeta_imagen(self, ruta_absoluta, nombre_archivo):
        # La tarjeta de Inicio con la imagen arriba, con la forma de la imagen (16:9 o 9:16) y
        # esquinas redondeadas, y debajo sus dos botones de atajo: "Descargar" a lo ancho y
        # "Eliminar", redondo y solo con el icono (sin rojo: ver DISENO.md).
        _, proporcion, decodificar = FORMATOS[self.tipo_actual]
        imagen = ft.Container(
            aspect_ratio=proporcion,
            border_radius=10,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            # Mientras carga, el hueco de la imagen se ve como la cara de un botón.
            bgcolor="#0DFFFFFF",
            content=ft.Image(src=f"biblioteca/{self.tipo_actual}/{nombre_archivo}",
                             fit=ft.BoxFit.COVER, cache_width=decodificar)
        )
        descargar = boton_atajo(ft.Icons.DOWNLOAD_ROUNDED,
                                "Descargar" if self.descargar_con_texto else None,
                                lambda e, n=nombre_archivo, r=ruta_absoluta: self.descargar_imagen(n, r))
        if not self.descargar_con_texto:
            descargar.tooltip = globo("Descargar")
        # "Eliminar" solo lleva el icono y borra sin preguntar: con el cursor encima dice qué hace.
        eliminar = boton_atajo(ft.Icons.DELETE_OUTLINE, None,
                               lambda e, r=ruta_absoluta: self.borrar_imagen(r), ancho=48)
        eliminar.tooltip = globo("Eliminar")
        botones = ft.Row([descargar, eliminar], spacing=12)
        return tarjeta_iphone(ft.Column([imagen, botones], spacing=20))

    def _crear_vacia(self):
        # Pestaña sin imágenes: una tarjeta como las de Crear contenido (cabecera arriba y el
        # botón abajo, en el sitio de la segunda fila de atajos de Inicio) que lleva a Crear
        # contenido. Se pulsa entera. Mide lo que una tarjeta de Inicio (250 de alto y la mitad
        # del ancho) y va centrada bajo el interruptor.
        if self.tipo_actual == "cuentas":
            subtitulo = "Las imágenes de cuentas que generes aparecerán aquí."
        else:
            subtitulo = "Los recibos que generes aparecerán aquí."
        boton, _, encender, hundir = boton_atajo_suelto(ft.Icons.AUTO_AWESOME_OUTLINED, "Crear contenido")
        contenido = ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera_tarjeta("BIBLIOTECA VACÍA", subtitulo),
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=ft.Row([boton])),
        ], spacing=10))
        tarjeta = tarjeta_iphone(
            contenido,
            on_hover=lambda e: encender(e.data in (True, "true")),
            on_tap_down=lambda _: hundir(),
            on_click=lambda _: self.router.cambiar_vista("contenido")
        )
        tarjeta.expand = 2
        # Con separación 5 y huecos de 1 a cada lado, la tarjeta mide (ancho − 10) / 2, lo mismo
        # que una de Inicio, y sus bordes caen donde los de la segunda y la tercera tarjeta de
        # Crear contenido.
        return ft.Row([ft.Container(expand=1), tarjeta, ft.Container(expand=1)],
                      spacing=5, height=250, vertical_alignment=ft.CrossAxisAlignment.STRETCH)

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
        aviso(self.page_ref, mensaje)


def _momento(carpeta, archivo):
    # Cuándo se hizo una imagen: los generadores ponen la hora en el nombre
    # (cuentas_1790255079.png); si no la lleva, la fecha del archivo.
    hora = re.search(r"_(\d+)\.", archivo)
    return int(hora.group(1)) if hora else os.path.getmtime(os.path.join(carpeta, archivo))


def _en_filas(tarjetas, columnas):
    # Reparte las tarjetas en filas de `columnas`; la última se completa con huecos para que
    # sus tarjetas midan lo mismo que las de arriba.
    filas = []
    for k in range(0, len(tarjetas), columnas):
        fila = tarjetas[k:k + columnas]
        fila += [ft.Container(expand=1) for _ in range(columnas - len(fila))]
        filas.append(ft.Row(fila, spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))
    return filas
