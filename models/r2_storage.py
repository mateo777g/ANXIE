"""
models/r2_storage.py
Las fotos de las cuentas en Cloudflare R2 (bucket anxie-store-fotos), DIRECTO desde el panel, sin
el Worker de Cloudflare que usaba lilshop (se borra al final de la fase 2).

Qué hace (subfase 2.4, 26/09):
  - preparar_foto(ruta): comprueba que el archivo pesa como mucho 15 MB y que de verdad es una
    imagen, y la pasa a WebP calidad 80 con el lado largo como mucho de 2560 px (lo eligió el
    dueño el 25/09: a 1600 no se leen los nombres de las skins con el zoom del catálogo).
  - R2Storage.subir_foto(ruta): la prepara y la sube con Content-Type image/webp. Nombre =
    milisegundos + ".webp", el mismo formato que las que ya hay (1787093217877.webp). Devuelve
    el nombre y la URL pública completa, que es lo que va en image_url.
  - R2Storage.borrar_foto(nombre o URL): la borra. Si falla, NO se pierde en silencio: se apunta
    en %LOCALAPPDATA%\\AnxieStore\\fotos_por_borrar.json (fuera del proyecto y de los repos, como
    las huérfanas de Taku Monky) y el error sube igual, para que la vista avise.
    R2Storage.reintentar_pendientes() vuelve a probar las apuntadas.

Las llaves son de la API S3 de R2 y SOLO sirven para leer y escribir objetos de este bucket (un
token de Cloudflare con "Object Read & Write" limitado a anxie-store-fotos). Viven en el .env del
panel (R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET, R2_PUBLIC_BASE), nunca en
el repo: es público.

La firma S3 (SigV4) va a mano con httpx y no con boto3: solo hacen falta PUT y DELETE de un
objeto (unas 40 líneas), httpx ya viene con supabase, y boto3 añadiría ~80 MB al .exe, ~0.5 s
de importar y sus sumas CRC32 por defecto (desde la 1.36), que R2 ha rechazado en algunas
versiones. La firma se comprobó contra la de botocore (idéntica) el 26/09.

Todo es BLOQUEANTE (disco, Pillow y red): desde una vista, en asyncio.to_thread, como el resto.
"""
import hashlib
import hmac
import io
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

from models.entorno import RUTA_ENV, leer
from models.supabase_client import FaltaConfiguracion

TAMANO_MAXIMO = 15 * 1024 * 1024     # 15 MB: se mide el archivo de verdad, no una cabecera
LADO_MAXIMO = 2560
CALIDAD_WEBP = 80
TIPO = "image/webp"
# El nombre de una foto: solo cifras + .webp (el mismo guardián que el Worker, contra rutas raras).
NOMBRE_VALIDO = re.compile(r"^[0-9]+\.webp$")
REGION = "auto"                       # R2 no tiene regiones: SigV4 lleva "auto"

# Las fotos que no se pudieron borrar. Las pruebas lo cambian por uno en la carpeta temporal.
ARCHIVO_PENDIENTES = (Path(os.getenv("LOCALAPPDATA") or Path.home()) / "AnxieStore"
                      / "fotos_por_borrar.json")


class ImagenNoValida(Exception):
    """El archivo no se puede subir: pesa más de 15 MB, no es una imagen o está roto. El mensaje
    ya viene listo para enseñarlo en un aviso."""


class ErrorR2(Exception):
    """R2 contestó con un error (llaves malas, sin permiso, el bucket no existe...)."""

    def __init__(self, mensaje, estado=None):
        super().__init__(mensaje)
        self.estado = estado


# ---------------------------------------------------------------- la foto

def comprobar_foto(ruta):
    """Lo rápido (unos ms): que exista, que pese como mucho 15 MB y que sea una imagen sin daños.
    Devuelve lo que pesa en bytes. ImagenNoValida si no vale. Para avisar al ELEGIR la foto, sin
    esperar a guardar; preparar_foto lo vuelve a hacer igual."""
    from PIL import Image               # Pillow tarda en importar: solo cuando hace falta

    ruta = Path(ruta)
    try:
        tamano = ruta.stat().st_size
    except OSError:
        raise ImagenNoValida("No se encontró el archivo.")
    if tamano > TAMANO_MAXIMO:
        raise ImagenNoValida(f"La foto pesa {tamano / 1024 / 1024:.1f} MB; el máximo es 15 MB.")
    if tamano == 0:
        raise ImagenNoValida("El archivo está vacío.")
    try:
        # verify() lee el archivo entero buscando daños sin decodificarlo. El límite de píxeles de
        # Pillow (~179 millones) corta las "bombas" (un PNG pequeño que ocupa gigas al abrirlo).
        with Image.open(ruta) as prueba:
            prueba.verify()
    except Image.DecompressionBombError:
        raise ImagenNoValida("La imagen es demasiado grande.")
    except Exception:
        raise ImagenNoValida("El archivo no es una imagen o está dañado.")
    return tamano


