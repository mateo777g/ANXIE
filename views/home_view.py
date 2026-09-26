import flet as ft
import os

from models import perfil
from views.barra_lateral import crear_barra_lateral
from views.piezas import (fondo_pagina, fecha_vista, titulo_vista, cabecera_tarjeta,
                          tarjeta_iphone, boton_atajo, etiqueta)

class HomeView(ft.Container):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.page_ref = router.page
        self.expand = True
        self.bgcolor = "#0e0e0e"
        self.gradient = fondo_pagina()
        self.padding = 0

        # --- CONTADORES ---
        # Sin icono (el dueño, 26/09: los atajos de al lado ya llevan los suyos y tantos iconos
        # saturaban la vista); el texto de la etiqueta ya dice cuál es cuál.
        contador_cuentas, self.numero_cuentas, self.etiqueta_cuentas = self._crear_contador()
        contador_recibos, self.numero_recibos, self.etiqueta_recibos = self._crear_contador()

        # --- BARRA LATERAL (SIDEBAR) ---
        sidebar = crear_barra_lateral(self.router, "home")

        # El nombre del saludo: como eligió que lo llamen en su Perfil (models/perfil.py). Al
        # guardarlo, la ventana Perfil lo cambia aquí también (pintores_perfil).
        self.saludo_nombre = titulo_vista(perfil.como_llamarte())
        self.router.pintores_perfil["saludo"] = self._pintar_saludo

        # --- CONTENIDO PRINCIPAL ---
        main_content = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column([
                # Fecha
                fecha_vista(),
                
                # Saludo
                ft.Row([titulo_vista("Buenos días,"), self.saludo_nombre], spacing=10),
                
                ft.Container(height=25), # Más separación del saludo para que respire
                
                # --- FILA DE TARJETAS ---
                # Las dos tarjetas empiezan arriba (sin centrar) y con la misma cabecera, así
                # títulos, subtítulos y contenido quedan a la misma altura en las dos. Centrado,
                # la tarjeta con menos contenido bajaba su título.
                ft.Row([
                    # Bloque 1: ¿Qué hacemos hoy?
                    tarjeta_iphone(ft.Column([
                            *cabecera_tarjeta("¿QUÉ HACEMOS HOY?", "Atajos a las tareas que más usas."),

                            # PRIMERA FILA DE BOTONES (Los Originales)
                            ft.Row([
                                self._atajo(ft.Icons.IMAGE, "Imagen Cuentas", "generador_miniaturas"),
                                self._atajo(ft.Icons.RECEIPT_LONG, "Imagen Recibos", "recibo")
                            ], spacing=12),

                            # SEGUNDA FILA: las cuentas de la tienda (el dueño, 26/09; antes
                            # Cuenta Pequeña y Recibo Pequeño, que siguen en Crear contenido).
                            # "Agregar Cuenta" lleva a Cuentas con la ventana de Agregar
                            # abierta; "Administrar Cuentas", a Cuentas tal cual.
                            ft.Row([
                                boton_atajo(ft.Icons.INVENTORY_OUTLINED, "Agregar Cuenta",
                                            lambda _: self._agregar_cuenta()),
                                self._atajo(ft.Icons.VIEW_LIST_OUTLINED, "Administrar Cuentas", "cuentas")
                            ], spacing=12)

                        ])),

                    # Bloque 2: Contenido Generado (Vuelve a ser UN SOLO BLOQUE)
                    tarjeta_iphone(ft.Column([
                            *cabecera_tarjeta("CONTENIDO GENERADO", "Estadísticas de tus cuentas actuales."),

                            # Los dos contadores en dos columnas, como los botones de al lado
                            # (misma separación): el segundo empieza donde "Imagen Recibos".
                            ft.Row([contador_cuentas, contador_recibos], spacing=12)

                        ]))
                ], 
                height=250, 
                vertical_alignment=ft.CrossAxisAlignment.STRETCH
                )
            ])
        )

        self.content = ft.Row([sidebar, main_content], expand=True, spacing=0)

    def _pintar_saludo(self):
        # Solo si Inicio sigue en pantalla: si no, la próxima vez que se abra ya lo lee nuevo.
        if self.saludo_nombre.page is None:
            return
        self.saludo_nombre.value = perfil.como_llamarte()
        self.saludo_nombre.update()

    # --- MÉTODO DE LECTURA DE BIBLIOTECA HISTÓRICA ---
    def did_mount(self):
        self.cargar_total_biblioteca()

    def cargar_total_biblioteca(self):
        carpeta_cuentas = os.path.join("biblioteca", "cuentas")
        carpeta_recibos = os.path.join("biblioteca", "recibos")
        
        total_cuentas = 0
        total_recibos = 0
        
        if os.path.exists(carpeta_cuentas):
            archivos_c = [f for f in os.listdir(carpeta_cuentas) if f.endswith(('.png', '.jpg', '.jpeg'))]
            total_cuentas = len(archivos_c)
            
        if os.path.exists(carpeta_recibos):
            archivos_r = [f for f in os.listdir(carpeta_recibos) if f.endswith(('.png', '.jpg', '.jpeg'))]
            total_recibos = len(archivos_r)
        
        self._pintar_contadores(total_cuentas, total_recibos)

    def _pintar_contadores(self, total_cuentas, total_recibos):
        self.numero_cuentas.value = str(total_cuentas)
        self.numero_recibos.value = str(total_recibos)
        self.etiqueta_cuentas.value = "Cuenta subida" if total_cuentas == 1 else "Cuentas subidas"
        self.etiqueta_recibos.value = "Cuenta vendida" if total_recibos == 1 else "Cuentas vendidas"
        self.update()

    def _crear_contador(self):
        # Contador de "CONTENIDO GENERADO", hecho sobre el reloj del iPhone: arriba qué se
        # cuenta (el texto de un botón de atajo, sin icono) y debajo el número en grande,
        # en Coolvetica y en el gris de las cifras del reloj. Ocupa la misma franja que los
        # botones de al lado: la etiqueta arranca a la altura de la primera fila y la línea
        # base del número cae donde acaba la segunda.
        tam = 116
        franja = 48 + 10 + 48   # dos filas de botones y su separación
        # La caja de texto de Coolvetica es mucho más alta que sus cifras (0.667 del tamaño):
        # sobra aire arriba y abajo. Por eso el número va suelto en un Stack de alto fijo,
        # sin recorte, y se baja lo que su caja mide por debajo de la línea base, así la
        # base queda justo en el borde de abajo del Stack. Ese 0.348 del tamaño está medido
        # en el panel, igual en el de escritorio y en el web (no es el 0.233 que dice el
        # archivo de la fuente: Flutter le suma parte del interlineado).
        numero = ft.Text("0", color="#909090", size=tam, font_family="Coolvetica",
                         left=0, bottom=-round(tam * 0.348))
        fila_etiqueta, texto_etiqueta = etiqueta(None)
        contador = ft.Container(expand=1, content=ft.Column([
            fila_etiqueta,
            ft.Stack([numero], height=franja - 20, clip_behavior=ft.ClipBehavior.NONE)
        ], spacing=0))
        return contador, numero, texto_etiqueta

    def _agregar_cuenta(self):
        # Cuentas la mira al crearse (y la borra): abre Agregar en cuanto tiene las cuentas.
        self.router.abrir_agregar_cuenta = True
        self.router.cambiar_vista("cuentas")

    def _atajo(self, icono, texto, ruta):
        # Botón de la tarjeta de atajos (views/piezas.py): lleva a su vista.
        return boton_atajo(icono, texto, lambda _: self.router.cambiar_vista(ruta))
