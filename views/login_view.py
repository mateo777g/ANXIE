import asyncio

import flet as ft

from models import sesion
from models.entorno import leer
from views.piezas import (tarjeta_iphone, boton_atajo,
                          apagar_boton, campo, aviso, sin_auto_update)
from views.tema import C

# --- ENTRAR ---
# La pantalla de entrada del panel (fase 2, 24/09): lo que se ve al abrirlo si no hay una sesión
# recordada en esta PC. Lo decidió el dueño: la contraseña "al inicio del panel", no dentro de
# Cuentas, y que se recuerde (models/sesion.py). Con una sesión guardada, el panel abre directo en
# Inicio y esta pantalla no sale.
# Ocupa la ventana entera, sin barra lateral (como la de Taku Monky), en dos mitades del mismo alto
# (26/09, del componente GrainGradient que mandó el dueño): a la izquierda una tarjeta de Inicio
# con la contraseña y a la derecha las manchas con grano, la frase y la etiqueta de la marca. Solo
# la contraseña: el correo es fijo (ADMIN_EMAIL del .env), como en lilshop. Sustituye al login
# viejo del PIN "1234", que no se abría desde ninguna parte. El diseño, en DISENO.md
# ("Distribución de Entrar").

# Todo a 48 del borde de su mitad, 56 arriba: el título de la tarjeta y la frase de las manchas
# empiezan a la misma altura y a la misma distancia de su borde.
MARGEN, MARGEN_ARRIBA = 48, 56
RADIO = 16                    # el de una tarjeta de Inicio, para las dos mitades


def encabezado(titulo, subtitulo):
    # El título grande de la tarjeta, del tamaño de la frase de las manchas (56, como ella, y a su
    # misma altura: las dos líneas de arriba quedan parejas), y debajo su descripción, como
    # "Create an account" en el componente.
    return [
        ft.Text(titulo, size=56, color=C.texto, font_family="LetraTitulo",
                style=ft.TextStyle(height=1.0)),
        ft.Container(height=14),
        ft.Text(subtitulo, size=22, color=C.texto_suave, font_family="LetraTexto"),
    ]


