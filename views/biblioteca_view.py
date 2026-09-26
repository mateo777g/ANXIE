import asyncio
import json
import math
import os
import re
import shutil

import flet as ft

from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo, boton_atajo_suelto, interruptor, globo,
                          aviso, aislar, sin_auto_update)

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

# Abrir por partes (lo pidió el dueño el 25/09): al abrir una pestaña salen al momento las filas
# que caben en la ventana y una más; el resto llega detrás, unas TANDA tarjetas cada vez (en filas
# enteras: 4 filas de cuentas o 2 de recibos), con una pausa de PAUSA segundos entre tandas para que
# los eventos (el cursor, un clic) pasen entre medias. Cada tanda frena los eventos lo que tarda en
# hacerse y mandarse: con 8 tarjetas, unos 40 ms (medido el 26/09; con 24, más de 150).
TANDA = 8
PAUSA = 0.03


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
        # Cada pestaña ya hecha, por tipo (ver _armar): sus archivos, sus tarjetas y sus filas.
        self.pestanas = {}
        # Mientras la vista está abierta, las tandas siguen llegando (_seguir_cargando).
        self.montada = False

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
        # Toda la vista se desplaza junta, cabecera incluida: con la cabecera fija, las
        # tarjetas se cortarían en seco bajo el título.
        # Es una lista (ListView) con las filas sueltas en ella, y no una columna con scroll, para
        # que Flutter solo dibuje las filas que se ven: la columna las dibujaba TODAS al abrir, y
        # con 200 imágenes el panel de escritorio las decodificaba a la vez (4.4 GB de memoria y
        # más de 40 s de CPU; medido el 25/09). El mismo padding (40) y la misma separación (10)
        # que la columna: se ve igual. Van las filas de las dos pestañas; las de la otra,
        # escondidas (_mostrar).
        self.lista = ft.ListView([
            fecha_vista(),
            cabecera,
            ft.Container(height=25),
        ], spacing=10, padding=40, expand=True, scroll=ft.ScrollMode.AUTO)

        # STRETCH: una columna con scroll dentro de una fila se encoge a su contenido y la fila
        # la centraba en vertical. Estirada mide lo que la ventana, y el contenido va arriba
        # como en Inicio. La barra ya medía el alto entero: no cambia.
        self.content = ft.Row([crear_barra_lateral(self.router, "biblioteca"), self.lista],
                              expand=True, spacing=0,
                              vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def did_mount(self):
        self.page_ref = self.router.page
        # Al cambiar el ancho de la ventana, "Descargar" puede dejar de caber (o volver a caber).
        # Sin auto-update: _mostrar() hace su update() (y llega un evento por píxel al arrastrar).
        self._al_redimensionar = sin_auto_update(self._al_cambiar_tamano)
        self.page_ref.on_resize = self._al_redimensionar
        self.page_ref.update()
        self.montada = True
        self._mostrar()

    def will_unmount(self):
        self.montada = False
        if self.page_ref.on_resize == self._al_redimensionar:
            self.page_ref.on_resize = None

    def _al_cambiar_tamano(self, e):
        # Solo se rehace la pestaña si cambia algo: arrastrando el borde llega un evento por píxel.
        if self._pestana_vieja(self.tipo_actual):
            self._mostrar()

    def _descargar_cabe(self, tipo):
        # ¿Cabe el texto en el botón "Descargar"? La ventana menos la barra (250) y los márgenes
        # (80), repartida en columnas con separación 10; y de cada tarjeta, su borde y padding
        # (52), el botón redondo (48) y la separación entre los dos (12).
        columnas = FORMATOS[tipo][0]
        contenido = (self.page_ref.width or 1264) - 250 - 80
        tarjeta = (contenido - 10 * (columnas - 1)) / columnas
        return tarjeta - 52 - 48 - 12 >= ANCHO_DESCARGAR

    def _pestana_vieja(self, tipo):
        # Sin hacer todavía, o hecha con "Descargar" de otro ancho del que cabe ahora.
        pestana = self.pestanas.get(tipo)
        return pestana is None or bool(pestana["archivos"]) and pestana["texto"] != self._descargar_cabe(tipo)

    def _al_cambiar_pestana(self, indice):
        self.tipo_actual = PESTANAS[indice][2]
        self._mostrar()

    def _mostrar(self):
        # Enseña la pestaña actual y esconde la otra. Cada pestaña se hace UNA vez, la primera vez
        # que se enseña, y luego solo se esconde y se enseña: rehacerla en cada cambio de pestaña
        # tardaba 29 s con 200 imágenes (medido el 25/09). Se rehace solo si "Descargar" deja de
        # caber o vuelve a caber (al cambiar el ancho de la ventana).
        # Rehacer va en dos update(): primero se añaden las filas nuevas, escondidas, y luego se
        # quitan las viejas. Un update() que quita miles de controles y a la vez añade otros miles
        # es lentísimo en Flet (compara cada quitado con cada añadido); por separado, no.
        tipo = self.tipo_actual
        for otro, pestana in self.pestanas.items():
            for fila in pestana["filas"]:
                fila.visible = otro == tipo
        if self._pestana_vieja(tipo):
            vieja = self.pestanas.get(tipo)
            nueva = self._armar(tipo)
            self.lista.controls.extend(nueva["filas"])
            if vieja:
                for fila in nueva["filas"]:
                    fila.visible = False
                self.lista.update()
                for fila in vieja["filas"]:
                    self.lista.controls.remove(fila)
                for fila in nueva["filas"]:
                    fila.visible = True
            # Desde aquí, la pestaña vieja (si la había) deja de recibir tandas: su tarea ve que
            # ya no es la de este tipo y se para.
            self.pestanas[tipo] = nueva
            if len(nueva["tarjetas"]) < len(nueva["archivos"]):
                self.page_ref.run_task(self._seguir_cargando, nueva)
        self.lista.update()

    async def _seguir_cargando(self, pestana):
        # El resto de la pestaña, por tandas, detrás de las primeras filas. Entre tanda y tanda
        # suelta el hilo (PAUSA) para que los eventos no esperen. Si mientras tanto se cambia de
        # pestaña, sigue llegando, escondida; si se borra una imagen, sigue desde donde vaya (las
        # que faltan ya son las de después); si la pestaña se rehace (el ancho de la ventana) o se
        # sale de la vista, se para.
        tipo = pestana["tipo"]
        while True:
            await asyncio.sleep(PAUSA)
            if not self.montada or self.pestanas.get(tipo) is not pestana:
                return
            if len(pestana["tarjetas"]) >= len(pestana["archivos"]):
                return
            filas = self._anadir_filas(pestana, max(1, TANDA // FORMATOS[tipo][0]))
            for fila in filas:
                fila.visible = tipo == self.tipo_actual
            self.lista.controls.extend(filas)
            self.lista.update()

    def _filas_primeras(self, tipo):
        # Cuántas filas salen al momento: las que caben en la ventana (debajo de la cabecera, que
        # acaba en y 173) y una más. Una fila mide su imagen (el ancho de la tarjeta sin su borde
        # ni padding, 52, en la forma de la imagen) más los botones y el padding (120), y 10 de
        # separación.
        columnas, proporcion, _ = FORMATOS[tipo]
        contenido = (self.page_ref.width or 1264) - 250 - 80
        tarjeta = (contenido - 10 * (columnas - 1)) / columnas
        fila = (tarjeta - 52) / proporcion + 120 + 10
        alto = (self.page_ref.height or 681) - 173
        return max(1, math.ceil(alto / fila)) + 1

    def _anadir_filas(self, pestana, cuantas):
        # Hace las `cuantas` filas siguientes de la pestaña (o las que queden) y las devuelve.
        # Las tandas son siempre filas enteras, así que solo la última de todas lleva huecos.
        columnas = FORMATOS[pestana["tipo"]][0]
        inicio = len(pestana["tarjetas"])
        fin = min(len(pestana["archivos"]), inicio + cuantas * columnas)
        nuevas = [self._crear_tarjeta_imagen(pestana, k) for k in range(inicio, fin)]
        pestana["tarjetas"] += nuevas
        filas = _en_filas([tarjeta for tarjeta, _, _ in nuevas], columnas)
        pestana["filas"] += filas
        return filas

    def _armar(self, tipo):
        # Lee la carpeta del tipo y hace sus primeras filas (el resto llega por tandas:
        # _seguir_cargando). Cada tarjeta es un sitio fijo: la tarjeta k enseña la imagen k de
        # `archivos`, y sus botones buscan la suya al pulsarse. Así, al borrar una, las de detrás
        # solo cambian de imagen (_quitar).
        carpeta = os.path.join("biblioteca", tipo)
        archivos = []
        if os.path.exists(carpeta):
            archivos = [f for f in os.listdir(carpeta) if f.endswith(('.png', '.jpg', '.jpeg'))]
        # Las más nuevas primero: la que se acaba de generar sale arriba a la izquierda.
        archivos.sort(key=lambda f: _momento(carpeta, f), reverse=True)

        pestana = {"tipo": tipo, "archivos": archivos, "texto": self._descargar_cabe(tipo),
                   "tarjetas": [], "filas": []}
        if archivos:
            self._anadir_filas(pestana, self._filas_primeras(tipo))
        else:
            pestana["filas"] = [self._crear_vacia(tipo)]
        return pestana

    def _crear_tarjeta_imagen(self, pestana, k):
        # La tarjeta de Inicio con la imagen arriba, con la forma de la imagen (16:9 o 9:16) y
        # esquinas redondeadas, y debajo sus dos botones de atajo: "Descargar" a lo ancho y
        # "Eliminar", redondo y solo con el icono (sin rojo: ver DISENO.md).
        # Devuelve la tarjeta, su imagen y su botón "Eliminar".
        tipo = pestana["tipo"]
        _, proporcion, decodificar = FORMATOS[tipo]
        foto = ft.Image(src=_src(tipo, pestana["archivos"][k]), fit=ft.BoxFit.COVER,
                        cache_width=decodificar)
        imagen = ft.Container(
            aspect_ratio=proporcion,
            border_radius=10,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            # Mientras carga, el hueco de la imagen se ve como la cara de un botón.
            bgcolor="#0DFFFFFF",
            content=foto
        )
        descargar = boton_atajo(ft.Icons.DOWNLOAD_ROUNDED,
                                "Descargar" if pestana["texto"] else None,
                                lambda e: self.descargar_imagen(pestana, k))
        if not pestana["texto"]:
            descargar.tooltip = globo("Descargar")
        # "Eliminar" solo lleva el icono y borra sin preguntar: con el cursor encima dice qué hace.
        eliminar = boton_atajo(ft.Icons.DELETE_OUTLINE, None,
                               lambda e: self.borrar_imagen(pestana, k), ancho=48)
        eliminar.tooltip = globo("Eliminar")
        botones = ft.Row([descargar, eliminar], spacing=12)
        # Aislada (piezas.aislar): los update() de la lista no bajan a sus ~40 controles.
        tarjeta = aislar(tarjeta_iphone(ft.Column([imagen, botones], spacing=20)))
        return tarjeta, foto, eliminar

    def _crear_vacia(self, tipo):
        # Pestaña sin imágenes: una tarjeta como las de Crear contenido (cabecera arriba y el
        # botón abajo, en el sitio de la segunda fila de atajos de Inicio) que lleva a Crear
        # contenido. Se pulsa entera. Mide lo que una tarjeta de Inicio (250 de alto y la mitad
        # del ancho) y va centrada bajo el interruptor.
        if tipo == "cuentas":
            subtitulo = "Las imágenes de cuentas que generes aparecerán aquí."
        else:
            subtitulo = "Los recibos que generes aparecerán aquí."
        boton, _, encender, hundir = boton_atajo_suelto(ft.Icons.AUTO_AWESOME_OUTLINED, "Crear contenido")
        contenido = ft.Container(padding=ft.Padding(bottom=7), content=ft.Column([
            *cabecera_tarjeta("BIBLIOTECA VACÍA", subtitulo),
            ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT, content=ft.Row([boton])),
        ], spacing=10))
        # Sin auto-update: encender y hundir hacen su update(), y cambiar_vista su page.update().
        tarjeta = tarjeta_iphone(
            contenido,
            on_hover=sin_auto_update(lambda e: encender(e.data in (True, "true"))),
            on_tap_down=sin_auto_update(lambda _: hundir()),
            on_click=sin_auto_update(lambda _: self.router.cambiar_vista("contenido"))
        )
        tarjeta.expand = 2
        # Con separación 5 y huecos de 1 a cada lado, la tarjeta mide (ancho − 10) / 2, lo mismo
        # que una de Inicio, y sus bordes caen donde los de la segunda y la tercera tarjeta de
        # Crear contenido.
        return ft.Row([ft.Container(expand=1), tarjeta, ft.Container(expand=1)],
                      spacing=5, height=250, vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def borrar_imagen(self, pestana, k):
        ruta = _ruta(pestana["tipo"], pestana["archivos"][k])
        if os.path.exists(ruta):
            os.remove(ruta)
            self.mostrar_snack("Eliminada.")
            self._quitar(pestana, k)

    def _quitar(self, pestana, k):
        # Quita la imagen k sin rehacer la galería (rehacerla, con 200 imágenes, tardaba más de
        # 30 s): las tarjetas de detrás se quedan en su sitio y cada una pasa a enseñar la imagen
        # siguiente; sobra la última tarjeta, que deja su sitio a un hueco (o se va su fila, si se
        # queda sin tarjetas). Se ve lo mismo que antes: todas corridas un sitio.
        tipo, archivos, tarjetas = pestana["tipo"], pestana["archivos"], pestana["tarjetas"]
        columnas = FORMATOS[tipo][0]
        archivos.pop(k)
        if not archivos:
            # Era la última: la tarjeta de "vacía" en su lugar.
            for fila in pestana["filas"]:
                self.lista.controls.remove(fila)
            pestana["tarjetas"], pestana["filas"] = [], [self._crear_vacia(tipo)]
            self.lista.controls.extend(pestana["filas"])
            self.lista.update()
            return
        for j in range(k, min(len(archivos), len(tarjetas))):
            foto = tarjetas[j][1]
            foto.src = _src(tipo, archivos[j])
            foto.update()
        if len(tarjetas) <= len(archivos):
            # Aún faltaban tandas: todas las tarjetas hechas siguen teniendo imagen, y las tandas
            # que quedan ya salen desde la siguiente. No sobra ninguna.
            if k < len(tarjetas):
                tarjetas[k][2]._encender(True)
            return
        ultima = tarjetas.pop()[0]
        fila = pestana["filas"][len(archivos) // columnas]
        fila.controls[fila.controls.index(ultima)] = ft.Container(expand=1)
        if len(archivos) % columnas == 0:
            pestana["filas"].remove(fila)
            self.lista.controls.remove(fila)
            self.lista.update()
        else:
            fila.update()
        # El cursor sigue encima de "Eliminar" (se acaba de pulsar), y ese botón es ahora el de
        # la imagen siguiente: encendido, como sale un botón nuevo bajo el cursor.
        if k < len(tarjetas):
            tarjetas[k][2]._encender(True)

    def descargar_imagen(self, pestana, k):
        nombre_archivo = pestana["archivos"][k]
        ruta_origen = _ruta(pestana["tipo"], nombre_archivo)
        try:
            es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None
            if es_en_la_nube:
                self.page_ref.launch_url(f"/biblioteca/{pestana['tipo']}/{nombre_archivo}")
            else:
                clave_json = f"ruta_descargas_{pestana['tipo']}"
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


def _src(tipo, archivo):
    # La imagen para ft.Image: relativa a la carpeta del panel (su assets_dir).
    return f"biblioteca/{tipo}/{archivo}"


def _ruta(tipo, archivo):
    return os.path.abspath(os.path.join("biblioteca", tipo, archivo))


def _momento(carpeta, archivo):
    # Cuándo se hizo una imagen: los generadores ponen la hora en el nombre
    # (cuentas_1790255079.png); si no la lleva, la fecha del archivo.
    hora = re.search(r"_(\d+)\.", archivo)
    return int(hora.group(1)) if hora else os.path.getmtime(os.path.join(carpeta, archivo))


class _FilaAislada(ft.Row):
    # Una fila de tarjetas que Flet trata como aislada (como piezas.aislar, pero sin envoltorio):
    # el update() de la lista compara lo suyo (si se ve o no) y no baja a sus tarjetas. Con 500
    # imágenes por pestaña, cada tanda que llegaba recorría todas las filas ya puestas y tardaba
    # cada vez más (hasta ~200 ms al final; medido el 26/09). Un cambio en sus tarjetas se manda
    # con su propio update() (así lo hace _quitar).
    def is_isolated(self):
        return True

    def __repr__(self):
        return "FilaAislada"


def _en_filas(tarjetas, columnas):
    # Reparte las tarjetas en filas de `columnas`; la última se completa con huecos para que
    # sus tarjetas midan lo mismo que las de arriba.
    filas = []
    for k in range(0, len(tarjetas), columnas):
        fila = tarjetas[k:k + columnas]
        fila += [ft.Container(expand=1) for _ in range(columnas - len(fila))]
        filas.append(_FilaAislada(fila, spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))
    return filas
