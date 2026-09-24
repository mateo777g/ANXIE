import datetime

import flet as ft

# Piezas de diseño que comparten las vistas del panel. Las reglas y el porqué de cada número
# están en DISENO.md.


DIAS = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
         "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]


def fondo_pagina():
    # El fondo de las vistas nuevas: un brillo gris abajo a la derecha sobre negro. De ahí
    # viene la luz de todo el panel (las tarjetas se aclaran hacia esa esquina).
    return ft.RadialGradient(
        center=ft.Alignment(0.95, 0.85),
        radius=1.25,
        colors=["#a5a5a5", "#5c5c5c", "#1a1a1a", "#000000"],
        stops=[0, 0.32, 0.7, 1]
    )


def fecha_vista():
    # La fecha de arriba de cada vista ("JUEVES, 24 DE SEPTIEMBRE").
    hoy = datetime.datetime.now()
    texto = f"{DIAS[hoy.weekday()]}, {hoy.day} DE {MESES[hoy.month - 1]}"
    return ft.Text(texto, color=ft.Colors.WHITE, size=14, font_family="CreatoDisplayLight")


def titulo_vista(texto, tamano=40):
    # El título grande de cada vista ("Buenos días, Miguel", "Crear contenido"). Los
    # generadores lo llevan a 35, su tamaño de siempre (regla 11: nada cambia de tamaño).
    return ft.Text(texto, size=tamano, color=ft.Colors.WHITE, font_family="CreatoDisplay")


def brillo(esquina, radio=1.0):
    # Brillo redondo del borde en una esquina, como el widget del iPhone. Lo usan las
    # tarjetas, los botones de atajos y la píldora del menú, siempre en pareja: arriba a la
    # izquierda y abajo a la derecha. El radio es una fracción del lado corto de la caja.
    return ft.RadialGradient(
        center=esquina,
        radius=radio,
        colors=["#8AFFFFFF", "#2EFFFFFF", "#00FFFFFF"],
        stops=[0, 0.3, 1]
    )


def anillo_brillo(esquina, radio, alto):
    # Solo la línea del borde (1 px, blanca), recortada con el brillo de una esquina:
    # DST_IN deja la línea con la transparencia del degradado.
    # Un ShaderMask solo enmascara lo que cae dentro de su caja. Cuando el botón no cae en
    # píxel entero (Windows al 125 o 150 %, o durante el zoom), el antialias de la línea
    # se sale medio píxel de la caja, se queda sin enmascarar y se ve blanco puro: una
    # línea a todo lo largo de arriba y de abajo y un punto en cada extremo. Por eso la
    # máscara es `holgura` px más grande por cada lado y la línea va dentro con ese margen.
    # El degradado se corrige para que el brillo mida lo mismo (el radio es una fracción
    # del alto de la máscara) y su centro vuelva a la altura de la línea; a lo ancho queda
    # `holgura` px por fuera, porque el ancho del botón cambia con la ventana.
    # Va dentro de un Stack con clip_behavior=NONE, que no recorte la holgura.
    holgura = 2
    alto_mascara = alto + 2 * holgura
    centro = ft.Alignment(esquina.x, esquina.y * (1 - 2 * holgura / alto_mascara))
    return ft.ShaderMask(
        left=-holgura, top=-holgura, right=-holgura, bottom=-holgura,
        shader=brillo(centro, alto / alto_mascara),
        blend_mode=ft.BlendMode.DST_IN,
        content=ft.Container(
            margin=holgura,
            border=ft.Border.all(1, ft.Colors.WHITE), border_radius=radio
        )
    )


def cabecera_tarjeta(titulo, subtitulo):
    # Título y subtítulo de una tarjeta, iguales en todas: el título en mayúsculas.
    return [
        ft.Text(titulo, size=16, color=ft.Colors.WHITE, font_family="CreatoDisplay"),
        ft.Text(subtitulo, color=ft.Colors.WHITE54, size=12, font_family="CreatoDisplayLight"),
        ft.Container(height=15),
    ]


