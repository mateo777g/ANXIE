import asyncio

import flet as ft

from models import sesion
from models.entorno import leer
from views.barra_lateral import marca
from views.piezas import (fondo_pagina, cabecera_tarjeta, tarjeta_iphone, boton_atajo,
                          apagar_boton, campo, aviso, sin_auto_update)

# --- ENTRAR ---
# La pantalla de entrada del panel (fase 2, 24/09): lo que se ve al abrirlo si no hay una sesión
# recordada en esta PC. Lo decidió el dueño: la contraseña "al inicio del panel", no dentro de
# Cuentas, y que se recuerde (models/sesion.py). Con una sesión guardada, el panel abre directo en
# Inicio y esta pantalla no sale.
# Ocupa la ventana entera, sin barra lateral (como la de Taku Monky): el logo y la marca de la
# barra, y debajo una tarjeta de Inicio con la contraseña. Solo la contraseña: el correo es fijo
# (ADMIN_EMAIL del .env), como en lilshop. Sustituye al login viejo del PIN "1234", que no se
# abría desde ninguna parte. El diseño, en DISENO.md ("Distribución de Entrar").

# La tarjeta mide lo que una de Inicio en la ventana del dueño: (1264 − 250 − 80 − 10) / 2.
ANCHO_TARJETA = 462
ALTO_TARJETA = 250


class LoginView(ft.Container):
    def __init__(self, router, motivo=None, destino="home"):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.motivo = motivo          # un aviso al llegar ("Tu sesión se cerró…"), si lo hay
        self.destino = destino        # a dónde ir al entrar: Inicio, o la vista de donde se vino
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.alignment = ft.Alignment.CENTER

        configurado = all(leer(clave) for clave in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "ADMIN_EMAIL"))
        if configurado:
            # Como la tarjeta vacía de Mi biblioteca: la cabecera arriba, el campo en el sitio de
            # la primera fila de atajos de Inicio y "Entrar" en el de la segunda.
            # Enter y "Entrar" van sin auto-update: _entrar hace sus update() (el botón, el campo,
            # el aviso o cambiar_vista).
            self.campo_contrasena = campo(pista="Contraseña", icono=ft.Icons.LOCK_OUTLINE,
                                          contrasena=True, tamano=13, autofoco=True,
                                          al_enviar=sin_auto_update(
                                              lambda _: self.page_ref.run_task(self._entrar)))
            self.boton_entrar = boton_atajo(ft.Icons.LOGIN, "Entrar",
                                            lambda _: self.page_ref.run_task(self._entrar))
            partes = [
                *cabecera_tarjeta("INICIA SESIÓN", "Escribe la contraseña de la tienda para entrar al panel."),
                ft.Row([self.campo_contrasena]),
                ft.Container(expand=True, alignment=ft.Alignment.BOTTOM_LEFT,
                             content=ft.Row([self.boton_entrar])),
            ]
        else:
            # Sin .env no hay a qué tienda entrar: se dice qué falta y dónde va.
            partes = cabecera_tarjeta(
                "FALTA EL ARCHIVO .ENV",
                "Sin él, el panel no sabe a qué tienda conectarse. Va en la carpeta del panel, "
                "junto a main.py (o junto al .exe).")
        tarjeta = tarjeta_iphone(ft.Container(padding=ft.Padding(bottom=7),
                                              content=ft.Column(partes, spacing=10)),
                                 expand=None)
        tarjeta.width, tarjeta.height = ANCHO_TARJETA, ALTO_TARJETA

        # La marca, alineada al borde izquierdo de la tarjeta (a 25, donde empieza su texto), y
        # 30 de aire hasta ella.
        self.content = ft.Column([
            ft.Container(width=ANCHO_TARJETA, padding=ft.Padding(left=25), content=marca()),
            ft.Container(height=30),
            tarjeta,
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

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
