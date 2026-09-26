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
from views import tema

# 🔥 IMPORTAMOS TUS NUEVOS ARCHIVOS RÉPLICA AQUÍ 🔥
from views.imgmini_view import CuentaPequenaView 
from views.recibomini_view import ReciboPequenoView

class MainController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Anxie Store - Panel"
        # El tema que quedó elegido en Ajustes (config.json; el oscuro si no hay). Antes de crear
        # ninguna vista: cada una lee sus colores al construirse (views/tema.py).
        tema.cargar()
        self.page.theme_mode = tema.C.modo
        self.page.padding = 0 
        # La letra del panel (ver DISENO.md), registrada aquí una sola vez porque la barra lateral
        # la usa en todas las vistas. Las familias se llaman por lo que son (LetraTitulo,
        # LetraTexto), no por la fuente: cambiar de fuente es cambiar estas dos líneas.
        fuentes = dict(getattr(self.page, "fonts", {}) or {})
        # Plus Jakarta Sans, la de la página web (26/09, la eligió el dueño): títulos en Bold y el
        # resto en Medium (a su cliente la Creato Display Regular / Light le parecía muy delgada).
        fuentes["LetraTitulo"] = "assets/PlusJakartaSans-Bold.ttf"
        fuentes["LetraTexto"] = "assets/PlusJakartaSans-Medium.ttf"
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

    def cambiar_tema(self, nombre):
        # Lo llama Ajustes al elegir otro tema: se guarda, y se rehace Ajustes (con su barra) ya
        # con los colores nuevos; las demás vistas se construyen con ellos al abrirlas. La capa
        # de la ventana Perfil vive en page.overlay (se crea una vez): se quita para que la
        # próxima vez nazca con el velo del tema nuevo.
        tema.guardar(nombre)
        self.page.theme_mode = tema.C.modo
        ventana = getattr(self, "ventana_perfil", None)
        if ventana is not None:
            self.page.overlay.remove(ventana["capa"])
            self.ventana_perfil = None
        self.cambiar_vista("ajustes")

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