def tarjeta_iphone(contenido, radio=16, padding=25, expand=1, **eventos):
    # El borde brilla en dos esquinas opuestas: un brillo arriba a la izquierda
    # (contenedor de fuera) y otro abajo a la derecha (el de en medio). Las otras dos
    # esquinas quedan sin brillo. `eventos` (on_hover, on_click...) van al contenedor de
    # fuera, para una tarjeta que se pulsa entera.
    # `radio`, `padding` y `expand` son para los paneles de los generadores, que llevan la
    # tarjeta en la medida que ya tenían (regla 11): el borde de 1 px + `padding` deja el
    # contenido donde lo dejaba su borde de 1 + su padding.
    return ft.Container(
        expand=expand,
        border_radius=radio,
        gradient=brillo(ft.Alignment(-1, -1)),
        # Sombra solo hacia abajo, como el widget del iPhone: se encoge tanto como se
        # difumina (spread = -blur) para que no asome arriba ni a los lados, y se baja
        # un poco más que eso para que salga por abajo.
        shadow=ft.BoxShadow(
            blur_radius=14,
            spread_radius=-14,
            color=ft.Colors.BLACK54,
            offset=ft.Offset(0, 16)
        ),
        content=ft.Container(
            expand=True,
            padding=1,
            border_radius=radio,
            gradient=brillo(ft.Alignment(1, 1)),
            content=ft.Container(
                expand=True,
                # Degradado leve como el widget del iPhone: se aclara hacia la esquina inferior derecha
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#222222", "#3a3a3a"]
                ),
                border_radius=radio - 1,
                padding=padding,
                content=contenido
            )
        ),
        **eventos
    )


# La curva, el tiempo y el zoom de "Ver catálogo" de la página web (cubic-bezier(0.22, 1,
# 0.36, 1) es un ease-out quint, 460 ms, 1.05): los de los atajos, la barra y el interruptor.
CURVA = ft.Animation(460, ft.AnimationCurve.EASE_OUT_QUINT)
ZOOM = 1.05


def relevo(fila):
    # El relevo de "Ver catálogo": la fila (icono y texto) está escrita dos veces, apiladas y
    # recortadas; al encenderse, la primera sube y la segunda entra desde abajo. `fila` es una
    # función que devuelve la fila (se llama una vez por copia). Devuelve la capa y la función
    # que la enciende (encender(True/False)); quien la llame hace el update().
    # La segunda copia espera justo debajo, fuera del recorte: el offset es una fracción del
    # alto de la propia fila. Icono y texto van en blanco dentro de una capa al 54 %: en reposo
    # se ven igual que WHITE54, y al encenderse la capa sube al 100 % con una transición suave
    # (el color de un ft.Text cambiaría de golpe).
    sale = ft.Container(content=fila(), offset=ft.Offset(0, 0), animate_offset=CURVA)
    entra = ft.Container(content=fila(), offset=ft.Offset(0, 1), animate_offset=CURVA)
    rodillo = ft.Container(
        content=ft.Stack([sale, entra]),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        opacity=0.54, animate_opacity=CURVA
    )

    def encender(dentro):
        rodillo.opacity = 1 if dentro else 0.54
        sale.offset = ft.Offset(0, -1 if dentro else 0)
        entra.offset = ft.Offset(0, 0 if dentro else 1)

    return rodillo, encender


def etiqueta(icono, texto=""):
    # Qué es un dato, encima de él: icono 20 y texto Light 13, los dos en WHITE54, separación
    # 8 (lo de dentro de un atajo, en reposo). La de los contadores de Inicio ("Cuentas
    # subidas") y la de las carpetas de Ajustes ("Carpeta actual"). Devuelve la fila y su
    # texto, por si hay que cambiarlo después.
    texto = ft.Text(texto, color=ft.Colors.WHITE54, size=13, font_family="CreatoDisplayLight")
    return ft.Row([ft.Icon(icono, color=ft.Colors.WHITE54, size=20), texto], spacing=8), texto


def globo(texto, distancia=32, encima=False):
    # El globo que sale con el cursor encima, con la letra y los colores del panel (el de Flet
    # sale en Roboto). `distancia` va del centro del control al globo: 32 para un botón de 48
    # (debajo, como el de "Eliminar" en Mi biblioteca).
    return ft.Tooltip(
        message=texto,
        text_style=ft.TextStyle(size=12, color=ft.Colors.WHITE, font_family="CreatoDisplayLight"),
        decoration=ft.BoxDecoration(bgcolor="#2a2a2a", border_radius=ft.BorderRadius.all(12)),
        padding=ft.Padding(left=12, top=6, right=12, bottom=6),
        vertical_offset=distancia,
        prefer_below=False if encima else None,
        wait_duration=ft.Duration(milliseconds=500),
    )


def fila_atajo(icono, texto=None):
    # Lo de dentro de un botón de atajo: icono 20 y texto Light 13, separación 8. Sin texto,
    # solo el icono (el botón redondo de "Eliminar" en Mi biblioteca).
    fila = [ft.Icon(icono, color=ft.Colors.WHITE, size=20)]
    if texto:
        fila.append(ft.Text(texto, color=ft.Colors.WHITE, size=13, font_family="CreatoDisplayLight"))
    return ft.Row(fila, spacing=8, tight=True)


