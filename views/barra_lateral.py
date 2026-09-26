import flet as ft

from views.piezas import anillo_brillo, sin_auto_update

# --- BARRA LATERAL ---
# Una sola para todas las vistas: cada una la pide con crear_barra_lateral(router, sección),
# donde sección es la ruta de la opción que va marcada. Ver DISENO.md.
#
# El menú lleva UNA píldora con el estilo de los botones de atajos de Inicio (cara de blanco
# translúcido y brillo en dos esquinas). Se queda bajo la sección activa; con el cursor encima
# de una opción se desliza hasta ella y se enciende como un atajo (zoom, cara más clara, texto
# en blanco y el relevo del texto), y al salir el cursor del menú vuelve apagada a la activa.

# Las opciones del menú: texto, icono y ruta de MainController.cambiar_vista. "Cuentas" (el
# inventario de la tienda, fase 2) entró el 24/09 justo encima de Ajustes: las demás siguen en
# su sitio, que el cliente ya se sabe.
SECCIONES = [
    ("Inicio", ft.Icons.HOME, "home"),
    ("Crear contenido", ft.Icons.AUTO_AWESOME_OUTLINED, "contenido"),
    ("Mi biblioteca", ft.Icons.INBOX, "biblioteca"),
    ("Cuentas", ft.Icons.STOREFRONT, "cuentas"),
    ("Ajustes", ft.Icons.SETTINGS, "ajustes"),
]

ANCHO = 210           # la barra (250) menos su padding de 20 por lado
ALTO = 44             # lo que medía cada opción: padding 12 + icono 20 + padding 12
PASO = ALTO + 10      # una opción cada 54 px: su alto más la separación de 10
RADIO = ALTO // 2     # píldora: extremos en semicírculo
# La curva, el tiempo y el zoom de los atajos (y de "Ver catálogo" de la página web).
CURVA = ft.Animation(460, ft.AnimationCurve.EASE_OUT_QUINT)
ZOOM = 1.05
CARA_REPOSO, CARA_ENCENDIDA = "#0DFFFFFF", "#24FFFFFF"
# Blanco al 12 %: sobre la barra sale 43, el mismo tono que la raya de debajo del logo.
BORDE = "#1FFFFFFF"


def crear_barra_lateral(router, activa):
    return ft.Container(
        width=250,
        bgcolor="#0e0e0e",
        # Línea fina en el borde derecho: separa la barra del contenido, que junto a ella es
        # negro (Inicio) o del mismo #0e0e0e que la barra (las vistas viejas). El borde cuenta
        # como padding, por eso el derecho baja a 19: así el menú sigue midiendo 210.
        border=ft.Border(right=ft.BorderSide(1, BORDE)),
        padding=ft.Padding(left=20, top=20, right=19, bottom=20),
        content=ft.Column([
            # Logo y Título
            marca(),
            ft.Divider(height=40, color=ft.Colors.WHITE24),

            # Menú de navegación
            _crear_menu(router, activa),
        ], spacing=10)
    )


def marca(**kwargs):
    # El logo y la marca: arriba de la barra y en la pantalla de entrar (una pieza, regla 9).
    return ft.Row([
        ft.CircleAvatar(radius=25, background_image_src="assets/fragmentless.png", bgcolor=ft.Colors.WHITE),
        ft.Column([
            ft.Text("FRAGMENTLESS", color=ft.Colors.WHITE, size=18, font_family="CreatoDisplay"),
            ft.Text("PANEL", color=ft.Colors.WHITE, size=10, font_family="CreatoDisplay")
        ], spacing=0)
    ], **kwargs)


