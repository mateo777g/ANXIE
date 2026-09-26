import asyncio
import datetime
import math
import re
import unicodedata

import flet as ft

from models import sesion
from models.cuenta_dao import CuentaDAO, EscrituraSinEfecto
from models.r2_storage import R2Storage, ImagenNoValida, ErrorR2, comprobar_foto
from models.supabase_client import FaltaConfiguracion
from views.barra_lateral import crear_barra_lateral
from views.login_view import mensaje_error
from views.piezas import (MESES, fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo, boton_atajo_suelto, apagar_boton, campo,
                          etiqueta, globo, aviso, capa_ventana, sin_auto_update)
from views.tema import C

# --- CUENTAS ---
# El inventario de la tienda (la tabla Cuentas de Supabase, lo que vende anxiestore.com): lo que
# hacía lilshop.html, dentro del panel. Se hace por subfases (planes/plan panel flet.txt, en
# pagina/): la 1 es esta vista con la tabla, el buscador y el contador (y la entrada con
# contraseña, que desde el 24/09 va al abrir el panel: views/login_view.py); la 2, el ojo
# (ocultar / mostrar en la página); la 3, los tres puntos (una ventanita con todos los datos); la
# 5 y la 6, Editar (el lápiz) y "Agregar cuenta", que abren la misma ventana con el formulario y
# suben la foto directo a R2 (models/r2_storage.py); la 7, "Eliminar" en los tres puntos (la fila
# y su foto). El diseño, en DISENO.md ("Distribución de Cuentas").

# Las columnas de la tabla: título y peso (expand). Las acciones miden fijo: tres botones
# redondos de 36 con 8 entre ellos.
COLUMNAS = [("CUENTA", 7), ("DESCRIPCIÓN", 3), ("PLATAFORMAS", 3), ("PRECIO", 2),
            ("VISIBILIDAD", 2)]
SEPARACION = 14
BOTON = 36
ANCHO_ACCIONES = 3 * BOTON + 2 * 8
# La foto de cada fila, con la forma de las de la tienda (16:9), decodificada pequeña: entera,
# una foto de 1600 o 2560 px ocuparía megas de memoria para enseñarse a 80.
FOTO_ANCHO, FOTO_ALTO = 80, 45
# Lo que mide una fila: la foto (45, lo más alto de la fila: los textos van a 2 líneas como mucho
# y las pastillas a 2 filas) y su padding (12 + 12). Encima de cada una, su raya de 1.
ALTO_FILA = FOTO_ALTO + 24
# Abrir por partes (2.3e, 26/09, como Mi biblioteca): al abrir salen al momento las filas que caben
# en la ventana y una más; el resto llega detrás, TANDA filas cada vez, con PAUSA segundos entre
# tandas para que los eventos (el cursor, una tecla del buscador) pasen entre medias.
TANDA = 8
PAUSA = 0.03
# Los avisos con la ventana de Editar / Agregar abierta: a 40 (el margen de las vistas) tapaban
# medio "Guardar"; a 9, en el hueco de debajo de la tarjeta, como en los generadores.
ABAJO_VENTANA = 9

# Las plataformas, con los nombres y las mismas expresiones que la página (renderPlataformasHTML
# de catalogo.html): "disponibilidad" es texto libre y la página busca esto en él.
PLATAFORMAS = [
    (re.compile(r"\b(PC|COMPU|DESKTOP)\b", re.I), "PC"),
    (re.compile(r"\b(XBOX|XBX|XONE)\b", re.I), "XBOX"),
    (re.compile(r"\b(PLAY|PS|PS4|PS5|PLAYSTATION)\b", re.I), "PLAY"),
    (re.compile(r"\b(NINTENDO|SWITCH|SWUICH|NSW)\b", re.I), "NINTENDO"),
]