def boton_atajo(icono, texto, al_pulsar, ancho=None, alto=48):
    # Botón de atajo que se enciende con su propio cursor y se pulsa solo (Inicio).
    # Apagado (apagar_boton), no se enciende ni se pulsa.
    boton, cara, encender, hundir = boton_atajo_suelto(icono, texto, ancho, alto)
    cara.on_hover = lambda e: boton.disabled or encender(e.data in (True, "true"))
    cara.on_tap_down = lambda _: boton.disabled or hundir()
    cara.on_click = lambda e: boton.disabled or al_pulsar(e)
    return boton


def apagar_boton(boton, apagado):
    # Un botón de atajo apagado: al 40 % (como una tarea bloqueada en Crear contenido) y sin
    # eventos. "Descargar" de los generadores, hasta que hay una imagen generada.
    boton.disabled = apagado
    boton.opacity = 0.4 if apagado else 1


def boton_atajo_suelto(icono, texto, ancho=None, alto=48):
    # El botón de atajo sin eventos: devuelve el botón, su cara y las funciones que lo
    # encienden (encender(True/False)) y lo hunden (hundir()), para que otro control (una
    # tarjeta entera, por ejemplo) decida cuándo.
    # Sin `ancho` ocupa todo el sitio que le dejen (expand); con ancho = alto (48) y sin
    # texto es un círculo: los mismos anillos y la misma cara.
    # `alto` es 48, el de un atajo; los generadores lo piden en la medida de sus botones de
    # siempre (45 los de abajo, 40 los redondos), por la regla 11.
    # Con el mismo brillo de esquinas que la tarjeta.
    # Aquí no sirve el truco de la tarjeta (contenedores anidados con padding 1): el
    # botón es translúcido y el brillo se vería por toda la cara. Por eso los dos
    # anillos van debajo y la cara encima; la cara, que es la que recibe el clic y el
    # efecto al pulsar, deja ver la línea del borde a través de su blanco al 5 %.
    # Forma de píldora: el radio es la mitad del alto, así los extremos son semicírculos.
    radio = alto / 2
    # Al pasar el cursor, el mismo relevo que "Ver catálogo" de la página web (relevo()):
    # el botón crece a 1.05, se enciende (cara al 14 %, icono y texto a blanco puro) y su
    # contenido sube y deja entrar desde abajo una copia idéntica.
    # Al pulsarlo se hunde a 0.97, también como en la web, y la cara sube al 20 %.
    # Sin ink de Flet a propósito: el tema oscuro pinta al pulsar un gris al 25 % que
    # tapaba el botón entero, y el contenedor no deja cambiar ese color.
    cara_reposo, cara_encendida, cara_pulsada = "#0DFFFFFF", "#24FFFFFF", "#33FFFFFF"

    rodillo, encender_relevo = relevo(lambda: fila_atajo(icono, texto))
    cara = ft.Container(
        left=0, top=0, right=0, bottom=0,
        alignment=ft.Alignment.CENTER,
        content=rodillo,
        bgcolor=cara_reposo, border_radius=radio,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    )
    boton = ft.Container(
        height=alto, expand=ancho is None, width=ancho,
        scale=1, animate_scale=CURVA,
        # Sin recorte: las máscaras de los anillos sobresalen 2 px de la caja a propósito.
        content=ft.Stack([
            anillo_brillo(ft.Alignment(-1, -1), radio, alto),
            anillo_brillo(ft.Alignment(1, 1), radio, alto),
            cara
        ], clip_behavior=ft.ClipBehavior.NONE)
    )

    def encender(dentro):
        boton.scale = ZOOM if dentro else 1
        cara.bgcolor = cara_encendida if dentro else cara_reposo
        encender_relevo(dentro)
        boton.update()

    def hundir():
        boton.scale = 0.97
        cara.bgcolor = cara_pulsada
        boton.update()

    return boton, cara, encender, hundir


