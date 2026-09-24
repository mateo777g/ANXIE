import flet as ft
from views.home_view import HomeView
from views.image1_view import Image1View
from views.contenido_view import ContenidoView
from views.ajustes_view import AjustesView
from views.biblioteca_view import BibliotecaView
from views.login_view import LoginView
from views.recibo_view import ReciboView

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
        
        self.content_container = ft.Container(expand=True)
        self.page.add(self.content_container)
        
        self.cambiar_vista("home") 

    def cambiar_vista(self, vista: str):
        self.content_container.content = None
        
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
            
        elif vista == "recibo": 
            vista_actual = ReciboView(self)

        # 🔥 AGREGAMOS TUS DOS NUEVAS RUTAS AQUÍ 🔥
        elif vista == "cuenta_pequena":
            vista_actual = CuentaPequenaView(self)

        elif vista == "recibo_pequeno":
            vista_actual = ReciboPequenoView(self)
            
        else:
            vista_actual = HomeView(self)
            
        self.content_container.content = vista_actual
        self.page.update()