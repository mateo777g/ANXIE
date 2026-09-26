import flet as ft
from models import sesion
from views.home_view import HomeView
from views.image1_view import Image1View
from views.contenido_view import ContenidoView
from views.ajustes_view import AjustesView
from views.biblioteca_view import BibliotecaView
from views.cuentas_view import CuentasView
from views.login_view import LoginView
from views.recibo_view import ReciboView
from views.piezas import sin_auto_update

# 🔥 IMPORTAMOS TUS NUEVOS ARCHIVOS RÉPLICA AQUÍ 🔥
from views.imgmini_view import CuentaPequenaView 
from views.recibomini_view import ReciboPequenoView

class MainController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Anxie Store - Panel"
        self.page.theme_mode = "dark"
        self.page.padding = 0 
        # Creato Display, la letra del diseño nuevo (ver DISENO.md). Se registra aquí, una sola
        # vez, porque la barra lateral la usa en todas las vistas.
        fuentes = dict(getattr(self.page, "fonts", {}) or {})
        fuentes["CreatoDisplay"] = "assets/CreatoDisplay-Regular.otf"
        fuentes["CreatoDisplayLight"] = "assets/CreatoDisplay-Light.otf"
        # Coolvetica (condensada), solo para los números de los contadores de Inicio.
        fuentes["Coolvetica"] = "assets/Coolvetica Rg Cram.otf"
        self.page.fonts = fuentes
        
        # Eventos de la ventana que llegan aunque nadie los escuche (el tema de Windows, cuando la
        # ventana gana o pierde el foco...). Sin manejador, Flet hace igual su auto-update, que
        # compara la página entera: con Mi biblioteca llena, más de 1 s por evento (medido el
        # 25/09). Con un manejador vacío sin auto-update (regla 12 de DISENO.md), nada.
        nada = sin_auto_update(lambda e: None)
        self.page.on_platform_brightness_change = nada
        self.page.on_app_lifecycle_state_change = nada
        self.page.on_locale_change = nada
        self.page.on_media_change = nada

        self.content_container = ft.Container(expand=True)
        self.page.add(self.content_container)

        # Se entra al abrir el panel (fase 2, lo decidió el dueño el 24/09). Con una sesión
        # recordada en esta PC, directo a Inicio (sin red: los generadores no la necesitan; la
        # sesión se comprueba cuando algo la usa, en Cuentas). Si no, la pantalla de entrar.
        self.cambiar_vista("home" if sesion.hay_sesion_guardada() else "login")

    def mostrar_login(self, motivo=None, destino="home"):
        # La pantalla de entrar, con un aviso si se llega a ella porque la sesión se cerró, y
        # la vista a la que volver al entrar (Cuentas, si se venía de ahí).
        self._poner_vista(LoginView(self, motivo, destino))

    def _poner_vista(self, vista):
        # Cambia la vista en DOS update(): primero entra la nueva, en un contenedor suyo junto al
        # de la vieja, que se esconde (lo que se ve cambia ya aquí); luego se quita la vieja, que
        # ya no se veía. En un solo update() (quitar la vieja y poner la nueva a la vez), Flet
        # busca cada control quitado entre los puestos y cada puesto entre los quitados: salir de
        # Mi biblioteca con 200 + 200 imágenes (16 000 controles) contra los ~360 de Inicio
        # tardaba 1.5 s, casi todo en eso (medido el 26/09, 2.3d). Por separado, ~20 ms.
        # Lo mismo que hace Mi biblioteca al rehacer una pestaña (añadir y luego quitar).
        vieja = self.content_container
        self.content_container = ft.Container(expand=True, content=vista)
        vieja.visible = False
        self.page.controls.append(self.content_container)
        self.page.update()
        self.page.controls.remove(vieja)
        self.page.update()

    def cambiar_vista(self, vista: str):
        if vista == "home":
            vista_actual = HomeView(self)
            
        elif vista == "generador_miniaturas": 
            vista_actual = Image1View(self)
            
        elif vista == "contenido": 
            vista_actual = ContenidoView(self)
        
        elif vista == "ajustes":
            vista_actual = AjustesView(self)
            
        elif vista == "biblioteca":
            vista_actual = BibliotecaView(self)

        elif vista == "cuentas":
            vista_actual = CuentasView(self)

        elif vista == "login":
            vista_actual = LoginView(self)
            
        elif vista == "recibo": 
            vista_actual = ReciboView(self)

        # 🔥 AGREGAMOS TUS DOS NUEVAS RUTAS AQUÍ 🔥
        elif vista == "cuenta_pequena":
            vista_actual = CuentaPequenaView(self)

        elif vista == "recibo_pequeno":
            vista_actual = ReciboPequenoView(self)
            
        else:
            vista_actual = HomeView(self)
            
        self._poner_vista(vista_actual)