class CuentasView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = C.fondo
        self.gradient = fondo_pagina()
        self.padding = 0

        self.cuentas = []          # tal como vienen de Supabase, las más nuevas primero
        self.filas = {}            # id de la cuenta → su fila en la tabla (para cambiar solo esa)
        self.rayas = {}            # id de la cuenta → la raya de encima de su fila
        self.hechas = 0            # cuántas de self.cuentas tienen ya su fila (llegan por tandas)
        self.lista = None          # la lista de filas de la tabla (ver _pintar_tabla)
        # Se llega por el atajo "Agregar Cuenta" de Inicio: la ventana de Agregar se abre
        # sola en cuanto están las cuentas (_cargar). Se lee y se borra aquí, así no vuelve a
        # abrirse al entrar otra vez por el menú.
        self.abrir_agregar = getattr(router, "abrir_agregar_cuenta", False)
        router.abrir_agregar_cuenta = False

        # --- CABECERA ---
        # La de Inicio: fecha, título y un hueco de 25. El título es el contador ("12 cuentas en
        # tu tienda", con las ocultas: es todo lo que se administra aquí); antes de entrar dice
        # "Cuentas". "Agregar cuenta" va en la línea del título, a la derecha.
        self.titulo = titulo_vista("Cuentas")
        self.boton_agregar = boton_atajo(ft.Icons.ADD, "Agregar cuenta",
                                         lambda _: self._abrir_formulario(None), ancho=180)
        self.boton_agregar.visible = False
        cabecera = ft.Row([self.titulo, self.boton_agregar],
                          alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                          vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # --- BUSCADOR ---
        # Filtra la tabla ya cargada mientras se escribe (no vuelve a Supabase en cada tecla).
        self.buscador = campo(pista="Busca por título, skins, plataforma o precio…",
                              icono=ft.Icons.SEARCH, tamano=13,
                              al_cambiar=sin_auto_update(self._filtrar))
        self.fila_buscador = ft.Row([self.buscador], visible=False)

        # Lo de debajo del buscador: la tabla, o la tarjeta de entrar, de cargando o de error.
        self.cuerpo = ft.Column(spacing=10)

        # Toda la vista se desplaza junta, cabecera incluida (como Mi biblioteca).
        main_content = ft.Column([
            ft.Container(padding=40, content=ft.Column([
                fecha_vista(),
                cabecera,
                ft.Container(height=25),
                self.fila_buscador,
                self.cuerpo,
            ]))
        ], expand=True, scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        # Las ventanitas (los tres puntos, y después Editar y Agregar) van en una capa encima del
        # contenido, no de la barra: son "de esta sección".
        # Mientras Editar o Agregar guardan (subir la foto, escribir la fila), la ventana no se
        # cierra con el velo ni con Escape.
        self.guardando = False
        self.selector = None       # el selector de archivos de Windows (ft.FilePicker), al primer uso
        self.capa, self.abrir_ventana, self.cerrar_ventana = capa_ventana(
            self.page_ref, se_puede_cerrar=lambda: not self.guardando)
        main_content.left = main_content.top = main_content.right = main_content.bottom = 0
        seccion = ft.Stack([main_content, self.capa], expand=True)

        self.content = ft.Row([crear_barra_lateral(self.router, "cuentas"), seccion],
                              expand=True, spacing=0,
                              vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def did_mount(self):
        self.page_ref = self.router.page
        # Escape cierra la ventanita abierta.
        self.page_ref.on_keyboard_event = self._al_teclear
        self.page_ref.update()
        self.page_ref.run_task(self._arrancar)

    def will_unmount(self):
        if self.page_ref.on_keyboard_event == self._al_teclear:
            self.page_ref.on_keyboard_event = None

    def _al_teclear(self, e):
        # Cada tecla que se pulsa en la vista (también al escribir en el buscador) pasa por
        # aquí: sin auto-update (piezas.sin_auto_update), cerrar_ventana() hace su update().
        ft.context.disable_auto_update()
        if e.key == "Escape":
            self.cerrar_ventana()

    # ------------------------------------------------------------------
    # Entrar
    # ------------------------------------------------------------------
    async def _arrancar(self):
        # Se entra al abrir el panel (views/login_view.py) y la sesión se recuerda. Aquí se
        # comprueba que siga valiendo (la primera vez en cada ejecución, con el servidor): si ya
        # no vale, a la pantalla de entrar; sin internet, la tarjeta "SIN CONEXIÓN".
        try:
            dentro = await asyncio.to_thread(sesion.comprobar)
        except FaltaConfiguracion:
            self._poner_cuerpo([self._tarjeta_centrada(
                "FALTA EL ARCHIVO .ENV",
                "Sin él, el panel no sabe a qué tienda conectarse. Va en la carpeta del panel.")])
            return
        except Exception as e:
            print(f"[cuentas] no se pudo comprobar la sesión: {type(e).__name__}: {e}")
            self._sin_conexion(self._arrancar)
            return
        if not _montada(self.cuerpo):
            return      # se salió de la vista mientras se comprobaba
        if dentro:
            await self._cargar()
        else:
            self.router.mostrar_login("Tu sesión se cerró. Vuelve a entrar.", "cuentas")

    def _sin_conexion(self, reintentar):
        self._poner_cuerpo([self._tarjeta_centrada(
            "SIN CONEXIÓN", "No se pudieron traer las cuentas. Revisa tu internet.",
            boton=(ft.Icons.REFRESH, "Reintentar", lambda: self.page_ref.run_task(reintentar)))])

    # ------------------------------------------------------------------
    # La tabla
    # ------------------------------------------------------------------
    async def _cargar(self):
        self._poner_cuerpo([self._tarjeta_tabla([self._nota("Cargando cuentas…")], "Un momento…")])
        try:
            self.cuentas = await asyncio.to_thread(CuentaDAO.obtener_todas)
        except Exception as e:
            print(f"[cuentas] no se pudieron traer: {e}")
            if _sin_permiso(e):
                sesion.olvidar()
                self.router.mostrar_login("Tu sesión se cerró. Vuelve a entrar.", "cuentas")
            else:
                self._sin_conexion(self._cargar)
            return
        self.boton_agregar.visible = True
        self.fila_buscador.visible = True
        self._pintar_tabla()
        if self.abrir_agregar:
            self.abrir_agregar = False
            self._abrir_formulario(None)
        # Fotos viejas que no se pudieron borrar de R2 otra vez (al editar con foto nueva): se
        # reintentan callando, detrás (si sigue sin poder, siguen apuntadas).
        self.page_ref.run_task(self._reintentar_fotos)

    async def _reintentar_fotos(self):
        try:
            if await asyncio.to_thread(R2Storage.pendientes):
                quedan = await asyncio.to_thread(R2Storage.reintentar_pendientes)
                print(f"[cuentas] fotos por borrar en R2: quedan {quedan}")
        except Exception as e:
            print(f"[cuentas] no se pudieron reintentar las fotos por borrar: {e}")

    def _pintar_tabla(self):
        # La tabla se hace UNA vez, con todas las cuentas; el buscador solo esconde y enseña
        # filas (_filtrar). Rehacerla en cada tecla mandaba sus ~900 controles de Python a
        # Flutter por tecla: ~370 ms cada una (medido el 25/09).
        # Con muchas cuentas (2.3e, medido el 26/09 en el panel de escritorio con 200: 1.3 s de
        # Python y ~1.2 s más de Flutter para abrir, 290 ms el ojo, hasta 180 ms una tecla del
        # buscador y el cursor sobre las filas a trompicones), como Mi biblioteca:
        #   - las filas van en una ft.ListView dentro de la tarjeta, del alto justo de las filas
        #     que se ven (no se desplaza sola: la rueda sigue moviendo la vista entera). Flutter
        #     pone cada fila en su propia capa: el cursor encima de un botón repinta esa fila, no
        #     las 200 (en una columna repintaba la tabla entera en cada fotograma: tras desplazar,
        #     la ventana se quedaba congelada 0.8-1 s con el cursor encima de los botones);
        #   - las filas van aisladas (_FilaAislada): el update() de la lista no baja a sus 73
        #     controles, así que el ojo, el buscador y salir de la vista comparan ~400 controles
        #     en vez de ~15 000;
        #   - salen por partes: las que caben en la ventana y una más, y el resto por tandas
        #     (_seguir_cargando).
        if not _montada(self.cuerpo):
            return      # se salió de la vista mientras llegaban las cuentas
        self._poner_contador()
        total = len(self.cuentas)
        self.filas, self.rayas, self.hechas = {}, {}, 0
        self.nota_sin_resultados = self._nota("")
        if self.cuentas:
            # build_controls_on_demand=False: la lista mide lo que todas sus filas, así que Flutter
            # las hace todas de todas formas; hechas de una vez, el buscador las esconde y las
            # vuelve a enseñar sin rehacerlas (a demanda, con 200: 525 ms en volver a enseñarlas
            # todas y 260-290 en esconderlas; así, 33 y ~170; medido el 26/09).
            self.lista = ft.ListView(spacing=0, build_controls_on_demand=False)
            self._anadir_filas(self._filas_primeras())
            self._aplicar_filtro()
            renglones = [self.lista, self.nota_sin_resultados]
        else:
            self.lista = None
            renglones = [self._nota("Todavía no hay cuentas en la tienda.")]
        self._poner_cuerpo([self._tarjeta_tabla(renglones)])
        self.titulo.update()
        self.boton_agregar.update()
        self.fila_buscador.update()
        if self.hechas < total:
            self.page_ref.run_task(self._seguir_cargando, self.lista)

    def _poner_contador(self):
        total = len(self.cuentas)
        self.titulo.value = f"{total} cuenta en tu tienda" if total == 1 else f"{total} cuentas en tu tienda"

    def _filas_primeras(self):
        # Las filas que caben en la ventana entera (aunque la tabla empieza más abajo: así sobra
        # para cuando se baje un poco) y una más.
        return math.ceil((self.page_ref.height or 681) / (ALTO_FILA + 1)) + 1

    def _anadir_filas(self, cuantas):
        # Hace las filas de las `cuantas` cuentas siguientes (o las que queden), cada una con su
        # raya encima, y las pone al final de la lista.
        nuevas = self.cuentas[self.hechas:self.hechas + cuantas]
        for c in nuevas:
            self.rayas[c["id"]] = ft.Container(height=1, bgcolor=C.linea)
            self.filas[c["id"]] = self._crear_fila(c)
            self.lista.controls += [self.rayas[c["id"]], self.filas[c["id"]]]
        self.hechas += len(nuevas)

    async def _seguir_cargando(self, lista):
        # El resto de las filas, por tandas. Se para si se sale de la vista o si la tabla se hace
        # de nuevo (otra lista). Cada tanda pasa por el buscador: si ya hay algo escrito, las que
        # no coinciden llegan escondidas.
        while self.hechas < len(self.cuentas):
            await asyncio.sleep(PAUSA)
            if self.lista is not lista or not _montada(lista):
                return
            self._anadir_filas(TANDA)
            cambiados = self._aplicar_filtro()
            lista.update()
            if self.nota_sin_resultados in cambiados:
                self.nota_sin_resultados.update()

    def _filtrar(self, _):
        # Cada tecla del buscador: un solo update() de la lista, que solo compara sus filas
        # (aisladas) y manda las que se esconden o aparecen, y el de la nota si cambia.
        if not self.lista or not _montada(self.cuerpo):
            return
        cambiados = self._aplicar_filtro()
        if len(cambiados) > (self.nota_sin_resultados in cambiados):
            self.lista.update()
        if self.nota_sin_resultados in cambiados:
            self.nota_sin_resultados.update()

    def _aplicar_filtro(self):
        # Esconde las filas que no coinciden con el buscador (y sus rayas), ajusta el alto de la
        # lista a las que quedan y enseña «Ninguna cuenta coincide» si no queda ninguna (cuando ya
        # han llegado todas: mientras llegan tandas, puede coincidir una que aún no está).
        # Devuelve los controles que cambiaron.
        busqueda = _normalizar(self.buscador.value or "")
        cambiados, ninguna, vistas = [], True, 0
        for c in self.cuentas[:self.hechas]:
            coincide = not busqueda or busqueda in _texto_busqueda(c)
            for control, visible in ((self.filas[c["id"]], coincide),
                                     (self.rayas[c["id"]], coincide and not ninguna)):
                if control.visible != visible:
                    control.visible = visible
                    cambiados.append(control)
            ninguna = ninguna and not coincide
            vistas += coincide
        # La lista mide lo que sus filas (y las rayas entre ellas): sin alto, dentro de la tarjeta
        # no sabría cuánto medir. Sin ninguna, se esconde (no hay alto 0 en una ListView).
        alto = vistas * (ALTO_FILA + 1) - 1 if vistas else None
        if self.lista.height != alto or self.lista.visible != bool(vistas):
            self.lista.height, self.lista.visible = alto, bool(vistas)
            cambiados.append(self.lista)
        ninguna = ninguna and self.hechas == len(self.cuentas)
        nota, texto = self.nota_sin_resultados, self.nota_sin_resultados.content
        valor = f"Ninguna cuenta coincide con «{(self.buscador.value or '').strip()}»."
        if nota.visible != ninguna or (ninguna and texto.value != valor):
            nota.visible, texto.value = ninguna, valor
            cambiados.append(nota)
        return cambiados

    def _tarjeta_tabla(self, renglones, subtitulo=None):
        # Una tarjeta de Inicio a todo el ancho, con su cabecera: el título y, de subtítulo,
        # cuántas se ven en la página y cuántas están ocultas. Debajo, los títulos de las
        # columnas (Light 12, WHITE54: el subtítulo de una tarjeta), una raya y las filas.
        self.subtitulo_tabla = cabecera_tarjeta("INVENTARIO", subtitulo or self._texto_visibles())
        encabezados = ft.Container(
            padding=ft.Padding(bottom=12),
            content=ft.Row([
                *[ft.Text(texto, expand=peso, color=C.texto_suave, size=12,
                          font_family="CreatoDisplayLight") for texto, peso in COLUMNAS],
                ft.Container(width=ANCHO_ACCIONES),
            ], spacing=SEPARACION))
        tabla = ft.Column([encabezados, ft.Container(height=1, bgcolor=C.linea), *renglones],
                          spacing=0)
        return tarjeta_iphone(ft.Column([*self.subtitulo_tabla, tabla], spacing=10), expand=None)

    def _texto_visibles(self):
        if not self.cuentas:
            return "Las cuentas que subas aparecerán aquí."
        ocultas = sum(1 for c in self.cuentas if not c.get("visible", True))
        visibles = len(self.cuentas) - ocultas
        texto = f"{visibles} visible{'s' if visibles != 1 else ''} en anxiestore.com"
        if ocultas:
            texto += f" · {ocultas} oculta{'s' if ocultas != 1 else ''}"
        return texto + ". El ojo oculta una cuenta de la página o la vuelve a mostrar."

    def _crear_fila(self, cuenta):
        visible = bool(cuenta.get("visible", True))
        # La foto al 40 % si está oculta: lo que en el panel se ve apagado no está activo
        # (como un botón apagado o una tarea bloqueada).
        foto = ft.Container(
            width=FOTO_ANCHO, height=FOTO_ALTO, border_radius=6,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=C.cara,          # mientras carga, la cara de un botón (como Mi biblioteca)
            opacity=1 if visible else 0.4,
            content=ft.Image(src=cuenta.get("image_url") or "", fit=ft.BoxFit.COVER,
                             cache_width=FOTO_ANCHO * 3,
                             error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                                   color=C.tenue, size=20)),
        )
        titulo = ft.Text((cuenta.get("titulo") or "").strip(), color=C.texto, size=14,
                         font_family="CreatoDisplay", max_lines=2,
                         overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        descripcion = ft.Text((cuenta.get("descripcion") or "").strip(), color=C.texto_suave,
                              size=12, font_family="CreatoDisplayLight", max_lines=2,
                              overflow=ft.TextOverflow.ELLIPSIS)
        precio = ft.Column([
            ft.Text(_precio(cuenta.get("preciomxn"), "MXN"), color=C.texto, size=14,
                    font_family="CreatoDisplayLight"),
            ft.Text(_precio(cuenta.get("preciousd"), "USD"), color=C.texto_suave, size=12,
                    font_family="CreatoDisplayLight"),
        ], spacing=2)

        ojo = boton_atajo(ft.Icons.VISIBILITY_OFF_OUTLINED if visible else ft.Icons.VISIBILITY_OUTLINED,
                          None, sin_auto_update(lambda _, c=cuenta: self.page_ref.run_task(self._alternar, c)),
                          ancho=BOTON, alto=BOTON)
        ojo.tooltip = globo("Ocultar de la página" if visible else "Mostrar en la página",
                            distancia=BOTON / 2 + 8)
        editar = boton_atajo(ft.Icons.EDIT_OUTLINED, None,
                             sin_auto_update(lambda _, c=cuenta: self._abrir_formulario(c)),
                             ancho=BOTON, alto=BOTON)
        editar.tooltip = globo("Editar", distancia=BOTON / 2 + 8)
        detalles = boton_atajo(ft.Icons.MORE_HORIZ, None,
                               sin_auto_update(lambda _, c=cuenta: self._abrir_detalles(c)),
                               ancho=BOTON, alto=BOTON)
        detalles.tooltip = globo("Ver todos los datos", distancia=BOTON / 2 + 8)

        celdas = [
            ft.Row([foto, titulo], spacing=12, expand=COLUMNAS[0][1],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(content=descripcion, expand=COLUMNAS[1][1]),
            ft.Container(content=_plataformas(cuenta.get("disponibilidad")), expand=COLUMNAS[2][1]),
            ft.Container(content=precio, expand=COLUMNAS[3][1]),
            ft.Container(content=_estado(visible), expand=COLUMNAS[4][1],
                         alignment=ft.Alignment.CENTER_LEFT),
            ft.Row([ojo, editar, detalles], spacing=8, width=ANCHO_ACCIONES),
        ]
        fila = _FilaAislada(
            padding=ft.Padding(top=12, bottom=12),
            content=ft.Row(celdas, spacing=SEPARACION,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER))
        fila.data = ojo
        return fila

    # ------------------------------------------------------------------
    # El ojo: ocultar o mostrar en la página
    # ------------------------------------------------------------------
    async def _alternar(self, cuenta):
        # Solo cambia la columna visible; la cuenta no se borra. Oculta, la regla RLS de lectura
        # pública deja de dársela a la página (anxiestore.com), y la tabla del panel la sigue
        # enseñando, con su foto apagada y "OCULTA". Mientras se guarda, el ojo se apaga.
        nuevo = not bool(cuenta.get("visible", True))
        fila = self.filas.get(cuenta["id"])
        if fila:
            apagar_boton(fila.data, True)
            fila.update()
        try:
            actualizada = await asyncio.to_thread(CuentaDAO.cambiar_visibilidad, cuenta["id"], nuevo)
        except Exception as e:
            print(f"[cuentas] no se pudo cambiar la visibilidad de {cuenta['id']}: {e}")
            if fila and _montada(fila):
                apagar_boton(fila.data, False)
                fila.update()
            if _sin_permiso(e):
                # La sesión ya no vale: se olvida y a entrar otra vez (el cambio no se guardó).
                sesion.olvidar()
                self.router.mostrar_login("No se guardó: la sesión se cerró. Vuelve a entrar.",
                                          "cuentas")
            else:
                aviso(self.page_ref, mensaje_error(e, "No se pudo cambiar"))
            return
        cuenta["visible"] = bool(actualizada.get("visible", nuevo))
        self._cambiar_fila(cuenta)
        if not _montada(self.cuerpo):
            return      # se guardó igual; solo que ya no se está en la vista
        aviso(self.page_ref, "Visible otra vez en anxiestore.com." if cuenta["visible"]
              else "Oculta: ya no sale en anxiestore.com.")

    def _cambiar_fila(self, cuenta):
        # Cambia solo esa fila y el subtítulo, sin volver a pedir la tabla a Supabase.
        vieja = self.filas.get(cuenta["id"])
        if not vieja or not _montada(vieja):
            return
        nueva = self._crear_fila(cuenta)
        nueva.visible = vieja.visible       # si el buscador la tenía escondida, sigue igual
        renglones = vieja.parent.controls
        renglones[renglones.index(vieja)] = nueva
        self.filas[cuenta["id"]] = nueva
        self.subtitulo_tabla[1].value = self._texto_visibles()
        vieja.parent.update()
        self.subtitulo_tabla[1].update()

    # ------------------------------------------------------------------
    # Los tres puntos: todos los datos de una cuenta
    # ------------------------------------------------------------------
    def _abrir_detalles(self, cuenta):
        # Una tarjeta de Inicio del ancho de la tabla (sus mismos bordes): la cabecera (el título
        # de la cuenta y cuándo se subió), la foto grande a la izquierda y los datos a la
        # derecha, cada uno como un dato de Ajustes (su etiqueta encima y el valor debajo), y
        # abajo "Eliminar" y "Cerrar", en las dos mismas columnas (Editar es el lápiz de la fila).
        # "Eliminar" pregunta antes, en la misma ventana (ver _pedir_confirmacion).
        visible = bool(cuenta.get("visible", True))
        foto = ft.Container(
            aspect_ratio=16 / 9, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=C.cara,
            content=ft.Image(src=cuenta.get("image_url") or "", fit=ft.BoxFit.COVER,
                             cache_width=1280,
                             error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                                   color=C.tenue, size=28)))
        precio = ft.Column([
            ft.Text(_precio(cuenta.get("preciomxn"), "MXN"), color=C.texto, size=14,
                    font_family="CreatoDisplayLight"),
            ft.Text(_precio(cuenta.get("preciousd"), "USD"), color=C.texto_suave, size=12,
                    font_family="CreatoDisplayLight"),
        ], spacing=2)
        datos = ft.Column([
            ft.Row([_dato(ft.Icons.SELL_OUTLINED, "Precio", precio),
                    _dato(ft.Icons.TOLL_OUTLINED, "V-Bucks", _texto_dato(_vbucks(cuenta.get("vbucks"))))],
                   spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([_dato(ft.Icons.SPORTS_ESPORTS_OUTLINED, "Plataformas",
                          _plataformas(cuenta.get("disponibilidad"))),
                    _dato(ft.Icons.VISIBILITY_OUTLINED if visible else ft.Icons.VISIBILITY_OFF_OUTLINED,
                          "En la página", _estado(visible))],
                   spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([_dato(ft.Icons.NOTES, "Descripción", _descripcion(cuenta.get("descripcion")))]),
        ], spacing=18, expand=1)

        cabecera = cabecera_tarjeta((cuenta.get("titulo") or "").strip().upper(), _subida(cuenta))
        botones = ft.Row(spacing=25)
        eliminar = boton_atajo(ft.Icons.DELETE_OUTLINE, "Eliminar",
                               lambda _: self._pedir_confirmacion(cuenta, cabecera[1], botones))
        cerrar = boton_atajo(ft.Icons.CLOSE, "Cerrar", lambda _: self.cerrar_ventana())
        botones.controls = [eliminar, cerrar]

        tarjeta = tarjeta_iphone(ft.Column([
            *cabecera,
            ft.Row([ft.Container(content=foto, expand=1), datos], spacing=25,
                   vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Container(height=10),
            botones,
        ], spacing=10, tight=True), expand=None)
        self.abrir_ventana(tarjeta)

    # ------------------------------------------------------------------
    # Eliminar (subfase 2.7): desde los tres puntos
    # ------------------------------------------------------------------
    def _pedir_confirmacion(self, cuenta, subtitulo, botones):
        # Una cuenta borrada no vuelve: el primer "Eliminar" solo pregunta, en la misma ventana.
        # El subtítulo pasa a la pregunta y los dos botones, a "Sí, eliminar" / "No, dejarla" en
        # sus mismos sitios. "No" (o cerrar la ventana) no borra nada.
        antes = subtitulo.value, list(botones.controls)

        def volver(_):
            subtitulo.value, botones.controls = antes[0], antes[1]
            subtitulo.update()
            botones.update()

        si = boton_atajo(ft.Icons.DELETE_OUTLINE, "Sí, eliminar",
                         lambda _: self.page_ref.run_task(self._eliminar, cuenta, subtitulo, botones))
        no = boton_atajo(ft.Icons.UNDO, "No, dejarla", volver)
        subtitulo.value = ("¿Eliminar esta cuenta? Se borra de la tienda con su foto y no se puede "
                           "deshacer. Para quitarla solo un tiempo, usa el ojo.")
        botones.controls = [si, no]
        subtitulo.update()
        botones.update()

    async def _eliminar(self, cuenta, subtitulo, botones):
        # Primero la fila (si falla, no se toca nada más: la cuenta sigue entera), después su foto
        # de R2 (si falla, queda apuntada y se reintenta al abrir Cuentas: nunca una huérfana
        # olvidada). La foto solo se borra si ninguna otra cuenta la usa. Mientras, la ventana no
        # se cierra (self.guardando) y los botones van apagados.
        self.guardando = True
        for boton in botones.controls:
            apagar_boton(boton, True)
        subtitulo.value = "Eliminando…"
        botones.update()
        subtitulo.update()
        try:
            borrada = await asyncio.to_thread(CuentaDAO.borrar, cuenta["id"])
        except Exception as e:
            print(f"[cuentas] no se pudo eliminar la cuenta {cuenta['id']}: {type(e).__name__}: {e}")
            self.guardando = False
            if _sin_permiso(e):
                self.cerrar_ventana()
                sesion.olvidar()
                self.router.mostrar_login("No se eliminó: la sesión se cerró. Vuelve a entrar.",
                                          "cuentas")
                return
            if _montada(subtitulo):
                for boton in botones.controls:
                    apagar_boton(boton, False)
                subtitulo.value = "No se eliminó. Puedes intentarlo otra vez."
                botones.update()
                subtitulo.update()
            aviso(self.page_ref, mensaje_error(e, "No se eliminó"), abajo=ABAJO_VENTANA)
            return

        foto = borrada.get("image_url") or cuenta.get("image_url")
        otra = any(c is not cuenta and c.get("image_url") == foto for c in self.cuentas)
        foto_pendiente = False
        if foto and not otra:
            try:
                await asyncio.to_thread(R2Storage.borrar_foto, foto)
            except ValueError:
                pass            # no es una foto del bucket (una URL rara): no se toca
            except Exception as e:
                print(f"[cuentas] la foto {foto} quedó por borrar: {e}")
                foto_pendiente = True

        self.guardando = False
        self._quitar_fila(cuenta)
        if _montada(subtitulo):
            self.cerrar_ventana()
        if _montada(self.cuerpo):
            aviso(self.page_ref, "Cuenta eliminada: ya no sale en anxiestore.com."
                  + (" Su foto se borrará después." if foto_pendiente else ""))

    def _quitar_fila(self, cuenta):
        # Quita la fila y su raya de la lista sin rehacer la tabla (como Mi biblioteca al borrar),
        # con el contador y el subtítulo al día. Sin ninguna cuenta, la tabla vacía.
        posicion = next((i for i, c in enumerate(self.cuentas) if c is cuenta), None)
        if posicion is None:
            return
        del self.cuentas[posicion]
        if posicion < self.hechas:
            self.hechas -= 1
        fila, raya = self.filas.pop(cuenta["id"], None), self.rayas.pop(cuenta["id"], None)
        if not _montada(self.cuerpo):
            return
        if not self.cuentas:
            self._pintar_tabla()
            return
        if self.lista and fila is not None:
            self.lista.controls = [c for c in self.lista.controls if c is not fila and c is not raya]
        cambiados = self._aplicar_filtro()
        self._poner_contador()
        self.subtitulo_tabla[1].value = self._texto_visibles()
        self.lista.update()
        if self.nota_sin_resultados in cambiados:
            self.nota_sin_resultados.update()
        self.titulo.update()
        self.subtitulo_tabla[1].update()

    # ------------------------------------------------------------------
    # Editar y Agregar: la misma ventana (subfases 2.5 y 2.6)
    # ------------------------------------------------------------------
    def _abrir_formulario(self, cuenta):
        # La ventana de los tres puntos, con campos donde había datos: la misma tarjeta del ancho
        # de la tabla, la foto a la izquierda (con "Cambiar foto" debajo) y a la derecha cada dato
        # con su etiqueta encima (las mismas etiquetas e iconos que los tres puntos), y abajo
        # "Guardar cambios" y "Cancelar" en las dos columnas. Sin `cuenta`, "Agregar cuenta": vacía,
        # y la foto es obligatoria. Todos los campos son obligatorios, como en lilshop.
        nueva = cuenta is None
        c = cuenta or {}
        estado = {"ruta": None}             # la foto nueva elegida (ruta en esta PC), o None

        campos = {
            "titulo": campo(pista="Ej: Cuenta Fortnite OG Travis Scott", valor=c.get("titulo") or "",
                            tamano=13),
            "preciomxn": campo(pista="Ej: 700", valor=_cifra(c.get("preciomxn")), tamano=13),
            "preciousd": campo(pista="Ej: 41", valor=_cifra(c.get("preciousd")), tamano=13),
            "vbucks": campo(pista="Ej: 1,500", valor=str(c.get("vbucks") or ""), tamano=13),
            "disponibilidad": campo(pista="Ej: PC XBOX PLAY",
                                    valor=c.get("disponibilidad") or "", tamano=13),
            "descripcion": campo(pista="Ej: 85 skins | OG STW | Travis Scott (cada cosa con |)",
                                 valor=c.get("descripcion") or "", tamano=13),
        }
        campos["descripcion"].multiline = True
        campos["descripcion"].min_lines = campos["descripcion"].max_lines = 3

        # La foto: la de la cuenta, o un hueco con su icono (Agregar). Al elegir una, sale ahí.
        imagen = ft.Image(src=c.get("image_url") or "", fit=ft.BoxFit.COVER, cache_width=1280,
                          error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                                color=C.tenue, size=28))
        hueco = ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, color=C.tenue, size=28)
        foto = ft.Container(
            aspect_ratio=16 / 9, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=C.cara, alignment=ft.Alignment.CENTER,
            content=imagen if c.get("image_url") else hueco)
        nota_foto = ft.Text("JPG, PNG o WebP, hasta 15 MB. Se sube en WebP de hasta 2560 px.",
                            color=C.texto_suave, size=12, font_family="CreatoDisplayLight")
        boton_foto = boton_atajo(ft.Icons.IMAGE_OUTLINED, "Elegir foto" if nueva else "Cambiar foto",
                                 lambda _: self.page_ref.run_task(self._elegir_foto, estado, foto,
                                                                  imagen, nota_foto))
        datos = ft.Column([
            ft.Row([_dato(ft.Icons.TITLE, "Título", campos["titulo"])]),
            ft.Row([_dato(ft.Icons.SELL_OUTLINED, "Precio en MXN", campos["preciomxn"]),
                    _dato(ft.Icons.ATTACH_MONEY, "Precio en USD", campos["preciousd"])], spacing=12),
            ft.Row([_dato(ft.Icons.TOLL_OUTLINED, "V-Bucks", campos["vbucks"]),
                    _dato(ft.Icons.SPORTS_ESPORTS_OUTLINED, "Plataformas", campos["disponibilidad"])],
                   spacing=12),
            ft.Row([_dato(ft.Icons.NOTES, "Descripción", campos["descripcion"])]),
        ], spacing=14, expand=1)

        subtitulo = ("Llena todos los datos y elige la foto. Sale en anxiestore.com al guardar."
                     if nueva else _subida(c))
        cabecera = cabecera_tarjeta("AGREGAR CUENTA" if nueva else "EDITAR CUENTA", subtitulo)
        botones = []
        guardar = boton_atajo(ft.Icons.ADD if nueva else ft.Icons.CHECK,
                              "Agregar cuenta" if nueva else "Guardar cambios",
                              lambda _: self.page_ref.run_task(
                                  self._guardar, cuenta, campos, estado, cabecera[1], botones))
        cancelar = boton_atajo(ft.Icons.CLOSE, "Cancelar", lambda _: self.cerrar_ventana())
        botones += [guardar, cancelar, boton_foto]

        tarjeta = tarjeta_iphone(ft.Column([
            *cabecera,
            ft.Row([ft.Column([foto, ft.Row([boton_foto]), nota_foto], spacing=12, expand=1), datos],
                   spacing=25, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Container(height=10),
            ft.Row([guardar, cancelar], spacing=25),
        ], spacing=10, tight=True), expand=None)
        self.abrir_ventana(tarjeta)

    async def _elegir_foto(self, estado, foto, imagen, nota):
        # El selector de archivos de Windows (el de Flet: no bloquea la ventana, al contrario que
        # el de tkinter de los generadores). La foto se comprueba al momento (pesa, es imagen) y
        # sale en el hueco; se convierte y se sube al guardar.
        if self.selector is None:
            self.selector = ft.FilePicker()        # se registra solo en la página; se guarda aquí
        try:
            archivos = await self.selector.pick_files(
                dialog_title="Elige la foto de la cuenta",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "gif", "bmp"])
        except Exception as e:
            print(f"[cuentas] el selector de archivos falló: {e}")
            aviso(self.page_ref, "No se pudo abrir el selector de archivos.", abajo=ABAJO_VENTANA)
            return
        if not archivos or not archivos[0].path:
            return                                  # cerró el selector sin elegir
        ruta = archivos[0].path
        try:
            tamano = await asyncio.to_thread(comprobar_foto, ruta)
        except ImagenNoValida as e:
            aviso(self.page_ref, str(e), abajo=ABAJO_VENTANA)
            return
        if not _montada(foto):
            return                                  # la ventana se cerró mientras
        estado["ruta"] = ruta
        imagen.src = ruta
        foto.content = imagen
        nombre = ruta.replace("\\", "/").rsplit("/", 1)[-1]
        peso = (f"{tamano / 1024 / 1024:.1f} MB" if tamano >= 1024 * 1024
                else f"{max(1, round(tamano / 1024))} KB")
        nota.value = f"{nombre} · {peso}. Se sube al guardar."
        foto.update()
        nota.update()

    async def _guardar(self, cuenta, campos, estado, subtitulo, botones):
        nueva = cuenta is None
        datos, falta = _leer_formulario(campos)
        if not falta and nueva and not estado["ruta"]:
            falta = "Falta la foto."
        if falta:
            aviso(self.page_ref, falta, abajo=ABAJO_VENTANA)
            return

        # Mientras guarda: los botones apagados, el subtítulo dice qué hace y la ventana no se
        # cierra (se_puede_cerrar de capa_ventana).
        texto_antes = subtitulo.value

        def trabajando(texto):
            self.guardando = texto is not None
            for boton in botones:
                apagar_boton(boton, self.guardando)
                boton.update()
            subtitulo.value = texto or texto_antes
            subtitulo.update()

        subida = None
        try:
            if estado["ruta"]:
                trabajando("Subiendo la foto…")
                subida = await asyncio.to_thread(R2Storage.subir_foto, estado["ruta"])
                datos["image_url"] = subida["url"]
            trabajando("Guardando…")
            if nueva:
                fila = await asyncio.to_thread(CuentaDAO.crear, datos)
            else:
                fila = await asyncio.to_thread(CuentaDAO.actualizar, cuenta["id"], datos)
        except Exception as e:
            print(f"[cuentas] no se pudo guardar: {type(e).__name__}: {e}")
            if subida:
                # La foto nueva ya estaba en R2 pero la fila no se guardó: fuera, que no quede
                # huérfana (si tampoco se puede, queda apuntada y se reintenta al volver).
                try:
                    await asyncio.to_thread(R2Storage.borrar_foto, subida["nombre"])
                except Exception as e2:
                    print(f"[cuentas] la foto nueva {subida['nombre']} quedó por borrar: {e2}")
            self.guardando = False
            if _montada(subtitulo):
                trabajando(None)
            if _sin_permiso(e):
                self.cerrar_ventana()
                sesion.olvidar()
                self.router.mostrar_login("No se guardó: la sesión se cerró. Vuelve a entrar.",
                                          "cuentas")
            else:
                aviso(self.page_ref, _mensaje_guardar(e), abajo=ABAJO_VENTANA)
            return

        # Editando con foto nueva: la vieja se borra SOLO ahora que la fila ya apunta a la nueva.
        vieja_sin_borrar = False
        vieja = (cuenta or {}).get("image_url")
        if subida and vieja and vieja != subida["url"]:
            try:
                await asyncio.to_thread(R2Storage.borrar_foto, vieja)
            except ValueError:
                pass            # no es una foto del bucket (una URL rara): no se toca
            except Exception as e:
                print(f"[cuentas] la foto vieja {vieja} quedó por borrar: {e}")
                vieja_sin_borrar = True

        self.guardando = False
        if nueva:
            self._agregar_fila(fila)
            texto = "Cuenta agregada: ya sale en anxiestore.com."
        else:
            cuenta.update(fila)
            self._cambiar_fila(cuenta)
            texto = "Cambios guardados."
        if vieja_sin_borrar:
            texto += " La foto vieja se borrará después."
        if _montada(subtitulo):
            self.cerrar_ventana()
        if _montada(self.cuerpo):
            aviso(self.page_ref, texto)

    def _agregar_fila(self, cuenta):
        # La cuenta nueva va arriba del todo (las más nuevas primero), sin rehacer la tabla: su
        # fila y su raya al principio de la lista, y el contador y el subtítulo al día.
        self.cuentas.insert(0, cuenta)
        if not _montada(self.cuerpo):
            return
        if self.lista is None:
            self._pintar_tabla()            # era la tienda vacía: ahora sí hay tabla
            return
        self.rayas[cuenta["id"]] = ft.Container(height=1, bgcolor=C.linea)
        self.filas[cuenta["id"]] = self._crear_fila(cuenta)
        self.lista.controls[0:0] = [self.rayas[cuenta["id"]], self.filas[cuenta["id"]]]
        self.hechas += 1
        cambiados = self._aplicar_filtro()
        self._poner_contador()
        self.subtitulo_tabla[1].value = self._texto_visibles()
        self.lista.update()
        if self.nota_sin_resultados in cambiados:
            self.nota_sin_resultados.update()
        self.titulo.update()
        self.subtitulo_tabla[1].update()

    # ------------------------------------------------------------------
    # Piezas de la vista
    # ------------------------------------------------------------------
    def _poner_cuerpo(self, controles):
        self.cuerpo.controls = controles
        if _montada(self.cuerpo):     # se pudo salir de la vista mientras se esperaba a Supabase
            self.cuerpo.update()

    def _nota(self, texto):
        # Lo que va en la tabla cuando no hay filas (cargando, sin resultados, vacía): Light 13
        # WHITE54, centrado.
        return ft.Container(
            padding=ft.Padding(top=28, bottom=16), alignment=ft.Alignment.CENTER,
            content=ft.Text(texto, color=C.texto_suave, size=13,
                            font_family="CreatoDisplayLight"))

    def _tarjeta_centrada(self, titulo, subtitulo, contenido=None, boton=None):
        # Una tarjeta de Inicio (250 de alto, la mitad del ancho) centrada, como la tarjeta vacía
        # de Mi biblioteca: la cabecera arriba, `contenido` en el sitio de la primera fila de
        # atajos y `boton` (un atajo ya hecho, o (icono, texto, al_pulsar) para que lo encienda
        # la tarjeta entera) en el de la segunda.
        partes = [*cabecera_tarjeta(titulo, subtitulo)]
        if contenido:
            partes.append(contenido)
        eventos = {}
        if isinstance(boton, tuple):
            icono, texto, al_pulsar = boton
            boton, _, encender, hundir = boton_atajo_suelto(icono, texto)
            eventos = dict(on_hover=sin_auto_update(lambda e: encender(e.data in (True, "true"))),
                           on_tap_down=sin_auto_update(lambda _: hundir()),
                           on_click=sin_auto_update(lambda _: al_pulsar()))
        if boton:
            partes.append(ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT,
                                       content=ft.Row([boton])))
        tarjeta = tarjeta_iphone(ft.Container(padding=ft.Padding(bottom=7),
                                              content=ft.Column(partes, spacing=10)), **eventos)
        tarjeta.expand = 2
        # Con separación 5 y huecos de 1 a cada lado, mide (ancho − 10) / 2: lo que una tarjeta
        # de Inicio, con los bordes donde la segunda y la tercera de Crear contenido.
        return ft.Row([ft.Container(expand=1), tarjeta, ft.Container(expand=1)],
                      spacing=5, height=250, vertical_alignment=ft.CrossAxisAlignment.STRETCH)


class _FilaAislada(ft.Container):
    # Una fila de la tabla que Flet trata como aislada (como piezas.aislar, pero sin envoltorio):
    # el update() de la lista compara la fila (si se ve o no) pero no baja a sus 73 controles. Lo
    # de dentro solo cambia con fila.update() (el ojo apagado mientras guarda) o poniendo una fila
    # nueva en su sitio (_cambiar_fila). __repr__ corto: ver piezas.Aislado.
    def is_isolated(self):
        return True

    def __repr__(self):
        return "FilaAislada"


def _dato(icono, texto, valor):
    # Un dato de la ventana de los tres puntos: su etiqueta encima (icono y texto en WHITE54,
    # como "Carpeta actual" en Ajustes) y el valor debajo, a 6.
    fila, _ = etiqueta(icono, texto)
    return ft.Column([fila, valor], spacing=6, expand=1)


def _texto_dato(texto):
    return ft.Text(texto, color=C.texto, size=14, font_family="CreatoDisplayLight")


def _vbucks(valor):
    # "500", "100VB", "500VB " → "500 V-Bucks"; lo demás, tal cual.
    texto = str(valor or "").strip()
    numero = re.fullmatch(r"([\d.,]+)\s*(V-?BUCKS|VB)?", texto, re.I)
    return f"{numero.group(1)} V-Bucks" if numero else (texto or "—")


def _descripcion(texto):
    # Las descripciones de la tienda son listas separadas por "|" ("85 skins | OG STW | ..."):
    # una pastilla por cosa, como las plataformas. Si no lleva "|", el texto tal cual.
    texto = (texto or "").strip()
    partes = [p.strip() for p in texto.split("|") if p.strip()]
    if len(partes) < 2:
        return _texto_dato(texto or "—")
    return ft.Row([_pastilla(p) for p in partes], spacing=4, run_spacing=4, wrap=True)


def _subida(cuenta):
    # "Subida el 22 de septiembre de 2026 · número 52", en la hora de esta PC.
    try:
        fecha = datetime.datetime.fromisoformat(cuenta["created_at"]).astimezone()
        cuando = f"Subida el {fecha.day} de {MESES[fecha.month - 1].lower()} de {fecha.year}"
    except (KeyError, TypeError, ValueError):
        cuando = "Sin fecha de subida"
    return f"{cuando} · número {cuenta.get('id')}"


def _pastilla(texto):
    # Una pastilla de la tabla: la cara de un botón (blanco al 5 %) con el texto en Light 10.
    return ft.Container(
        bgcolor=C.cara, border_radius=9, padding=ft.Padding(left=7, top=2, right=7, bottom=2),
        content=ft.Text(texto, color=C.texto, size=10, font_family="CreatoDisplayLight"))


def _estado(visible):
    # "VISIBLE" / "OCULTA", en una píldora con la raya del panel. Sin colores (regla 3): la
    # visible en blanco con su punto lleno; la oculta en WHITE54 con el punto hueco.
    color = C.texto if visible else C.texto_suave
    punto = ft.Container(width=6, height=6, border_radius=3,
                         bgcolor=C.texto if visible else None,
                         border=None if visible else ft.Border.all(1, C.texto_suave))
    return ft.Container(
        border=ft.Border.all(1, C.tenue if visible else C.linea), border_radius=11,
        padding=ft.Padding(left=9, top=4, right=10, bottom=4),
        content=ft.Row([punto, ft.Text("VISIBLE" if visible else "OCULTA", color=color, size=10,
                                       font_family="CreatoDisplayLight")],
                       spacing=6, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER))


def _plataformas(disponibilidad):
    # Una pastilla por plataforma, con los nombres de la página. Si el texto no nombra ninguna,
    # se enseña tal cual (la página también).
    texto = (disponibilidad or "").strip()
    nombres = [nombre for regex, nombre in PLATAFORMAS if regex.search(texto)]
    if not nombres:
        return ft.Text(texto or "—", color=C.texto_suave, size=12,
                       font_family="CreatoDisplayLight", max_lines=2,
                       overflow=ft.TextOverflow.ELLIPSIS)
    return ft.Row([_pastilla(nombre) for nombre in nombres], spacing=4, run_spacing=4, wrap=True)


def _precio(valor, moneda):
    # "700" → "$700 MXN"; con miles, "$1,800 MXN"; con centavos, se enseñan.
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return f"— {moneda}"
    cifra = f"{int(numero):,}" if numero.is_integer() else f"{numero:,.2f}"
    return f"${cifra} {moneda}"


def _normalizar(texto):
    # Minúsculas y sin tildes: "cripta" encuentra "Crípta".
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").strip()


def _texto_busqueda(cuenta):
    # Dónde busca el buscador: título, descripción (las skins), plataformas, V-Bucks y precios.
    partes = [cuenta.get(k) for k in ("titulo", "descripcion", "disponibilidad", "vbucks",
                                      "preciomxn", "preciousd")]
    return _normalizar(" ".join(str(p) for p in partes if p is not None))


def _montada(control):
    # ¿Sigue en pantalla? (se pudo salir de la vista, o repintar la tabla, mientras se guardaba)
    try:
        return control.page is not None and control.parent is not None
    except RuntimeError:
        return False


def _sin_permiso(error):
    # La sesión ya no vale: la RLS no dejó escribir (0 filas), Postgres negó el permiso (42501)
    # o el token caducó sin poder renovarse (PGRST301/303: "JWT expired").
    return (isinstance(error, EscrituraSinEfecto)
            or getattr(error, "code", None) in ("42501", "PGRST301", "PGRST303"))


def _cifra(valor):
    # Un precio de la tabla, para el campo: 700 (no "700.0"); vacío si no hay.
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return ""
    return str(int(numero)) if numero.is_integer() else f"{numero:g}"


def _numero(texto):
    # "700", "$1,800", "41.5 USD" → 700, 1800, 41.5; None si no es un número de 0 o más.
    limpio = re.sub(r"[\s$,]|MXN|USD", "", texto or "", flags=re.I)
    try:
        numero = float(limpio)
    except ValueError:
        return None
    if not math.isfinite(numero) or numero < 0:
        return None
    return int(numero) if numero.is_integer() else round(numero, 2)


# Los campos del formulario, en el orden de la ventana, con el aviso de cuando faltan.
FALTAS = [("titulo", "Falta el título."), ("preciomxn", "Falta el precio en MXN."),
          ("preciousd", "Falta el precio en USD."), ("vbucks", "Faltan los V-Bucks."),
          ("disponibilidad", "Faltan las plataformas."), ("descripcion", "Falta la descripción.")]


def _leer_formulario(campos):
    # Los datos del formulario, listos para Supabase, y el aviso de lo primero que falte o esté
    # mal (None si todo está bien). Los precios, números (la columna es numeric); lo demás, texto.
    datos = {clave: (campos[clave].value or "").strip() for clave, _ in FALTAS}
    for clave, texto in FALTAS:
        if not datos[clave]:
            return datos, texto
    for clave, moneda in (("preciomxn", "MXN"), ("preciousd", "USD")):
        numero = _numero(datos[clave])
        if numero is None:
            return datos, f"El precio en {moneda} tiene que ser un número."
        datos[clave] = numero
    return datos, None


def _mensaje_guardar(error):
    # El aviso de un error al guardar: la foto (no vale, R2 dijo que no, faltan las llaves) o
    # Supabase y la red (mensaje_error, el de la pantalla de entrar).
    if isinstance(error, ImagenNoValida):
        return str(error)
    if isinstance(error, ErrorR2):
        return f"No se pudo subir la foto (R2: {error.estado})."
    if isinstance(error, FaltaConfiguracion) and "R2_" in str(error):
        return "No se pudo subir la foto: faltan las llaves de R2 en el .env."
    return mensaje_error(error, "No se guardó")