def _crear_menu(router, activa):
    indice_activo = [ruta for _, _, ruta in SECCIONES].index(activa)
    # Si se llega aquí por un clic en el menú, el cursor sigue encima de la opción pulsada,
    # que ahora es la activa: la barra nueva nace ya encendida ahí, igual que estaba la de la
    # vista anterior. Si naciera apagada, el cursor la volvería a encender y el zoom y el
    # relevo se repetirían a cada clic.
    estado = {"indice": indice_activo, "encendida": getattr(router, "menu_encendido", False)}
    router.menu_encendido = False

    # La píldora va debajo y las opciones encima, en el mismo Stack: las opciones son las que
    # reciben el cursor y el clic. Cada una ocupa su sitio fijo (PASO · i) y la píldora se
    # mueve cambiando su top.
    cara = ft.Container(
        left=0, top=0, right=0, bottom=0, border_radius=RADIO,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    )
    pildora = ft.Container(
        left=0, width=ANCHO, height=ALTO,
        animate_position=CURVA, animate_scale=CURVA,
        # Sin recorte: las máscaras de los anillos sobresalen 2 px de la caja a propósito.
        content=ft.Stack([
            anillo_brillo(ft.Alignment(-1, -1), RADIO, ALTO),
            anillo_brillo(ft.Alignment(1, 1), RADIO, ALTO),
            cara
        ], clip_behavior=ft.ClipBehavior.NONE)
    )
    opciones = [_crear_opcion(texto, icono, PASO * i) for i, (texto, icono, _) in enumerate(SECCIONES)]

    def pintar():
        i, encendida = estado["indice"], estado["encendida"]
        pildora.top = PASO * i
        pildora.scale = ZOOM if encendida else 1
        cara.bgcolor = CARA_ENCENDIDA if encendida else CARA_REPOSO
        for k, (_, pintar_opcion) in enumerate(opciones):
            pintar_opcion(encendida and k == i)

    def mover(i, encendida):
        if (estado["indice"], estado["encendida"]) == (i, encendida):
            return
        estado.update(indice=i, encendida=encendida)
        pintar()
        menu.update()

    def al_pasar(i):
        def manejador(e):
            # Solo al entrar: la vuelta a la activa la da el menú entero al salir (abajo).
            if e.data in (True, "true"):
                mover(i, True)
        return manejador

    def al_pulsar(ruta):
        def manejador(_):
            router.menu_encendido = True
            router.cambiar_vista(ruta)
        return manejador

    def al_salir_del_menu(e):
        # La vuelta va aquí y no en la salida de cada opción: entre opciones hay 10 px de
        # hueco, y al cruzarlo la píldora arrancaría hacia la activa y se daría la vuelta.
        if e.data not in (True, "true"):
            mover(indice_activo, False)

    # Todo sin auto-update (sin_auto_update, en piezas.py): mover() hace menu.update() y
    # cambiar_vista() su page.update(); si no, cada paso del cursor comparaba la página entera.
    for i, ((opcion, _), (_, _, ruta)) in enumerate(zip(opciones, SECCIONES)):
        opcion.on_hover = sin_auto_update(al_pasar(i))
        opcion.on_click = sin_auto_update(al_pulsar(ruta))

    pintar()
    menu = ft.Container(
        on_hover=sin_auto_update(al_salir_del_menu),
        # Alto fijo: un Stack con todo posicionado no sabe medirse dentro de una Column.
        # Sin recorte (por defecto un Stack recorta): se comería la holgura de los anillos
        # y el zoom de la píldora.
        content=ft.Stack(
            [pildora] + [opcion for opcion, _ in opciones],
            width=ANCHO, height=PASO * (len(SECCIONES) - 1) + ALTO,
            clip_behavior=ft.ClipBehavior.NONE
        )
    )
    return menu


def _crear_opcion(texto, icono, top):
    # Una opción del menú: solo icono y texto, sin fondo (el fondo es la píldora). Mismo
    # padding, fila y tamaños que el botón de antes, así nada se mueve de sitio.
    # Como en los atajos, la fila está escrita dos veces para el relevo (la segunda espera
    # justo debajo, fuera del recorte) y va en blanco dentro de una capa al 54 % que sube al
    # 100 % al encenderse (el color de un ft.Text cambiaría de golpe). Sin ink: el tema oscuro
    # pinta un gris al 25 % al pulsar.
    def fila():
        return ft.Row([
            ft.Icon(icono, color=ft.Colors.WHITE, size=20),
            ft.Text(texto, color=ft.Colors.WHITE, size=14, font_family="CreatoDisplayLight")
        ], tight=True)

    sale = ft.Container(content=fila(), animate_offset=CURVA)
    entra = ft.Container(content=fila(), animate_offset=CURVA)
    rodillo = ft.Container(
        content=ft.Stack([sale, entra]),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        animate_opacity=CURVA
    )
    opcion = ft.Container(
        left=0, top=top, width=ANCHO, height=ALTO, padding=12,
        alignment=ft.Alignment.CENTER_LEFT,
        content=rodillo,
        animate_scale=CURVA
    )

    def pintar(encendida):
        opcion.scale = ZOOM if encendida else 1
        rodillo.opacity = 1 if encendida else 0.54
        sale.offset = ft.Offset(0, -1 if encendida else 0)
        entra.offset = ft.Offset(0, 0 if encendida else 1)

    return opcion, pintar
