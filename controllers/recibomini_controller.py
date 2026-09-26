import os
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from models.entorno import recurso

class ReciboMiniController:

    # =========================================================
    # PERSPECTIVA 3D
    # =========================================================
    @staticmethod
    def _find_coefficients(pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        A = [row[:] for row in matrix]
        B = [p for pair in pb for p in pair]
        n = len(A)
        for i in range(n):
            max_row = max(range(i, n), key=lambda r: abs(A[r][i]))
            A[i], A[max_row] = A[max_row], A[i]
            B[i], B[max_row] = B[max_row], B[i]
            pivot = A[i][i]
            for j in range(i, n): A[i][j] /= pivot
            B[i] /= pivot
            for row in range(n):
                if row != i:
                    factor = A[row][i]
                    for j in range(i, n): A[row][j] -= factor * A[i][j]
                    B[row] -= factor * B[i]
        return B

    @staticmethod
    def aplicar_perspectiva_bloque(img_bloque, inclinacion=60):
        """Top más angosto que el bottom → efecto panel inclinado 3D."""
        ancho, alto = img_bloque.size
        puntos_control = [(inclinacion, 0), (ancho - inclinacion, 0), (ancho, alto), (0, alto)]
        puntos_origen  = [(0, 0),            (ancho, 0),               (ancho, alto), (0, alto)]
        matrix = ReciboMiniController._find_coefficients(puntos_control, puntos_origen)
        return img_bloque.transform(
            (ancho, alto), Image.Transform.PERSPECTIVE, matrix,
            resample=Image.Resampling.BILINEAR
        )

    # =========================================================
    # LIMPIADOR DE IMAGEN CHECKER
    # =========================================================
    @staticmethod
    def limpiar_imagen_checker(ruta_imagen):
        img = Image.open(ruta_imagen).convert("RGBA")
        ancho, alto = img.size
        img_gray = img.convert("L")
        pixeles = img_gray.load()
        y_corte = alto
        filas_validas = 0
        altura_minima_bloque = int(alto * 0.05)
        posible_y = alto
        for y in range(alto - 1, int(alto * 0.2), -1):
            pixeles_claros = 0
            for x in range(0, ancho, 2):
                if pixeles[x, y] > 30:
                    pixeles_claros += 1
            densidad = pixeles_claros / (ancho / 2)
            if densidad > 0.12:
                if filas_validas == 0:
                    posible_y = y
                filas_validas += 1
                if filas_validas >= altura_minima_bloque:
                    y_corte = posible_y
                    break
            else:
                filas_validas = 0
        nueva_altura = min(alto, y_corte + 5)
        return img.crop((0, 0, ancho, nueva_altura))

    # =========================================================
    # TEXTO CON SOMBRA DIFUMINADA
    # =========================================================
    @staticmethod
    def dibujar_texto_estilo_meta(
        imagen_fondo, posicion, texto, font,
        blur_radius=40, shadow_offset=(16, 16),
        opacity=255, shadow_opacity=180,
        fill_color=(255, 255, 255),
        doble_sombra=False
    ):
        x, y = posicion
        capa_sombra = Image.new("RGBA", imagen_fondo.size, (0, 0, 0, 0))
        draw_sombra = ImageDraw.Draw(capa_sombra)

        draw_sombra.text(
            (x + shadow_offset[0], y + shadow_offset[1]), texto,
            font=font, fill=(0, 0, 0, shadow_opacity), anchor="mm"
        )
        capa_sombra_borrosa = capa_sombra.filter(ImageFilter.GaussianBlur(blur_radius))

        imagen_fondo.paste(capa_sombra_borrosa, (0, 0), capa_sombra_borrosa)
        if doble_sombra:
            imagen_fondo.paste(capa_sombra_borrosa, (0, 0), capa_sombra_borrosa)

        draw_fijo = ImageDraw.Draw(imagen_fondo)
        draw_fijo.text(
            (x, y), texto, font=font,
            fill=(fill_color[0], fill_color[1], fill_color[2], opacity),
            anchor="mm"
        )

    # =========================================================
    # GENERADOR PRINCIPAL
    # =========================================================
    @staticmethod
    def generar_recibo(img_skin, correo1, correo2, usuario, fecha, ruta_salida):
        if not fecha or fecha.strip() == "":
            fecha = datetime.datetime.now().strftime("%d/%m/%Y")

        FONDO_PATH = recurso(os.path.join("assets", "plantillarecibo.jpg"))
        FUENTE_PATH = recurso(os.path.join("assets", "FORTNITE.OTF"))

        # RESOLUCIÓN 4K VERTICAL ORIGINAL
        W, H = 2160, 3840
        fondo = Image.open(FONDO_PATH).convert("RGBA").resize((W, H))

        try:
            fuente_correo  = ImageFont.truetype(FUENTE_PATH, 145)
            fuente_usuario = ImageFont.truetype(FUENTE_PATH, 175)
            fuente_fecha   = ImageFont.truetype(FUENTE_PATH, 215)
        except IOError:
            fuente_correo = fuente_usuario = fuente_fecha = ImageFont.load_default()

        draw_fondo = ImageDraw.Draw(fondo)

        # ─────────────────────────────────────────────────────
        # CORREOS
        # ─────────────────────────────────────────────────────
        draw_fondo.text((W // 2, 1090), correo1, font=fuente_correo, fill=(255, 255, 255, 255), anchor="mm")
        draw_fondo.text((W // 2, 1265), correo2, font=fuente_correo, fill=(255, 255, 255, 255), anchor="mm")

        # ─────────────────────────────────────────────────────
        # LOCKER DINÁMICO ESCALADO Y POSICIONADO
        # ─────────────────────────────────────────────────────
        if os.path.exists(img_skin):
            locker = ReciboMiniController.limpiar_imagen_checker(img_skin)
            
            # 🔥 AJUSTE: Forzamos un ancho grande y calculamos el alto para no deformar 🔥
            TARGET_WIDTH = 1850
            proporcion = locker.height / locker.width
            target_height = int(TARGET_WIDTH * proporcion)
            
            # Resize agranda o encoge la imagen a la medida exacta que le damos
            locker = locker.resize((TARGET_WIDTH, target_height), Image.Resampling.LANCZOS)

            inclinacion = int(locker.width * 0.015)
            if inclinacion > 0:
                locker = ReciboMiniController.aplicar_perspectiva_bloque(locker, inclinacion)

            # 🔥 AJUSTE: Lo centramos horizontalmente y lo subimos 🔥
            x_pos = (W - locker.width) // 2
            y_pos = 1640  # Posición fija más arriba, debajo de los correos

            # Sombra intensa
            capa_sombra_locker = Image.new("RGBA", fondo.size, (0, 0, 0, 0))
            draw_s = ImageDraw.Draw(capa_sombra_locker)
            draw_s.rectangle(
                [x_pos, y_pos + 20, x_pos + locker.width, y_pos + locker.height + 20],
                fill=(0, 0, 0, 255)
            )
            capa_sombra_locker = capa_sombra_locker.filter(ImageFilter.GaussianBlur(70))
            
            fondo.paste(capa_sombra_locker, (0, 0), capa_sombra_locker)
            fondo.paste(capa_sombra_locker, (0, 0), capa_sombra_locker)
            
            fondo.paste(locker, (x_pos, y_pos), locker)

        # ─────────────────────────────────────────────────────
        # TEXTOS DE PIE
        # ─────────────────────────────────────────────────────
        color_meta = (255, 79, 138)
        
        ReciboMiniController.dibujar_texto_estilo_meta(
            fondo, (W // 2, 3550), usuario, fuente_usuario,
            blur_radius=40, shadow_offset=(16, 16), shadow_opacity=165,
            fill_color=color_meta, doble_sombra=True 
        )
        
        ReciboMiniController.dibujar_texto_estilo_meta(
            fondo, (W // 2, 3715), fecha, fuente_fecha,
            blur_radius=40, shadow_offset=(16, 16), shadow_opacity=165,
            fill_color=(255, 255, 255), doble_sombra=True
        )

        resultado = fondo.convert("RGB")
        resultado.save(ruta_salida, "JPEG", quality=95)