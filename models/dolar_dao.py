"""
models/dolar_dao.py
El dólar de la tienda: la fila única de la tabla Ajustes de Supabase (desde el 3/11/2026).

El cliente pone solo el precio en MXN de cada cuenta; el USD lo calcula la BASE (un trigger en
Cuentas: preciomxn / dolar_mxn, en dólares enteros, mínimo 1). Al cambiar el dólar, otro trigger
recalcula todas las cuentas, así que la página se actualiza sola sin tocar su código.

Dos modos (la tarjeta DÓLAR de Ajustes):
  - En vivo (dolar_en_vivo = true): la función dolar_al_dia() de la base lo trae de Frankfurter
    (las tasas de referencia del Banco Central Europeo, gratis y sin llave). Un cron de la base la
    llama cada 3 horas, aunque el panel esté cerrado.
  - Manual: el número que pone el cliente; el cron no lo toca.

Solo el dueño (su sesión) puede leer y cambiar la tabla y llamar a la función: la RLS y los
permisos de la base. Todo es bloqueante (red): desde una vista, en otro hilo.
"""
import datetime

from models.cuenta_dao import EscrituraSinEfecto
from models.supabase_client import cliente

TABLA = "Ajustes"
COLUMNAS = "dolar_mxn, dolar_en_vivo, dolar_fecha, dolar_fuente"


class DolarDAO:
    @staticmethod
    def obtener():
        # La fila del dólar: {"dolar_mxn": 18.7197, "dolar_en_vivo": True, ...}, o None si no la
        # deja ver (sin la sesión del dueño la RLS no devuelve nada).
        respuesta = cliente().table(TABLA).select(COLUMNAS).eq("id", 1).execute()
        return (respuesta.data or [None])[0]

    @staticmethod
    def poner_manual(valor):
        # El dólar a mano: deja de ir en vivo. Devuelve la fila como quedó (la base ya recalculó
        # el USD de todas las cuentas).
        ahora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        respuesta = (cliente().table(TABLA)
                     .update({"dolar_mxn": valor, "dolar_en_vivo": False, "dolar_fecha": ahora,
                              "dolar_fuente": "Manual"})
                     .eq("id", 1).execute())
        if not respuesta.data:
            raise EscrituraSinEfecto("El dólar no se guardó (0 filas).")
        return respuesta.data[0]

    @staticmethod
    def poner_en_vivo():
        # Vuelve a en vivo y trae el dólar de hoy en ese momento (sin esperar al cron).
        respuesta = cliente().rpc("dolar_al_dia", {"forzar": True}).execute()
        if not respuesta.data:
            raise EscrituraSinEfecto("El dólar en vivo no se guardó.")
        return respuesta.data


def usd_de(mxn, dolar):
    # Lo mismo que calcula la base, para enseñarlo en el formulario mientras se escribe:
    # dólares enteros, redondeando la mitad hacia arriba (como round() de Postgres), mínimo 1.
    if mxn is None or not dolar:
        return None
    return max(1, int(float(mxn) / float(dolar) + 0.5))
