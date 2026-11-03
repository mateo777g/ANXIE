import asyncio
import functools
import json
import os
import re

import flet as ft
from PIL import ImageFont

from models import perfil, sesion
from models.dolar_dao import DolarDAO
from models.entorno import recurso
from views import tema
from views.barra_lateral import crear_barra_lateral
from views.login_view import mensaje_error
from views.piezas import (MESES, fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo, boton_atajo_suelto, apagar_boton, campo,
                          etiqueta, globo, aviso, interruptor, sin_auto_update)
from views.tema import C

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

# La ruta va en Medium 14 y en una línea. Si no cabe, Flutter la corta con "…" y sale entera
# en un globo; para saber si cabe se mide con la misma fuente.
FUENTE_RUTA = recurso("assets/PlusJakartaSans-Medium.ttf")
TAM_RUTA = 14

# Los temas del panel (views/tema.py), en el orden del interruptor: texto, icono y su nombre.
TEMAS = [("Oscuro", ft.Icons.DARK_MODE_OUTLINED, "oscuro"),
         ("Claro", ft.Icons.LIGHT_MODE_OUTLINED, "claro")]
# El alto de la tarjeta del tema: su cabecera (75), la separación (10), el interruptor (48) y los
# 7 que dejan las otras tarjetas bajo su botón, más el padding (25 + 25) y el borde (1 + 1).
ALTO_TEMA = 75 + 10 + 48 + 7 + 50 + 2

# Los modos del dólar (3/11), en el orden del interruptor: en vivo (lo trae la base de Frankfurter)
# o manual (el número que pone el cliente). Ver models/dolar_dao.py.
MODOS_DOLAR = [("En vivo", ft.Icons.SYNC), ("Manual", ft.Icons.EDIT_OUTLINED)]


