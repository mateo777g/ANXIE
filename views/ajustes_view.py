import functools
import json
import os

import flet as ft
from PIL import ImageFont

from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo_suelto, etiqueta, globo, aviso,
                          sin_auto_update)

ARCHIVO_CONFIG = "config.json"

# Las dos carpetas, una tarjeta cada una: clave (en config.json, ruta_descargas_<clave>),
# título, subtítulo e icono (el de su atajo en Inicio, su contador y su pestaña de Mi
# biblioteca, para que se sepa cuál es cuál).
CARPETAS = [
    ("cuentas", "DESCARGAS DE CUENTAS",
     "Carpeta donde se guardan las imágenes de cuentas que descargas.", ft.Icons.IMAGE),
    ("recibos", "DESCARGAS DE RECIBOS",
     "Carpeta donde se guardan los recibos que descargas.", ft.Icons.RECEIPT_LONG),
]

# La ruta va en Light 14 y en una línea. Si no cabe, Flutter la corta con "…" y sale entera
# en un globo; para saber si cabe se mide con la misma fuente.
FUENTE_RUTA = "assets/CreatoDisplay-Light.otf"
TAM_RUTA = 14


class AjustesView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.padding = 0

        self.es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None

        # --- RUTAS ---
        self.ruta_default = os.path.join(os.path.expanduser("~"), "Downloads")
        rutas_guardadas = self.leer_configuracion()
        # El texto de la ruta de cada tarjeta, por clave: de ahí lee guardar_configuracion.
        self.textos_ruta = {}
        tarjetas = []
        for clave, titulo, subtitulo, icono in CARPETAS:
            if self.es_en_la_nube:
                ruta = "Descargas automáticas del navegador"
            else:
                ruta = rutas_guardadas.get(clave, self.ruta_default)
            tarjetas.append(self._crear_tarjeta_carpeta(clave, titulo, subtitulo, icono, ruta))

        # --- CONTENIDO PRINCIPAL ---
        # La cabecera de Inicio (fecha, título, hueco de 25) y las dos carpetas en la fila de
        # sus tarjetas: 250 de alto y separación 10. Así títulos, subtítulos y botones caen en
        # el mismo píxel que en Inicio.
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                fecha_vista(),
                titulo_vista("Ajustes"),
                ft.Container(height=25),
                ft.Row(tarjetas, height=250, spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.STRETCH)
            ])
        )

        self.content = ft.Row([crear_barra_lateral(self.router, "ajustes"), main_content],
                              expand=True, spacing=0)

    def did_mount(self):
        self.page_ref = self.router.page
        # Al cambiar el ancho de la ventana, una ruta larga puede dejar de caber (o volver a
        # caber) en su tarjeta: su globo sale o se va. Sin auto-update: llega un evento por píxel
        # al arrastrar el borde, y _al_cambiar_tamano hace su update() solo si algo cambia.
        self._al_redimensionar = sin_auto_update(self._al_cambiar_tamano)
        self.page_ref.on_resize = self._al_redimensionar
        self.page_ref.update()

    def will_unmount(self):
        if self.page_ref.on_resize == self._al_redimensionar:
            self.page_ref.on_resize = None

    def _al_cambiar_tamano(self, e):
        # Solo se toca la vista si cambia algo: arrastrando el borde llega un evento por píxel.
        if any(self._poner_globo(texto) for texto in self.textos_ruta.values()):
            self.update()

    def _crear_tarjeta_carpeta(self, clave, titulo, subtitulo, icono, ruta):
        # Una tarjeta como las de Crear contenido (la cabecera arriba y un atajo abajo, en el
        # sitio de la segunda fila de atajos de Inicio) con la carpeta en medio, como un
        # contador de Inicio: en el sitio de la primera fila, qué es (el icono de su tipo y
        # "Carpeta actual") y debajo la ruta, en blanco. La tarjeta entera se pulsa: con el
        # cursor encima enciende "Cambiar carpeta", y al pulsar abre el explorador.
        # Etiqueta, ruta y botón caen donde la etiqueta de un contador, su número y la segunda
        # fila de atajos de Inicio.
        fila_etiqueta, _ = etiqueta(icono, "Carpeta actual")
        texto = ft.Text(ruta, color=ft.Colors.WHITE, size=TAM_RUTA, font_family="CreatoDisplayLight",
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self._poner_globo(texto)
        self.textos_ruta[clave] = texto
        boton, _, encender, hundir = boton_atajo_suelto(ft.Icons.FOLDER_OPEN, "Cambiar carpeta")
        # El botón va 7 px por encima del fondo, como en Crear contenido: acaba justo donde la
        # segunda fila de atajos de Inicio.
        contenido = ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera_tarjeta(titulo, subtitulo),
            # Separación 4: la ruta empieza a la altura de los números de los contadores de
            # Inicio (y 312 a 1×), a 11 px de su etiqueta, como ellos.
            ft.Column([fila_etiqueta, texto], spacing=4),
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=ft.Row([boton])),
        ], spacing=10))
        if self.es_en_la_nube:
            # En la nube no se elige carpeta: el botón, apagado, y la tarjeta sin eventos.
            boton.opacity = 0.4
            return tarjeta_iphone(contenido)

        def al_pulsar(_):
            # Deja la tarjeta encendida (no hundida) mientras el explorador está abierto.
            encender(True)
            self.seleccionar_carpeta_tk(clave)

        # Sin auto-update: encender y hundir hacen su update(); elegir la carpeta, el de la ruta
        # (_pintar_ruta) y el del aviso.
        return tarjeta_iphone(
            contenido,
            on_hover=sin_auto_update(lambda e: encender(e.data in (True, "true"))),
            on_tap_down=sin_auto_update(lambda _: hundir()),
            on_click=sin_auto_update(al_pulsar)
        )

    def _poner_globo(self, texto):
        # La ruta entera en un globo, solo si no cabe en su tarjeta (sale cortada con "…"); si
        # cabe, sin globo: diría lo mismo que la tarjeta. Devuelve si ha cambiado algo.
        # El globo sale justo encima de la ruta y tapa entera la fila de "Carpeta actual"
        # (debajo taparía el botón): a 11 del centro de la ruta, su borde de abajo queda a 5 px
        # de las letras y el de arriba por encima del icono.
        deseado = None if self._ruta_cabe(texto.value) else texto.value
        if (texto.tooltip.message if texto.tooltip else None) == deseado:
            return False
        texto.tooltip = globo(deseado, distancia=11, encima=True) if deseado else None
        return True

    def _ruta_cabe(self, ruta):
        # Lo que mide la tarjeta por dentro: la ventana menos la barra (250), los márgenes (80)
        # y la separación (10), entre dos; menos el borde y el padding de la tarjeta (52).
        ancho = ((self.page_ref.width or 1264) - 250 - 80 - 10) / 2 - 52
        try:
            return _fuente_ruta().getlength(ruta) <= ancho
        except Exception:
            return False  # sin poder medirla, mejor con globo

    def _pintar_ruta(self, clave, ruta):
        texto = self.textos_ruta[clave]
        texto.value = ruta
        self._poner_globo(texto)
        texto.update()

    def leer_configuracion(self):
        if os.path.exists(ARCHIVO_CONFIG):
            try:
                with open(ARCHIVO_CONFIG, "r") as f:
                    datos = json.load(f)
                    return {
                        "cuentas": datos.get("ruta_descargas_cuentas", self.ruta_default),
                        "recibos": datos.get("ruta_descargas_recibos", self.ruta_default)
                    }
            except: pass
        return {"cuentas": self.ruta_default, "recibos": self.ruta_default}

    def guardar_configuracion(self, clave):
        # Guarda las dos rutas; se llama al elegir la carpeta `clave` (no hay botón "Guardar":
        # así un cambio no se pierde por salir de la vista sin guardar).
        if self.es_en_la_nube: return
        try:
            with open(ARCHIVO_CONFIG, "w") as f:
                json.dump({
                    "ruta_descargas_cuentas": self.textos_ruta["cuentas"].value,
                    "ruta_descargas_recibos": self.textos_ruta["recibos"].value
                }, f)
            self.mostrar_snack(f"¡Carpeta de {clave} guardada!")
        except Exception as ex:
            self.mostrar_snack(f"Error: {ex}")

    def seleccionar_carpeta_tk(self, clave):
        if self.es_en_la_nube: return
        try:
            carpeta = self.abrir_explorador(clave)
        except Exception as ex:
            self.mostrar_snack(f"Error al abrir explorador: {ex}")
            return
        if carpeta:
            self._pintar_ruta(clave, os.path.normpath(carpeta))
            self.guardar_configuracion(clave)

    def abrir_explorador(self, clave):
        # El explorador de carpetas de Windows. Devuelve la elegida, o "" si se cancela.
        # (Las herramientas de captura lo sustituyen: en una prueba no se abre nunca.)
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        carpeta = filedialog.askdirectory(title=f"Carpeta para {clave}")
        root.destroy()
        return carpeta

    def mostrar_snack(self, mensaje):
        aviso(self.page_ref, mensaje)


@functools.lru_cache(maxsize=1)
def _fuente_ruta():
    return ImageFont.truetype(FUENTE_RUTA, TAM_RUTA)