def interruptor(opciones, elegida, al_cambiar):
    # Interruptor de una sola píldora, como un switch (Mi biblioteca: Cuentas / Recibos).
    # opciones = [(texto, icono), ...]; elegida = índice de la opción marcada al empezar;
    # al_cambiar(i) se llama cuando se pulsa otra opción.
    # La pista es un botón de atajo sin contenido (cara al 5 % y brillo en dos esquinas) y
    # dentro va otra píldora, el botón, bajo la opción elegida. El botón hace lo mismo que la
    # píldora de la barra lateral: con el cursor encima de una opción se desliza hasta ella y
    # se enciende (cara al 14 %, texto en blanco y el relevo); al salir el cursor de la pista
    # vuelve apagado a la elegida. El zoom de los atajos lo hace el interruptor entero (1.05
    # con el cursor encima, 0.97 al pulsar): si creciera solo el botón, sus extremos se
    # comerían los 4 px que lo separan del borde de la pista y los dos bordes se pegarían.
    # Al pulsar, esa opción pasa a ser la elegida y se llama a al_cambiar.
    alto = 48                    # el de un botón de atajo
    hueco = 4                    # entre el borde de la pista y el botón
    alto_boton = alto - 2 * hueco
    ancho = 124                  # cada opción: caben icono y texto con aire a los lados
    radio, radio_boton = alto // 2, alto_boton // 2
    cara_reposo, cara_encendida, cara_pulsada = "#0DFFFFFF", "#24FFFFFF", "#33FFFFFF"
    estado = {"elegida": elegida, "indice": elegida, "encendida": False, "pulsada": False}

    cara = ft.Container(
        left=0, top=0, right=0, bottom=0, border_radius=radio_boton,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    )
    # El botón se mueve cambiando su left, como la píldora de la barra su top.
    boton = ft.Container(
        top=hueco, width=ancho, height=alto_boton,
        animate_position=CURVA,
        # Sin recorte: las máscaras de los anillos sobresalen 2 px de la caja a propósito.
        content=ft.Stack([
            anillo_brillo(ft.Alignment(-1, -1), radio_boton, alto_boton),
            anillo_brillo(ft.Alignment(1, 1), radio_boton, alto_boton),
            cara
        ], clip_behavior=ft.ClipBehavior.NONE)
    )

    # Las opciones van encima del botón, cada una en su sitio fijo: son las que reciben el
    # cursor y el clic. Solo icono y texto, sin fondo (el fondo es el botón).
    etiquetas = []
    for i, (texto, icono) in enumerate(opciones):
        rodillo, encender = relevo(lambda icono=icono, texto=texto: fila_atajo(icono, texto))
        etiqueta = ft.Container(
            left=hueco + ancho * i, top=hueco, width=ancho, height=alto_boton,
            alignment=ft.Alignment.CENTER, content=rodillo
        )
        etiquetas.append((etiqueta, encender))

    def pintar():
        i, encendida, pulsada = estado["indice"], estado["encendida"], estado["pulsada"]
        pista.scale = 0.97 if pulsada else (ZOOM if encendida else 1)
        boton.left = hueco + ancho * i
        cara.bgcolor = cara_pulsada if pulsada else (cara_encendida if encendida else cara_reposo)
        for k, (_, encender) in enumerate(etiquetas):
            encender(encendida and k == i)

    def mover(i, encendida):
        if (estado["indice"], estado["encendida"], estado["pulsada"]) == (i, encendida, False):
            return
        estado.update(indice=i, encendida=encendida, pulsada=False)
        pintar()
        pista.update()

    def al_pasar(i):
        def manejador(e):
            # Solo al entrar: la vuelta a la elegida la da la pista entera al salir (abajo),
            # como en la barra: al cruzar de una opción a la otra, el botón no da la vuelta.
            if e.data in (True, "true"):
                mover(i, True)
        return manejador

    def al_hundir(i):
        def manejador(_):
            estado.update(indice=i, encendida=True, pulsada=True)
            pintar()
            pista.update()
        return manejador

    def al_pulsar(i):
        def manejador(_):
            cambia = i != estado["elegida"]
            estado.update(elegida=i, indice=i, encendida=True, pulsada=False)
            pintar()
            pista.update()
            if cambia:
                al_cambiar(i)
        return manejador

    def al_salir(e):
        if e.data not in (True, "true"):
            mover(estado["elegida"], False)

    for i, (etiqueta, _) in enumerate(etiquetas):
        etiqueta.on_hover = al_pasar(i)
        etiqueta.on_tap_down = al_hundir(i)
        etiqueta.on_click = al_pulsar(i)

    pista = ft.Container(
        width=ancho * len(opciones) + 2 * hueco, height=alto,
        animate_scale=CURVA,
        on_hover=al_salir,
        content=ft.Stack([
            anillo_brillo(ft.Alignment(-1, -1), radio, alto),
            anillo_brillo(ft.Alignment(1, 1), radio, alto),
            ft.Container(left=0, top=0, right=0, bottom=0, bgcolor=cara_reposo, border_radius=radio),
            boton,
            *[etiqueta for etiqueta, _ in etiquetas]
        ], clip_behavior=ft.ClipBehavior.NONE)
    )
    pintar()
    return pista