class AjustesView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = C.fondo
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
                       vertical_alignment=ft.CrossAxisAlignment.STRETCH),
                # Debajo, el tema (la idea del dueño, 26/09) y el dólar (3/11), en las mismas dos
                # columnas que las carpetas. Hasta el 3/11 el tema iba solo, de lado a lado.
                ft.Row([self._crear_tarjeta_tema(), self._crear_tarjeta_dolar()], height=ALTO_TEMA,
                       spacing=10, vertical_alignment=ft.CrossAxisAlignment.STRETCH),
            ], spacing=10)
        )

        self.content = ft.Row([crear_barra_lateral(self.router, "ajustes"), main_content],
                              expand=True, spacing=0)

    def did_mount(self):
        self.page_ref = self.router.page
        self.page_ref.run_task(self._cargar_dolar)
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
        texto = ft.Text(ruta, color=C.texto, size=TAM_RUTA, font_family="LetraTexto",
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

    def _crear_tarjeta_tema(self):
        # La cabecera, como las de las carpetas, y abajo el interruptor de Mi biblioteca con los
        # dos temas, en el sitio del botón de las otras (7 px por encima del fondo). Al elegir
        # uno, el botón del interruptor se desliza hasta él y, al acabar, la vista entera se
        # rehace con los colores nuevos (MainController.cambiar_tema).
        nombres = [nombre for _, _, nombre in TEMAS]

        def al_cambiar(i):
            async def cambiar():
                await asyncio.sleep(0.3)   # que se vea el botón llegar a su sitio
                self.router.cambiar_tema(nombres[i])
            self.page_ref.run_task(cambiar)

        selector = interruptor([(texto, icono) for texto, icono, _ in TEMAS],
                               nombres.index(tema.actual()), al_cambiar)
        return tarjeta_iphone(ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera_tarjeta("TEMA", "Los colores del panel: oscuro o claro."),
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=selector),
        ], spacing=10)))

    # ------------------------------------------------------------------
    # El dólar (3/11): de él sale el precio en USD de todas las cuentas
    # ------------------------------------------------------------------
    def _crear_tarjeta_dolar(self):
        # Como la del tema: la cabecera y abajo un interruptor, En vivo / Manual. El subtítulo
        # dice el dólar de ahora ("1 USD = 18.72 MXN · en vivo, del 2 de noviembre"). En Manual,
        # al lado del interruptor, el campo con el número y un botón redondo para guardarlo
        # (o Enter). Todo apagado hasta que llega el dólar de Supabase (_cargar_dolar).
        self.dolar = None                    # la fila de Ajustes, cuando llega
        self.guardando_dolar = False
        cabecera = cabecera_tarjeta("DÓLAR", "Leyendo el dólar…")
        self.subtitulo_dolar = cabecera[1]
        self.selector_dolar = interruptor(MODOS_DOLAR, 0, self._al_cambiar_modo_dolar)
        self.campo_dolar = campo(pista="18.50", tamano=13, expand=False,
                                 al_enviar=sin_auto_update(lambda _: self._guardar_dolar_manual()))
        self.campo_dolar.width = 86
        self.boton_dolar = boton_atajo(ft.Icons.CHECK, None, lambda _: self._guardar_dolar_manual(),
                                       ancho=48)
        self.manual_dolar = ft.Row([self.campo_dolar, self.boton_dolar], spacing=10,
                                   visible=False)
        self._apagar_dolar(True)
        return tarjeta_iphone(ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera,
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=ft.Row(
                [self.selector_dolar, self.manual_dolar], spacing=10)),
        ], spacing=10)))

    def _apagar_dolar(self, apagado):
        # Mientras lee o guarda: el interruptor, el campo y el botón al 40 % y sin eventos.
        for control in (self.selector_dolar, self.campo_dolar):
            control.disabled = apagado
            control.opacity = 0.4 if apagado else 1
        apagar_boton(self.boton_dolar, apagado)

    def _pintar_dolar(self, fila):
        # El subtítulo, el interruptor y el campo según la fila de Ajustes.
        self.dolar = fila
        en_vivo = bool(fila["dolar_en_vivo"])
        self.subtitulo_dolar.value = _texto_dolar(fila)
        self.selector_dolar._elegir(0 if en_vivo else 1)
        self.manual_dolar.visible = not en_vivo
        self.campo_dolar.value = _cifra_dolar(fila["dolar_mxn"])

    async def _cargar_dolar(self):
        try:
            if not await asyncio.to_thread(sesion.comprobar):
                self.subtitulo_dolar.value = "Entra con tu contraseña para ver el dólar."
                self.subtitulo_dolar.update()
                return
            fila = await asyncio.to_thread(DolarDAO.obtener)
        except Exception as e:
            print(f"[ajustes] no se pudo leer el dólar: {type(e).__name__}: {e}")
            fila = None
        if not _montada(self.subtitulo_dolar):
            return
        if not fila:
            self.subtitulo_dolar.value = "No se pudo leer el dólar. Revisa tu internet."
            self.subtitulo_dolar.update()
            return
        self._pintar_dolar(fila)
        self._apagar_dolar(False)
        self.update()

    def _al_cambiar_modo_dolar(self, i):
        # En vivo: la base lo trae ya de Frankfurter. Manual: se queda el dólar de ahora, fijo,
        # y sale el campo para cambiarlo.
        if i == 0:
            self.page_ref.run_task(self._guardar_dolar, None)
        else:
            self.page_ref.run_task(self._guardar_dolar, self.dolar["dolar_mxn"])

    def _guardar_dolar_manual(self):
        valor = _numero_dolar(self.campo_dolar.value)
        if valor is None:
            aviso(self.page_ref, "El dólar tiene que ser un número entre 5 y 60.")
            return
        self.page_ref.run_task(self._guardar_dolar, valor)

    async def _guardar_dolar(self, valor):
        # valor None = en vivo. Al guardarse, la base recalcula el USD de todas las cuentas y la
        # página lo enseña sola (anxiestore.com guarda el catálogo 5 minutos en cada visitante).
        if self.guardando_dolar or self.dolar is None:
            return
        self.guardando_dolar = True
        antes = self.dolar
        self.subtitulo_dolar.value = "Guardando el dólar…"
        self._apagar_dolar(True)
        self.update()
        try:
            if valor is None:
                fila = await asyncio.to_thread(DolarDAO.poner_en_vivo)
            else:
                fila = await asyncio.to_thread(DolarDAO.poner_manual, valor)
        except Exception as e:
            print(f"[ajustes] no se pudo guardar el dólar: {type(e).__name__}: {e}")
            fila = None
            texto = mensaje_error(e, "No se guardó el dólar")
        self.guardando_dolar = False
        if not _montada(self.subtitulo_dolar):
            return
        self._pintar_dolar(fila or antes)
        self._apagar_dolar(False)
        self.update()
        if fila is None:
            aviso(self.page_ref, texto)
        elif fila["dolar_en_vivo"]:
            aviso(self.page_ref, "Dólar en vivo. Precios en USD al día.")
        else:
            aviso(self.page_ref, "Dólar guardado. Precios en USD al día.")

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
        # Solo cambia sus dos claves: en config.json también va el perfil (models/perfil.py).
        if self.es_en_la_nube: return
        try:
            perfil.guardar_config({
                "ruta_descargas_cuentas": self.textos_ruta["cuentas"].value,
                "ruta_descargas_recibos": self.textos_ruta["recibos"].value
            })
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


def _texto_dolar(fila):
    # "1 USD = 18.72 MXN · en vivo, del 2 de noviembre" (el día de la tasa del Banco Central
    # Europeo, que va en dolar_fuente) o "1 USD = 18.50 MXN · manual".
    tasa = f"1 USD = {_cifra_dolar(fila['dolar_mxn'])} MXN"
    if not fila["dolar_en_vivo"]:
        return f"{tasa} · manual"
    dia = re.search(r"(\d{4})-(\d{2})-(\d{2})", fila.get("dolar_fuente") or "")
    if not dia:
        return f"{tasa} · en vivo"
    return f"{tasa} · en vivo, del {int(dia[3])} de {MESES[int(dia[2]) - 1].lower()}"


def _cifra_dolar(valor):
    # 18.7197 → "18.72"; 18.5 → "18.50" (como se escribe un tipo de cambio).
    try:
        return f"{float(valor):.2f}"
    except (TypeError, ValueError):
        return ""


def _numero_dolar(texto):
    # "18.5", "$18.50", "18,50" → 18.5; None si no es un dólar creíble (de 5 a 60 pesos, lo que
    # deja también la base).
    limpio = re.sub(r"[\s$]|MXN", "", (texto or "").replace(",", "."), flags=re.I)
    try:
        numero = float(limpio)
    except ValueError:
        return None
    return round(numero, 4) if 5 <= numero <= 60 else None


def _montada(control):
    # ¿Sigue en pantalla? (se pudo salir de Ajustes mientras se esperaba a Supabase)
    try:
        return control.page is not None and control.parent is not None
    except RuntimeError:
        return False