class LoginView(ft.Container):
    def __init__(self, router, motivo=None, destino="home"):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.motivo = motivo          # un aviso al llegar ("Tu sesión se cerró…"), si lo hay
        self.destino = destino        # a dónde ir al entrar: Inicio, o la vista de donde se vino
        self.expand = True
        # Negro liso, sin fondo_pagina(): la única vista sin el degradado (26/09, excepción que
        # pidió el dueño para que solo brillen las manchas). En el tema claro, gris muy claro.
        self.bgcolor = C.fondo_entrar
        self.padding = 12

        configurado = all(leer(clave) for clave in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "ADMIN_EMAIL"))
        if configurado:
            # El encabezado arriba, el campo y "Entrar" (blanco, lo pidió el dueño) debajo, del
            # ancho de la tarjeta. Enter y "Entrar" van sin auto-update: _entrar hace sus update()
            # (el botón, el campo, el aviso o cambiar_vista).
            self.campo_contrasena = campo(pista="Contraseña", icono=ft.Icons.LOCK_OUTLINE,
                                          contrasena=True, tamano=15, autofoco=True,
                                          relleno=ft.Padding(left=12, top=18, right=12, bottom=18),
                                          al_enviar=sin_auto_update(
                                              lambda _: self.page_ref.run_task(self._entrar)))
            self.boton_entrar = boton_atajo(ft.Icons.LOGIN, "Entrar",
                                            lambda _: self.page_ref.run_task(self._entrar), claro=True,
                                            alto=51, radio=10)   # la forma del campo: 51 de alto, radio 10
            partes = [
                *encabezado("Inicia sesión", "Escribe la contraseña de la tienda para entrar al panel."),
                ft.Container(height=48),
                ft.Row([self.campo_contrasena]),
                ft.Container(height=16),
                ft.Row([self.boton_entrar]),
            ]
        else:
            # Sin .env no hay a qué tienda entrar: se dice qué falta y dónde va.
            partes = encabezado(
                "Falta el archivo .env",
                "Sin él, el panel no sabe a qué tienda conectarse. Va en la carpeta del panel, "
                "junto a main.py (o junto al .exe).")
        # La tarjeta ocupa toda su mitad, del mismo alto que las manchas. El borde de 1 px más
        # este padding dejan el texto a 48 / 56 del borde, como la frase.
        tarjeta = tarjeta_iphone(
            ft.Column(partes, spacing=0), radio=RADIO, expand=94,
            # Más oscura que las de Inicio (lo pidió el dueño): del #0a0a0a de su muestra a un gris
            # algo más claro abajo a la derecha, el mismo sentido del degradado.
            # En el tema claro, al revés: más blanca que las de Inicio.
            colores=C.tarjeta_entrar,
            padding=ft.Padding(left=MARGEN - 1, top=MARGEN_ARRIBA - 1, right=MARGEN - 1, bottom=MARGEN - 1))

        # A la derecha, las dos manchas azules con grano (26/09, lo pidió el dueño a partir de un
        # GrainGradient de React; primero la quiso a la izquierda y luego a la derecha, como en el
        # componente): un WebP animado que pinta .claude/grano-login.py; Flutter lo reproduce solo.
        grano = ft.Container(
            expand=106, border_radius=RADIO, bgcolor="#000000", border=ft.Border.all(1, "#1FFFFFFF"),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack([
                ft.Image(src="assets/login-grano.webp", fit=ft.BoxFit.COVER,
                         width=float("inf"), height=float("inf")),
                # La frase, arriba a la izquierda como en el componente, en la letra de los títulos.
                ft.Container(left=MARGEN, top=MARGEN_ARRIBA, content=ft.Text(
                    "Moderniza\nTu Negocio", size=56, color=ft.Colors.WHITE,
                    font_family="LetraTitulo", style=ft.TextStyle(height=1.0))),
                ft.Container(left=MARGEN, right=MARGEN, bottom=MARGEN, content=etiqueta_marca()),
            ]))
        self.content = ft.Row([tarjeta, grano], spacing=12,
                              vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def did_mount(self):
        if self.motivo:
            aviso(self.page_ref, self.motivo, barra=0)

    async def _entrar(self):
        # Tal cual se escribió (una contraseña puede llevar espacios); vacía, ni se intenta.
        contrasena = self.campo_contrasena.value or ""
        if not contrasena.strip():
            aviso(self.page_ref, "Escribe la contraseña.", barra=0)
            await self.campo_contrasena.focus()
            return
        apagar_boton(self.boton_entrar, True)
        self.boton_entrar.update()
        try:
            await asyncio.to_thread(sesion.iniciar_sesion, contrasena)
        except Exception as e:
            print(f"[entrar] no se pudo: {type(e).__name__}: {e}")
            apagar_boton(self.boton_entrar, False)
            self.campo_contrasena.value = ""
            self.boton_entrar.update()
            self.campo_contrasena.update()
            aviso(self.page_ref, mensaje_error(e, "No se pudo entrar"), barra=0)
            # El campo, vacío y con el foco otra vez: se vuelve a escribir sin tener que pulsarlo.
            await self.campo_contrasena.focus()
            return
        self.router.cambiar_vista(self.destino)


def etiqueta_marca():
    # La etiqueta de abajo del panel de las manchas (26/09, como el "Download the windows app" del
    # componente): la cara de un botón de atajo, translúcida, con un borde parejo y la mancha
    # desenfocada detrás; dentro, el logo en blanco (assets/fragmentless-blanco.png, el trazo del
    # logo sin el fondo azul) y "Fragmentless · Panel de escritorio", los dos al 85 %. Larga, de
    # lado a lado del panel (a 48 de cada borde), con el texto a la izquierda y aire a la derecha,
    # como en el componente. No se pulsa: es una etiqueta.
    alto, radio = 48, 10   # rectángulo de esquinas suaves, como en el componente (rounded-[10px]), no píldora
    fila = ft.Row([
        ft.Image(src="assets/fragmentless-blanco.png", height=22, fit=ft.BoxFit.CONTAIN),
        ft.Text("Fragmentless · Panel de escritorio", size=15, color=ft.Colors.WHITE, font_family="LetraTitulo"),
    ], spacing=10, tight=True, opacity=0.85)
    # El borde, entero y parejo (el dueño no lo quiso con el brillo solo en dos esquinas, como
    # los atajos): 1 px blanco al 25 %, el border-white/25 del componente.
    return ft.Container(height=alto, border_radius=radio, bgcolor="#0DFFFFFF", blur=ft.Blur(8, 8),
                        border=ft.Border.all(1, "#40FFFFFF"), alignment=ft.Alignment.CENTER_LEFT,
                        padding=ft.Padding(left=18, top=0, right=22, bottom=0), content=fila)


def mensaje_error(error, que):
    # El aviso para un error de Supabase o de la red, en español (lo usa también Cuentas).
    import httpx
    from models.supabase_client import FaltaConfiguracion
    from supabase_auth.errors import AuthRetryableError
    if getattr(error, "code", None) == "invalid_credentials":
        return "Contraseña incorrecta."
    if isinstance(error, (httpx.RequestError, OSError, AuthRetryableError)):
        return f"{que}: sin conexión. Revisa tu internet."
    if isinstance(error, FaltaConfiguracion):
        return f"{que}: falta el archivo .env del panel."
    if getattr(error, "code", None) == "over_request_rate_limit":
        return f"{que}: demasiados intentos. Espera unos minutos."
    return f"{que}: {getattr(error, 'message', None) or error}"
