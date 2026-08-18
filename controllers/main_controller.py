import flet as ft
from views.home_view import HomeView
from views.image1_view import Image1View
from views.contenido_view import ContenidoView
from views.ajustes_view import AjustesView
from views.biblioteca_view import BibliotecaView
from views.login_view import LoginView # <-- IMPORTAMOS LA VISTA DE LOGIN
from views.recibo_view import ReciboView # <-- IMPORTAMOS LA NUEVA VISTA DE RECIBO

class MainController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Anxie Store - Panel"
        self.page.theme_mode = "dark"
        self.page.padding = 0 
        
        self.content_container = ft.Container(expand=True)
        self.page.add(self.content_container)
        
        # <-- CAMBIO IMPORTANTE: Ahora arrancamos en la vista de LOGIN en lugar de 'home'
        self.cambiar_vista("home") 

    def cambiar_vista(self, vista: str):
        self.content_container.content = None
        
        # <-- AGREGAMOS LA CONDICIÓN DEL LOGIN
        #if vista == "login":
        #    vista_actual = LoginView(self)
            
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
            
        elif vista == "recibo": # <-- AGREGAMOS LA NUEVA RUTA AQUÍ
            vista_actual = ReciboView(self)
            
        else:
            # Fallback por si acaso
            vista_actual = HomeView(self)
            
        self.content_container.content = vista_actual
        self.page.update()