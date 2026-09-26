"""
models/supabase_client.py
El cliente único de Supabase del panel (la tienda anxiestore.com: proyecto jayxntvpiduxvgvluaky).

Se crea con la llave ANON, la misma que ya lleva la página: sola solo puede LEER las cuentas
visibles. Lo que deja ver las ocultas y escribir es la sesión del dueño (models/sesion.py): al
entrar, este mismo cliente manda su access_token en cada consulta y las reglas RLS de la tabla
Cuentas lo reconocen por el correo. La llave service_role no se usa ni vive en el .env.

Mismo patrón que el panel de Taku Monky (models/supabase_client.py), con dos diferencias:
  - Se crea al primer uso y no al importar: así el panel abre aunque falte el .env, y la
    librería (unos 0.4 s de importar) solo se carga cuando hace falta.
  - La sesión SE RECUERDA (lo pidió el dueño el 24/09: la contraseña, una vez por PC, como
    lilshop en el navegador). supabase-py la guarda en un "almacén": aquí, un JSON en
    %LOCALAPPDATA%\\AnxieStore\\sesion.json, fuera del proyecto y de cualquier repo. Guarda los
    tokens de la sesión (no la contraseña). En Taku Monky se quitó el 05/09 por su candado de
    licencia; aquí no hay candado.

Todo lo de aquí (y de los DAO) es BLOQUEANTE (red). En Flet 0.82 un manejador normal corre en
el hilo de la ventana, así que quien lo llame desde una vista lo manda a otro hilo
(asyncio.to_thread), o el panel se congela mientras espera.
"""
import json
import os
from pathlib import Path

from models.entorno import RUTA_ENV, leer

# Dónde se recuerda la sesión. Las herramientas de prueba lo ponen a None (antes de crear el
# cliente) para no tocar nunca la sesión de verdad: entonces vive solo en memoria.
ARCHIVO_SESION = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "AnxieStore" / "sesion.json"


class FaltaConfiguracion(Exception):
    """No hay .env, o le faltan SUPABASE_URL o SUPABASE_ANON_KEY."""


class AlmacenSesion:
    """El almacén de supabase-py (la interfaz SyncSupportedStorage: get_item, set_item,
    remove_item) sobre un archivo JSON. Se escribe entero cada vez, en un temporal que luego
    reemplaza al bueno: un corte a medias no deja el archivo roto."""

    def __init__(self, archivo):
        self.archivo = Path(archivo)

    def _leer(self):
        try:
            return json.loads(self.archivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _escribir(self, datos):
        if not datos:
            self.archivo.unlink(missing_ok=True)
            return
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.archivo.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos), encoding="utf-8")
        os.replace(temporal, self.archivo)

    def get_item(self, clave):
        return self._leer().get(clave)

    def set_item(self, clave, valor):
        datos = self._leer()
        datos[clave] = valor
        self._escribir(datos)

    def remove_item(self, clave):
        datos = self._leer()
        if datos.pop(clave, None) is not None:
            self._escribir(datos)

    def hay_algo(self):
        return bool(self._leer())

    def borrar(self):
        self._escribir({})


_cliente = None


def almacen():
    # El almacén de la sesión, o None si las pruebas lo apagaron.
    return AlmacenSesion(ARCHIVO_SESION) if ARCHIVO_SESION else None


def cliente():
    global _cliente
    if _cliente is None:
        url, llave = leer("SUPABASE_URL"), leer("SUPABASE_ANON_KEY")
        if not url or not llave:
            raise FaltaConfiguracion(f"Faltan SUPABASE_URL o SUPABASE_ANON_KEY en {RUTA_ENV}")
        from supabase import ClientOptions, create_client
        guardada = almacen()
        opciones = ClientOptions(storage=guardada) if guardada else ClientOptions()
        # Al crearse, supabase-py carga la sesión guardada (y la renueva si caducó).
        _cliente = create_client(url, llave, opciones)
    return _cliente