def preparar_foto(ruta):
    """Devuelve los bytes WebP de la foto, listos para subir. ImagenNoValida si no vale."""
    from PIL import Image, ImageOps

    ruta = Path(ruta)
    comprobar_foto(ruta)
    try:
        # Tras verify() hay que abrirla otra vez para usarla.
        with Image.open(ruta) as original:
            original.load()
            # Las fotos del celular vienen tumbadas con una marca EXIF de "gírame": se aplica
            # (el <canvas> de lilshop también lo hacía) y la marca no pasa a la WebP.
            imagen = ImageOps.exif_transpose(original)
    except Image.DecompressionBombError:
        raise ImagenNoValida("La imagen es demasiado grande.")
    except Exception:
        # Pillow no la reconoce (no es imagen) o está rota: UnidentifiedImageError, OSError,
        # SyntaxError... todas quieren decir lo mismo para el dueño.
        raise ImagenNoValida("El archivo no es una imagen o está dañado.")

    # WebP guarda la transparencia (RGBA) igual que el <canvas> de lilshop; el resto, a RGB.
    tiene_alfa = imagen.mode in ("RGBA", "LA", "PA") or (
        imagen.mode == "P" and "transparency" in imagen.info)
    imagen = imagen.convert("RGBA" if tiene_alfa else "RGB")
    # thumbnail solo encoge (una foto pequeña se queda como está) y guarda la proporción.
    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.Resampling.LANCZOS)

    salida = io.BytesIO()
    imagen.save(salida, "WEBP", quality=CALIDAD_WEBP)
    return salida.getvalue()


# ---------------------------------------------------------------- nombres

_candado_nombre = threading.Lock()
_ultimo_ms = 0


def nuevo_nombre():
    # Milisegundos + ".webp". Dos subidas en el mismo milisegundo no chocan: se suma uno.
    global _ultimo_ms
    with _candado_nombre:
        ms = max(int(time.time() * 1000), _ultimo_ms + 1)
        _ultimo_ms = ms
    return f"{ms}.webp"


def nombre_de(foto):
    """El nombre del objeto a partir del nombre o de la URL pública (lo que guarda image_url).
    ValueError si no es una foto de las nuestras: así nunca se borra nada de fuera."""
    nombre = str(foto or "").strip()
    if "/" in nombre:
        base = leer("R2_PUBLIC_BASE").rstrip("/")
        if not base or not nombre.startswith(base + "/"):
            raise ValueError(f"La URL no es del bucket de fotos: {nombre}")
        nombre = nombre[len(base) + 1:]
    if not NOMBRE_VALIDO.match(nombre):
        raise ValueError(f"Nombre de foto no válido: {nombre}")
    return nombre


# ---------------------------------------------------------------- S3 (SigV4 a mano)

def _configuracion():
    datos = {
        "llave": leer("R2_ACCESS_KEY_ID"),
        "secreto": leer("R2_SECRET_ACCESS_KEY"),
        "endpoint": leer("R2_ENDPOINT").rstrip("/"),
        "bucket": leer("R2_BUCKET"),
        "base": leer("R2_PUBLIC_BASE").rstrip("/"),
    }
    faltan = [clave for clave, valor in (
        ("R2_ACCESS_KEY_ID", datos["llave"]), ("R2_SECRET_ACCESS_KEY", datos["secreto"]),
        ("R2_ENDPOINT", datos["endpoint"]), ("R2_BUCKET", datos["bucket"]),
        ("R2_PUBLIC_BASE", datos["base"])) if not valor]
    if faltan:
        raise FaltaConfiguracion(f"Faltan {', '.join(faltan)} en {RUTA_ENV}")
    return datos


def _hmac(llave, texto):
    return hmac.new(llave, texto.encode("utf-8"), hashlib.sha256).digest()


def firmar(metodo, url, cabeceras, cuerpo, llave, secreto, region=REGION, servicio="s3",
           ahora=None):
    """Devuelve las cabeceras de la petición con la firma SigV4 de AWS (la que habla R2).

    Se firman todas las cabeceras que se pasan, más host, x-amz-date y x-amz-content-sha256 (el
    SHA-256 del cuerpo). La URL tiene que llegar ya codificada (quote), sin parámetros."""
    ahora = ahora or datetime.now(timezone.utc)
    fecha_hora = ahora.strftime("%Y%m%dT%H%M%SZ")
    fecha = fecha_hora[:8]
    partes = urlparse(url)

    cabeceras = {clave.lower(): str(valor).strip() for clave, valor in cabeceras.items()}
    cabeceras["host"] = partes.netloc
    cabeceras["x-amz-date"] = fecha_hora
    cabeceras.setdefault("x-amz-content-sha256", hashlib.sha256(cuerpo or b"").hexdigest())

    firmadas = ";".join(sorted(cabeceras))
    peticion_canonica = "\n".join([
        metodo,
        partes.path or "/",
        partes.query,
        "".join(f"{clave}:{cabeceras[clave]}\n" for clave in sorted(cabeceras)),
        firmadas,
        cabeceras["x-amz-content-sha256"],
    ])
    ambito = f"{fecha}/{region}/{servicio}/aws4_request"
    texto_a_firmar = "\n".join([
        "AWS4-HMAC-SHA256", fecha_hora, ambito,
        hashlib.sha256(peticion_canonica.encode("utf-8")).hexdigest(),
    ])
    llave_firma = _hmac(_hmac(_hmac(_hmac(("AWS4" + secreto).encode("utf-8"), fecha), region),
                              servicio), "aws4_request")
    firma = hmac.new(llave_firma, texto_a_firmar.encode("utf-8"), hashlib.sha256).hexdigest()

    cabeceras["authorization"] = (f"AWS4-HMAC-SHA256 Credential={llave}/{ambito}, "
                                  f"SignedHeaders={firmadas}, Signature={firma}")
    return cabeceras


