"""
models/cuenta_dao.py
Acceso a la tabla Cuentas de Supabase: las cuentas que vende anxiestore.com.

Una clase con métodos estáticos que hacen la consulta y devuelven los datos listos para pintar,
sin nada de pantalla aquí (el patrón de PlatilloDAO en el panel de Taku Monky). Crecerá por
subfases: leer, cambiar la visibilidad, crear, editar (la foto la sube models/r2_storage.py)
y borrar.

Columnas de la tabla: id, created_at, titulo, preciomxn, preciousd, descripcion, vbucks,
disponibilidad (texto libre que además dice las plataformas: la página busca PC / XBOX / PLAY /
NINTENDO en él), image_url (la URL pública completa de la foto en R2) y visible (desde el 24/09:
false = oculta; la regla RLS de lectura pública solo deja ver las visibles, así que una oculta
desaparece de la página sin tocar su código).

Los errores de red o de la API suben tal cual: la vista decide el aviso. Todo es bloqueante (ver
supabase_client.py): desde una vista, en otro hilo.
"""
from models.supabase_client import cliente

TABLA = "Cuentas"
# Todas las columnas, por su nombre (nunca select("*")): la tabla del panel pinta casi todas y
# los tres puntos enseñan el resto.
COLUMNAS = ("id, titulo, preciomxn, preciousd, disponibilidad, vbucks, descripcion, "
            "image_url, visible, created_at")


class EscrituraSinEfecto(Exception):
    """Supabase contestó sin error pero no cambió ninguna fila.

    Un UPDATE o un DELETE que la RLS no deja hacer NO da error: no encuentra ninguna fila que
    cumpla la regla y "sale bien" con 0 filas (se vio en el panel de Taku Monky, y aquí, con la
    prueba de la regla del 24/09: otro usuario "actualiza" 0 filas). Sin comprobarlo, el panel
    enseñaría un cambio que no se guardó. Pasa sin sesión del dueño, o si la cuenta ya no existe.
    """


class CuentaDAO:
    @staticmethod
    def obtener_todas():
        # Todas, las más nuevas primero (como lilshop: por id, de mayor a menor). Con la sesión
        # del dueño vienen también las ocultas; sin ella, solo las visibles.
        respuesta = cliente().table(TABLA).select(COLUMNAS).order("id", desc=True).execute()
        return respuesta.data or []

    @staticmethod
    def cambiar_visibilidad(id_cuenta, visible):
        # Solo la columna visible: ocultar no borra nada, la cuenta sigue en la tabla y en el
        # panel. Devuelve la fila como quedó.
        respuesta = (cliente().table(TABLA).update({"visible": visible})
                     .eq("id", id_cuenta).execute())
        if not respuesta.data:
            raise EscrituraSinEfecto(f"El cambio de visibilidad de la cuenta {id_cuenta} no "
                                     "cambió ninguna fila.")
        return respuesta.data[0]

    @staticmethod
    def crear(datos):
        # Una cuenta nueva (Agregar cuenta, subfase 2.6). `datos`: titulo, preciomxn, preciousd,
        # vbucks, disponibilidad, descripcion e image_url (la foto ya subida a R2). id, created_at
        # y visible (true) los pone la base. Devuelve la fila tal como quedó. Sin la sesión del
        # dueño la RLS lo rechaza con error (42501): un INSERT no "sale bien" con 0 filas.
        respuesta = cliente().table(TABLA).insert(datos).execute()
        if not respuesta.data:
            raise EscrituraSinEfecto("La cuenta nueva no se guardó.")
        return respuesta.data[0]

    @staticmethod
    def actualizar(id_cuenta, datos):
        # Editar (subfase 2.5): cambia las columnas de `datos` y devuelve la fila como quedó. Como
        # el ojo, un UPDATE que la RLS no deja "sale bien" con 0 filas: se comprueba.
        respuesta = cliente().table(TABLA).update(datos).eq("id", id_cuenta).execute()
        if not respuesta.data:
            raise EscrituraSinEfecto(f"Los cambios de la cuenta {id_cuenta} no cambiaron ninguna "
                                     "fila.")
        return respuesta.data[0]

    @staticmethod
    def borrar(id_cuenta):
        # Borrar (subfase 2.7): la fila entera. Devuelve la fila borrada (con su image_url, para
        # borrar después su foto de R2). Como el ojo, un DELETE que la RLS no deja "sale bien" con
        # 0 filas: se comprueba, o el panel quitaría de la tabla una cuenta que sigue en la tienda.
        respuesta = cliente().table(TABLA).delete().eq("id", id_cuenta).execute()
        if not respuesta.data:
            raise EscrituraSinEfecto(f"La cuenta {id_cuenta} no se borró (0 filas).")
        return respuesta.data[0]
