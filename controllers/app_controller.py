import os
import shutil
import time
import json
from controllers.image_controller import ImageController
from controllers.recibo_controller import ReciboController
from controllers.imgmini_controller import ImgMiniController
# 🔥 IMPORTAMOS EL NUEVO CONTROLADOR PARA RECIBOS MINI
from controllers.recibomini_controller import ReciboMiniController 

class AppController:
    def __init__(self, view, tipo="cuenta"):
        self.view = view
        self.tipo = tipo 
        self.ruta_cache_temporal = None 

    def procesar_clicks(self, e):
        try:
            self.view.mostrar_snack("Procesando imagen... esto puede tomar un momento.")
            
            # --- TRUCO PARA LA BIBLIOTECA (AMPLIADO) ---
            if self.tipo == "cuentas_mini":
                carpeta_destino = "cuentas"
            elif self.tipo == "recibos_mini":
                carpeta_destino = "recibos"
            else:
                carpeta_destino = self.tipo
                
            carpeta_biblio = os.path.join("biblioteca", carpeta_destino)
            os.makedirs(carpeta_biblio, exist_ok=True)
            
            timestamp = int(time.time())
            nombre_archivo = f"{self.tipo}_{timestamp}.png"
            self.ruta_cache_temporal = os.path.abspath(os.path.join(carpeta_biblio, nombre_archivo))
            
            # --- DECIDIR QUÉ MOTOR USAR ---
            if self.tipo == "cuentas":
                picos_path = self.view.input_picos.value
                skins_path = self.view.input_skins.value
                emotes_path = self.view.input_emotes.value
                if not all([picos_path, skins_path, emotes_path]):
                    self.view.mostrar_snack("Por favor, llena las rutas de las 3 imágenes.")
                    return
                ImageController.generar_miniatura(
                    picos_path, skins_path, emotes_path, 
                    self.view.txt_picos.value, self.view.txt_skins.value, self.view.txt_emotes.value, 
                    self.ruta_cache_temporal
                )
                
            elif self.tipo == "cuentas_mini":
                picos_path = self.view.input_picos.value
                skins_path = self.view.input_skins.value
                emotes_path = self.view.input_emotes.value
                if not all([picos_path, skins_path, emotes_path]):
                    self.view.mostrar_snack("Por favor, llena las rutas de las 3 imágenes.")
                    return
                ImgMiniController.generar_miniatura(
                    picos_path, skins_path, emotes_path, 
                    self.view.txt_picos.value, self.view.txt_skins.value, self.view.txt_emotes.value, 
                    self.ruta_cache_temporal
                )
                
            elif self.tipo == "recibos":
                skin_path = self.view.input_skin.value
                if not skin_path:
                    self.view.mostrar_snack("Brou, te falta elegir la imagen del locker.")
                    return
                tipo_cuenta = getattr(self.view, "radio_tipo_cuenta", None)
                val_tipo = tipo_cuenta.value if (tipo_cuenta and tipo_cuenta.value) else "NFA"
                usuario_completo = f"{val_tipo} - {self.view.txt_usuario.value}"

                ReciboController.generar_recibo(
                    skin_path, self.view.txt_correo1.value, self.view.txt_correo2.value, 
                    usuario_completo, self.view.txt_fecha.value, self.ruta_cache_temporal
                )

            elif self.tipo == "recibos_mini":
                # 🔥 LÓGICA DE RECIBOS MINIS 🔥
                skin_path = self.view.input_skin.value
                if not skin_path:
                    self.view.mostrar_snack("Brou, te falta elegir la imagen del locker mini.")
                    return
                tipo_cuenta = getattr(self.view, "radio_tipo_cuenta", None)
                val_tipo = tipo_cuenta.value if (tipo_cuenta and tipo_cuenta.value) else "NFA"
                usuario_completo = f"{val_tipo} - {self.view.txt_usuario.value}"

                # Usa el controlador de recibos mini
                ReciboMiniController.generar_recibo(
                    skin_path, self.view.txt_correo1.value, self.view.txt_correo2.value, 
                    usuario_completo, self.view.txt_fecha.value, self.ruta_cache_temporal
                )
            
            if os.path.exists(self.ruta_cache_temporal):
                self.view.actualizar_preview(self.ruta_cache_temporal)
                self.view.mostrar_snack(f"¡Vista previa de {self.tipo} generada!")
            else:
                self.view.mostrar_snack("Error: El motor no generó la imagen temporal.")

        except Exception as ex:
            self.view.mostrar_snack(f"Error fatal: {str(ex)}")

    def descargar_imagen(self, e):
        if not self.ruta_cache_temporal or not os.path.exists(self.ruta_cache_temporal):
            self.view.mostrar_snack("No hay ninguna imagen generada para descargar, bro.")
            return

        nombre_val = self.view.input_nombre.value.strip()
        if not nombre_val:
            nombre_val = f"descarga_{self.tipo}"
            
        nombre_val = "".join(c for c in nombre_val if c.isalnum() or c in ('_', '-'))
        nombre_archivo_final = f"{nombre_val}.png"

        try:
            es_en_la_nube = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None

            # --- TRUCO AMPLIADO PARA CONFIGURACIONES ---
            if self.tipo == "cuentas_mini":
                tipo_config = "cuentas"
            elif self.tipo == "recibos_mini":
                tipo_config = "recibos"
            else:
                tipo_config = self.tipo

            if es_en_la_nube:
                ruta_en_assets = os.path.join("biblioteca", tipo_config, nombre_archivo_final)
                shutil.copy(self.ruta_cache_temporal, ruta_en_assets)
                self.view.page_ref.launch_url(f"/{tipo_config}/{nombre_archivo_final}")
                self.view.mostrar_snack("¡Descarga iniciada en tu navegador, bro!")
                
            else:
                ruta_guardada = None
                archivo_config = "config.json"
                clave_json = f"ruta_descargas_{tipo_config}" 
                
                if os.path.exists(archivo_config):
                    try:
                        with open(archivo_config, "r") as f:
                            datos = json.load(f)
                            ruta_guardada = datos.get(clave_json)
                    except:
                        pass
                
                if ruta_guardada and os.path.exists(ruta_guardada):
                    carpeta_destino = ruta_guardada
                else:
                    carpeta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                
                ruta_destino_final = os.path.join(carpeta_destino, nombre_archivo_final)
                shutil.copy(self.ruta_cache_temporal, ruta_destino_final)
                
                nombre_carpeta = os.path.basename(carpeta_destino)
                self.view.mostrar_snack(f"¡Guardada en {nombre_carpeta}! -> {nombre_archivo_final}")

        except Exception as ex:
            self.view.mostrar_snack(f"Error al procesar la descarga: {ex}")