"""
models/sesion.py
La sesión del dueño en Supabase Auth: la que deja ver las cuentas ocultas y editar la tabla.

Como en lilshop.html, el correo va fijo (ADMIN_EMAIL, en el .env) y solo se pide la
contraseña. Es un usuario normal de Supabase Auth, el único que hay (los registros están
apagados); las reglas RLS de Cuentas le dejan leerlo todo y escribir, a nadie más.

Se entra AL ABRIR EL PANEL (lo decidió el dueño el 24/09), en la pantalla de login
(views/login_view.py), y la sesión SE RECUERDA en %LOCALAPPDATA%\\AnxieStore\\sesion.json (ver
supabase_client.py): con una guardada, el panel abre directo en Inicio, sin red (los generadores
no la necesitan), y no se comprueba hasta que algo la usa (la vista Cuentas, con comprobar()).
supabase-py renueva solo el access_token antes de que caduque (dura una hora) y guarda el nuevo.

Los errores de red y de la API suben tal cual: la vista decide el aviso (AuthApiError con code
"invalid_credentials" si la contraseña no es; httpx.RequestError sin internet).

OJO si algún día hay "Cerrar sesión": auth.sign_out() de supabase-py cierra por defecto la sesión
del dueño EN TODAS PARTES (scope "global": también lilshop en el navegador). Aquí va con
{"scope": "local"}.
"""
from models.entorno import leer
from models.supabase_client import FaltaConfiguracion, almacen, cliente

_comprobada = False     # si ya se validó con el servidor en esta ejecución del panel


def correo_admin():
    return leer("ADMIN_EMAIL")


def hay_sesion_guardada():
    # ¿Hay una sesión recordada en esta PC? Solo mira el archivo (sin red y sin cargar
    # supabase-py): así decide MainController, al abrir, si enseña el login o Inicio.
    guardada = almacen()
    return bool(guardada and guardada.hay_algo())


def comprobar():
    """¿Hay una sesión que sirva? True / False; sin internet, sube el error de red.

    La primera vez en cada ejecución la valida con el servidor (set_session: si el token sigue
    valiendo pregunta por el usuario; si caducó, lo renueva). Hace falta además porque
    supabase-py, al cargar una sesión guardada que aún vale, no arranca la renovación automática:
    set_session la arranca y pone el token en las consultas. Si el servidor ya no la acepta
    (revocada, contraseña cambiada), se olvida y devuelve False."""
    global _comprobada
    from supabase_auth.errors import AuthApiError, AuthSessionMissingError

    auth = cliente().auth
    try:
        guardada = auth.get_session()          # la del archivo; la renueva si caducó
        if not guardada:
            return False
        if not _comprobada:
            auth.set_session(guardada.access_token, guardada.refresh_token)
            _comprobada = True
        return True
    except (AuthApiError, AuthSessionMissingError) as e:
        if getattr(e, "status", None) and e.status >= 500:
            raise                               # el servidor falló: no es que no valga
        olvidar()
        return False


def iniciar_sesion(contrasena):
    global _comprobada
    if not correo_admin():
        raise FaltaConfiguracion("Falta ADMIN_EMAIL en el .env")
    cliente().auth.sign_in_with_password({"email": correo_admin(), "password": contrasena})
    _comprobada = True                          # supabase-py ya la guardó en el almacén


def olvidar():
    # Borra la sesión recordada (sin llamar al servidor): la próxima vez, el panel pide entrar.
    global _comprobada
    _comprobada = False
    guardada = almacen()
    if guardada:
        guardada.borrar()


def cerrar_sesion():
    # Solo esta PC (scope "local"): la sesión de lilshop en el navegador sigue abierta.
    olvidar()
    cliente().auth.sign_out({"scope": "local"})