def _pedir(metodo, nombre, cuerpo=b"", cabeceras=None):
    import httpx

    datos = _configuracion()
    # Estilo "ruta" (endpoint/bucket/objeto): es el que R2 recomienda.
    url = f"{datos['endpoint']}/{quote(datos['bucket'])}/{quote(nombre)}"
    firmadas = firmar(metodo, url, cabeceras or {}, cuerpo, datos["llave"], datos["secreto"])
    firmadas.pop("host")              # httpx la pone él (la misma)
    respuesta = httpx.request(metodo, url, headers=firmadas, content=cuerpo or None,
                              timeout=httpx.Timeout(60, connect=15))
    if respuesta.status_code >= 300:
        # R2 contesta un XML con <Code> (SignatureDoesNotMatch, AccessDenied, NoSuchBucket...).
        codigo = re.search(r"<Code>([^<]+)</Code>", respuesta.text or "")
        raise ErrorR2(f"R2 respondió {respuesta.status_code}"
                      + (f" ({codigo.group(1)})" if codigo else "") + f" al {metodo} de {nombre}.",
                      respuesta.status_code)
    return respuesta


# ---------------------------------------------------------------- las huérfanas

_candado_pendientes = threading.Lock()


def _leer_pendientes():
    try:
        datos = json.loads(Path(ARCHIVO_PENDIENTES).read_text(encoding="utf-8"))
        return datos if isinstance(datos, list) else []
    except (OSError, ValueError):
        return []


def _escribir_pendientes(lista):
    archivo = Path(ARCHIVO_PENDIENTES)
    if not lista:
        archivo.unlink(missing_ok=True)
        return
    archivo.parent.mkdir(parents=True, exist_ok=True)
    temporal = archivo.with_suffix(".tmp")
    temporal.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporal, archivo)


def _apuntar_pendiente(nombre, motivo):
    with _candado_pendientes:
        lista = [p for p in _leer_pendientes() if p.get("nombre") != nombre]
        lista.append({"nombre": nombre, "motivo": str(motivo)[:300],
                      "fecha": datetime.now().isoformat(timespec="seconds")})
        _escribir_pendientes(lista)


def _quitar_pendiente(nombre):
    with _candado_pendientes:
        lista = _leer_pendientes()
        resto = [p for p in lista if p.get("nombre") != nombre]
        if len(resto) != len(lista):
            _escribir_pendientes(resto)


# ---------------------------------------------------------------- lo que usan las vistas

class R2Storage:
    @staticmethod
    def subir_foto(ruta):
        """Prepara la foto y la sube. Devuelve {"nombre": ..., "url": ...} (url va a image_url).
        ImagenNoValida si el archivo no vale; ErrorR2 / httpx.HTTPError si falla la subida."""
        cuerpo = preparar_foto(ruta)
        nombre = nuevo_nombre()
        _pedir("PUT", nombre, cuerpo, {"content-type": TIPO})
        return {"nombre": nombre, "url": f"{_configuracion()['base']}/{nombre}"}

    @staticmethod
    def borrar_foto(foto):
        """Borra la foto (nombre o URL pública). Borrar una que ya no existe también sale bien
        (S3 contesta 204 igual). Si falla, queda apuntada en ARCHIVO_PENDIENTES y el error sube."""
        nombre = nombre_de(foto)
        try:
            _pedir("DELETE", nombre)
        except Exception as error:
            _apuntar_pendiente(nombre, error)
            raise
        _quitar_pendiente(nombre)

    @staticmethod
    def pendientes():
        # Las fotos que quedaron sin borrar: [{"nombre", "motivo", "fecha"}].
        return _leer_pendientes()

    @staticmethod
    def reintentar_pendientes():
        """Vuelve a probar a borrar las apuntadas. Devuelve cuántas siguen sin poder borrarse."""
        for pendiente in _leer_pendientes():
            try:
                R2Storage.borrar_foto(pendiente.get("nombre"))
            except ValueError:
                _quitar_pendiente(pendiente.get("nombre"))    # apunte roto: no es de las nuestras
            except Exception:
                pass                                           # sigue apuntada (con su motivo nuevo)
        return len(_leer_pendientes())