def aviso(page, texto, abajo=40):
    # Los avisos de una vista ("Eliminada.", "¡Exportada con éxito!"): una píldora flotante
    # abajo, con la letra y los colores del panel, centrada sobre el contenido (a la derecha
    # de la barra lateral, que mide 250) y no sobre la ventana entera.
    # `abajo` es lo que queda entre la píldora (49 de alto) y el borde de abajo: 40, el margen
    # de las vistas. En los generadores la tarjeta de la derecha baja hasta ese margen y a 40
    # la píldora tapaba medio botón "Generar"; allí va a 9, centrada en los 66 px que quedan
    # entre los botones y el borde (donde salía el aviso de antes, de lado a lado).
    ancho = 320
    lado = max(16, ((page.width or 1264) - 250 - ancho) / 2)
    page.overlay.append(ft.SnackBar(
        ft.Row([ft.Text(texto, color=ft.Colors.WHITE, size=13, font_family="CreatoDisplayLight")],
               alignment=ft.MainAxisAlignment.CENTER),
        open=True,
        behavior=ft.SnackBarBehavior.FLOATING,
        bgcolor="#2a2a2a",
        shape=ft.RoundedRectangleBorder(radius=24),
        margin=ft.Margin(left=250 + lado, right=lado, bottom=abajo),
        padding=ft.Padding(left=20, top=15, right=20, bottom=15),
    ))
    page.update()


# Los campos de los generadores (rutas, textos, nombre de la descarga). Un pozo: más oscuro que
# la tarjeta en la que va, en negro translúcido (regla 7: igual de visible en la esquina oscura
# y en la clara), con la línea del borde en blanco al 12 % (el tono de la raya de la barra) y al
# 54 % cuando se escribe en él (el blanco del brillo de las esquinas), siempre de 1 px (Flutter
# la pone de 2 al escribir: pesaba más que todas las líneas del panel). La letra, la del panel.
# El tamaño, el de siempre (regla 11): texto a 12 y el relleno que ya tenía cada campo.
FONDO_CAMPO = "#33000000"
BORDE_CAMPO = "#1FFFFFFF"


def campo(etiqueta=None, pista=None, valor="", solo_lectura=False, relleno=None, expand=True):
    luz = ft.TextStyle(font_family="CreatoDisplayLight", color=ft.Colors.WHITE54)
    return ft.TextField(
        label=etiqueta, hint_text=pista, value=valor, read_only=solo_lectura,
        expand=expand, content_padding=relleno, text_size=12,
        color=ft.Colors.WHITE,
        text_style=ft.TextStyle(font_family="CreatoDisplayLight"),
        label_style=luz, hint_style=luz,
        bgcolor=FONDO_CAMPO, border_color=BORDE_CAMPO,
        focused_border_color=ft.Colors.WHITE54, focused_border_width=1, border_radius=10,
        cursor_color=ft.Colors.WHITE, selection_color=ft.Colors.WHITE24,
    )


def opcion_radio(valor):
    # Una opción de un RadioGroup (NFA / FA de los recibos): el círculo en blanco puro la
    # elegida y al 54 % las demás, y el texto en Light blanco. Sin rojo.
    return ft.Radio(
        value=valor, label=valor,
        label_style=ft.TextStyle(font_family="CreatoDisplayLight", color=ft.Colors.WHITE),
        fill_color={ft.ControlState.SELECTED: ft.Colors.WHITE, ft.ControlState.DEFAULT: ft.Colors.WHITE54},
        overlay_color={ft.ControlState.HOVERED: "#24FFFFFF", ft.ControlState.PRESSED: "#33FFFFFF",
                       ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT},
    )


def hueco_imagen(contenido):
    # El hueco de la vista previa de los generadores, donde sale la imagen generada: un pozo
    # como los campos, radio 10, con su borde de 2 px de siempre en el tono de la raya (el de
    # arriba era rojo), para que la imagen salga del mismo tamaño que antes. Ocupa todo el alto
    # que le quede en su columna y todo el ancho (width=9999 lo recorta la columna).
    return ft.Container(
        expand=True, width=9999,
        bgcolor=FONDO_CAMPO, border_radius=10, border=ft.Border.all(2, BORDE_CAMPO),
        content=contenido
    )
