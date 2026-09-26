import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from models.entorno import recurso

class ImageController:

    @staticmethod
    def aplicar_perspectiva_bloque(img_bloque, inclinacion=130):
        ancho, alto = img_bloque.size
        puntos_control = [(inclinacion, 0), (ancho - inclinacion, 0), (ancho, alto), (0, alto)]
        puntos_origen = [(0, 0), (ancho, 0), (ancho, alto), (0, alto)]
        matrix = ImageController._find_coefficients(puntos_control, puntos_origen)
        return img_bloque.transform((ancho, alto), Image.Transform.PERSPECTIVE, matrix, resample=Image.Resampling.BILINEAR)

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
    def dibujar_texto_estilo_meta(imagen_fondo, posicion, texto, font, blur_radius=40, shadow_offset=(16, 16), stroke_width=0, opacity=255, intensificar_sombra=False, shadow_opacity=255):
        x, y = posicion
        capa_sombra = Image.new("RGBA", imagen_fondo.size, (0, 0, 0, 0))
        draw_sombra = ImageDraw.Draw(capa_sombra)

        draw_sombra.text((x + shadow_offset[0], y + shadow_offset[1]), texto, font=font, fill=(0, 0, 0, shadow_opacity), anchor="mm")

        capa_sombra_borrosa = capa_sombra.filter(ImageFilter.GaussianBlur(blur_radius))

        if intensificar_sombra:
            imagen_fondo.paste(capa_sombra_borrosa, (0, 0), capa_sombra_borrosa)

        imagen_fondo.paste(capa_sombra_borrosa, (0, 0), capa_sombra_borrosa)

        draw_fijo = ImageDraw.Draw(imagen_fondo)
        draw_fijo.text((x, y), texto, font=font, fill=(255, 255, 255, opacity), anchor="mm")

    # =========================================================
    # EL ESCÁNER MATA-GATOS (POR VOLUMEN)
    # =========================================================
    @staticmethod
    def limpiar_imagen_checker(ruta_imagen):
        img = Image.open(ruta_imagen).convert("RGBA")
        ancho, alto = img.size
        
        img_gray = img.convert("L")
        pixeles = img_gray.load()
        
        y_corte = alto
        filas_validas = 0
        
        # Le pedimos que el bloque de color mida al menos el 5% de la altura de la imagen.
        # Las skins miden mucho más que eso. El logo del gato mide menos.
        altura_minima_bloque = int(alto * 0.05) 
        posible_y = alto
        
        # Subimos desde abajo
        for y in range(alto - 1, int(alto * 0.2), -1):
            pixeles_claros = 0
            
            # Checamos la fila saltando de 2 en 2 píxeles (más rápido, mismo resultado)
            for x in range(0, ancho, 2):
                if pixeles[x, y] > 30: # 30 para ignorar el fondo oscuro o ruidoso
                    pixeles_claros += 1
                    
            # Densidad en base a la mitad de píxeles que revisamos
            densidad = pixeles_claros / (ancho / 2)
            
            # Si al menos el 12% de la fila tiene color (agarra perfecto 1 o 2 skins sueltas)
            if densidad > 0.12:
                if filas_validas == 0:
                    posible_y = y # Guardamos la coordenada del primer píxel de color que vimos
                
                filas_validas += 1
                
                # Si ya confirmamos que este bloque es MUY alto, son las skins 100%
                if filas_validas >= altura_minima_bloque:
                    y_corte = posible_y
                    break
            else:
                # Si hay un hueco negro, se rompe la racha. 
                # Así es como el gato pierde: empieza a sumar, pero como es bajito, 
                # se le acaba el color antes de llegar a la 'altura_minima_bloque' y lo reseteamos a 0.
                filas_validas = 0
                
        # Le damos un pequeño respiro de 5 píxeles para que la skin no se vea rasurada
        nueva_altura = min(alto, y_corte + 5)
        img_recortada = img.crop((0, 0, ancho, nueva_altura))
        
        return img_recortada

    @staticmethod
    def generar_miniatura(img_picos, img_skins, img_emotes, txt_picos, txt_skins, txt_emotes, ruta_salida):
        FONDO_PATH = recurso(os.path.join("assets", "fondo.png"))
        FUENTE_PATH = recurso(os.path.join("assets", "FORTNITE.OTF"))

        W, H = 3840, 2160
        fondo = Image.open(FONDO_PATH).convert("RGBA").resize((W, H))

        POS_BLOQUE = (-40, 350)
        ancho_bloque, alto_bloque = 4040, 1800

        try:
            fuente_grande = ImageFont.truetype(FUENTE_PATH, 440)
            fuente_skins  = ImageFont.truetype(FUENTE_PATH, 200)
            fuente_lados  = ImageFont.truetype(FUENTE_PATH, 180)
            fuente_ticket = ImageFont.truetype(FUENTE_PATH, 98)
        except IOError:
            fuente_grande = fuente_skins = fuente_lados = fuente_ticket = ImageFont.load_default()

        ImageController.dibujar_texto_estilo_meta(
            fondo, (1920, 344), "¡CUENTA DISPONIBLE!", fuente_grande,
            blur_radius=35, shadow_offset=(18, 18), stroke_width=0, opacity=255, shadow_opacity=170
        )

        bloque_paso = Image.new("RGBA", (ancho_bloque, alto_bloque), (0, 0, 0, 0))

        picos_raw  = ImageController.limpiar_imagen_checker(img_picos).resize((1060, 1070))
        skins_raw  = ImageController.limpiar_imagen_checker(img_skins).resize((1300, 1320))
        emotes_raw = ImageController.limpiar_imagen_checker(img_emotes).resize((1060, 1070))

        bloque_paso.paste(skins_raw, (1310, 80), skins_raw)
        bloque_paso.paste(picos_raw, (170, 350), picos_raw)
        bloque_paso.paste(emotes_raw, (2690, 350), emotes_raw)

        bloque_deformado = ImageController.aplicar_perspectiva_bloque(bloque_paso, inclinacion=130)

        mascara_bloque = bloque_deformado.split()[3]
        sombra_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sombra_canvas.paste((0, 0, 0, 190), POS_BLOQUE, mask=mascara_bloque)

        sombra_difuminada = sombra_canvas.filter(ImageFilter.GaussianBlur(50))
        fondo.paste(sombra_difuminada, (0, 0), sombra_difuminada)
        fondo.paste(bloque_deformado, POS_BLOQUE, bloque_deformado)

        capa_textos_3d = Image.new("RGBA", (ancho_bloque, alto_bloque), (0, 0, 0, 0))

        ImageController.dibujar_texto_estilo_meta(capa_textos_3d, (620, 1600), txt_picos, fuente_lados, blur_radius=16, shadow_offset=(12, 12), opacity=245)
        ImageController.dibujar_texto_estilo_meta(capa_textos_3d, (1960, 1555), txt_skins, fuente_skins, blur_radius=16, shadow_offset=(12, 12), opacity=245)
        ImageController.dibujar_texto_estilo_meta(capa_textos_3d, (3300, 1600), txt_emotes, fuente_lados, blur_radius=16, shadow_offset=(12, 12), opacity=245)
        ImageController.dibujar_texto_estilo_meta(capa_textos_3d, (1960, 1750), "PUEDES ABRIR TICKET PARA COMPRAR O RESOLVER DUDAS.", fuente_ticket, blur_radius=12, shadow_offset=(1, 1))

        textos_deformados = ImageController.aplicar_perspectiva_bloque(capa_textos_3d, inclinacion=150)
        fondo.paste(textos_deformados, POS_BLOQUE, textos_deformados)

        resultado = fondo.convert("RGB")
        resultado.save(ruta_salida, "JPEG", quality=95)