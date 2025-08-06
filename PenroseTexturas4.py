import streamlit as st
import math, cmath, cairo, random
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime
import base64

# Configuración de la página
st.set_page_config(
    page_title="🎨 Generador Mosaicos Penrose con Texturas",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .pattern-preview {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .texture-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Definición de paletas basadas en teoría del color
PALETAS_TEXTURAS = {
    'Fuego': {
        'texturas': ['rosa', 'amarillo', 'naranja'],
        'descripcion': '🔥 Análoga Cálida - Rosa, Amarillo, Naranja',
        'teoria': 'Colores análogos en el espectro cálido para energía y dinamismo'
    },
    'Océano': {
        'texturas': ['azul', 'verde', 'gris 1'],
        'descripcion': '🌊 Análoga Fría - Azul, Verde, Gris',
        'teoria': 'Colores fríos consecutivos que transmiten calma y naturaleza'
    },
    'Contraste': {
        'texturas': ['azul', 'naranja', 'blanco1'],
        'descripcion': '⚡ Complementaria - Azul, Naranja, Blanco',
        'teoria': 'Colores opuestos que crean máximo impacto visual'
    },
    'Elegante': {
        'texturas': ['gris2', 'gris 1', 'blanco 4', 'blanco1'],
        'descripcion': '🏛️ Monocromática - Escala de Grises',
        'teoria': 'Escala de valores en un solo tono para sofisticación'
    },
    'Triádica': {
        'texturas': ['rosa', 'verde', 'amarillo'],
        'descripcion': '🎨 Triádica Vibrante - Rosa, Verde, Amarillo',
        'teoria': 'Tres colores equidistantes para balance dinámico'
    }
}

@st.cache_data
def cargar_texturas_streamlit():
    """Carga texturas para Streamlit con manejo de errores"""
    texturas = {}
    nombres_texturas = [
        "verde.png", "blanco1.png", "naranja.png", 
        "blanco2.png", "azul.png", "blanco 3.png", "gris 1.png", 
        "gris2.png", "blanco 4.png", "amarillo.png", "rosa.png"
    ]
    
    texturas_encontradas = []
    texturas_faltantes = []
    
    for nombre in nombres_texturas:
        nombre_limpio = nombre.replace('.png', '')
        try:
            if os.path.exists(nombre):
                texture = Image.open(nombre)
                # Mantener tamaño original para mejor calidad en murales
                # Solo redimensionar si es extremadamente grande
                if texture.size[0] > 1000 or texture.size[1] > 1000:
                    # Redimensionar manteniendo proporción
                    texture.thumbnail((800, 800), Image.Resampling.LANCZOS)
                
                texturas[nombre_limpio] = {
                    'array': np.array(texture),
                    'size': texture.size,
                    'pil': texture
                }
                texturas_encontradas.append(nombre)
            else:
                texturas_faltantes.append(nombre)
        except Exception as e:
            texturas_faltantes.append(f"{nombre} (Error: {str(e)})")
    
    return texturas, texturas_encontradas, texturas_faltantes

def aplicar_textura_a_triangulo_individual(ctx, vertices, textura_info, escala_textura=2.0):
    """Aplica una textura específica a un triángulo individual"""
    if not textura_info:
        return False
    
    # Obtener dimensiones del triángulo
    xs = [v.real for v in vertices]
    ys = [v.imag for v in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    ancho_triangulo = max_x - min_x
    alto_triangulo = max_y - min_y
    
    # Obtener textura PIL
    texture_pil = textura_info['pil']
    
    # Calcular tamaño de textura para llenar el triángulo
    tamano_textura = max(int(ancho_triangulo * 300), int(alto_triangulo * 300))  # Escalar para Cairo
    tamano_textura = max(100, min(tamano_textura, 800))  # Limitar tamaño
    
    # Aplicar escala de usuario
    tamano_final = int(tamano_textura * escala_textura)
    
    # Redimensionar textura para el triángulo
    texture_resized = texture_pil.resize((tamano_final, tamano_final), Image.Resampling.LANCZOS)
    
    # Convertir a RGBA
    if texture_resized.mode != 'RGBA':
        texture_resized = texture_resized.convert('RGBA')
    
    # Crear surface de Cairo para esta textura
    texture_array = np.array(texture_resized)
    height, width = texture_array.shape[:2]
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    buf = surface.get_data()
    
    # Convertir RGBA a BGRA para Cairo
    if len(texture_array.shape) == 3 and texture_array.shape[2] == 4:
        bgra_array = texture_array[:, :, [2, 1, 0, 3]]
    elif len(texture_array.shape) == 3 and texture_array.shape[2] == 3:
        bgr_array = texture_array[:, :, [2, 1, 0]]
        bgra_array = np.dstack([bgr_array, np.full((height, width), 255, dtype=np.uint8)])
    else:
        return False
    
    # Copiar datos
    buf_array = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 4))
    buf_array[:] = bgra_array
    surface.mark_dirty()
    
    # Crear patrón y aplicar transformación para ajustar al triángulo
    pattern = cairo.SurfacePattern(surface)
    
    # Matriz de transformación para ajustar la textura al triángulo
    matrix = cairo.Matrix()
    
    # Escalar la textura para que se ajuste al tamaño del triángulo
    escala_x = width / ancho_triangulo
    escala_y = height / alto_triangulo
    
    # Trasladar para centrar en el triángulo
    matrix.translate(-min_x * escala_x, -min_y * escala_y)
    matrix.scale(escala_x, escala_y)
    
    pattern.set_matrix(matrix)
    pattern.set_extend(cairo.EXTEND_PAD)  # No repetir, usar padding
    
    # Aplicar patrón
    ctx.set_source(pattern)
    return True

@st.cache_data
def generate_penrose_tiles_with_textures(divisions, resolution, paleta_nombre, accent_pattern, line_width, escala_textura, _texturas_dict):
    """
    Generador Penrose con texturas en lugar de colores sólidos
    """
    
    if paleta_nombre not in PALETAS_TEXTURAS:
        st.error(f"Paleta '{paleta_nombre}' no encontrada")
        return None, {}
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    
    # Verificar texturas disponibles
    texturas_disponibles = []
    for tex_nombre in texturas_paleta:
        if tex_nombre in _texturas_dict:
            texturas_disponibles.append(tex_nombre)
    
    if not texturas_disponibles:
        st.error(f"No hay texturas disponibles para la paleta '{paleta_nombre}'")
        return None, {}
    
    r1, r2 = resolution
    phi = (5 ** 0.5 + 1) / 2
    
    # Configurar Cairo
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, r1, r2)
    ctx = cairo.Context(surface)
    
    # Transformaciones
    scale = min(r1, r2) * 0.4
    ctx.scale(scale, scale)
    ctx.translate(0.5 * r1/scale, 0.5 * r2/scale)
    
    # Fondo blanco
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()
    
    def generate_penrose_rhombi(divisions):
        base = 5
        triangles = []
        
        for i in range(base * 2):
            v2 = cmath.rect(1, (2*i - 1) * math.pi / (base * 2))
            v3 = cmath.rect(1, (2*i + 1) * math.pi / (base * 2))
            
            if i % 2 == 0:
                v2, v3 = v3, v2
            
            triangles.append(("thin", 0+0j, v2, v3))
        
        for iteration in range(divisions):
            new_triangles = []
            
            for shape, v1, v2, v3 in triangles:
                if shape == "thin":
                    p1 = v1 + (v2 - v1) / phi
                    new_triangles.append(("thin", v3, p1, v2))
                    new_triangles.append(("thick", p1, v3, v1))
                else:
                    p2 = v2 + (v1 - v2) / phi
                    p3 = v2 + (v3 - v2) / phi
                    new_triangles.append(("thick", p3, v3, v1))
                    new_triangles.append(("thick", p2, p3, v2))
                    new_triangles.append(("thin", p3, p2, v1))
            
            triangles = new_triangles
        
        return triangles
    
    def should_use_accent_texture(triangle, pattern):
        if pattern is None or pattern == 'Ninguno':
            return False
            
        shape, v1, v2, v3 = triangle
        center = (v1 + v2 + v3) / 3
        distance = abs(center)
        angle = cmath.phase(center) % (2 * math.pi)
        
        if pattern == 'center_star':
            return distance < 0.3
        elif pattern == 'outer_ring':
            return distance > 0.6
        elif pattern == 'radial_bands':
            band_angle = angle * 6 / (2 * math.pi)
            return int(band_angle) % 2 == 0
        elif pattern == 'spiral_arms':
            spiral_angle = (angle + distance * 2 * math.pi) % (2 * math.pi)
            arm_width = 0.4
            arm_spacing = 2 * math.pi / 5
            
            for i in range(5):
                arm_center = i * arm_spacing
                if abs(spiral_angle - arm_center) < arm_width or \
                   abs(spiral_angle - arm_center - 2*math.pi) < arm_width:
                    return distance > 0.2 and distance < 0.8
            return False
        elif pattern == 'diamond_cross':
            x, y = center.real, center.imag
            main_cross = (abs(x) < 0.15 and abs(y) < 0.6) or \
                        (abs(y) < 0.15 and abs(x) < 0.6)
            diagonal_cross = (abs(x - y) < 0.12 and distance < 0.6) or \
                           (abs(x + y) < 0.12 and distance < 0.6)
            return main_cross or diagonal_cross
        elif pattern == 'petal_flower':
            if distance < 0.15 or distance > 0.7:
                return False
            petal_function = math.sin(5 * angle) * 0.3 + 0.4
            petal_tolerance = 0.08
            return abs(distance - petal_function) < petal_tolerance
        elif pattern == 'concentric_rings':
            ring_width = 0.15
            ring_number = int(distance / ring_width)
            return ring_number % 2 == 1
            
        return False
    
    # Función para asignar textura a cada triángulo individual
    def asignar_textura_triangulo(triangle, texturas_disponibles, accent_pattern):
        """Asigna una textura específica a cada triángulo basada en reglas"""
        shape, v1, v2, v3 = triangle
        
        # Verificar si debe usar textura de acento
        if should_use_accent_texture(triangle, accent_pattern) and len(texturas_disponibles) > 2:
            # Usar la tercera textura como acento
            return texturas_disponibles[2]
        
        # Asignación básica por tipo de triángulo
        if shape == "thin":
            return texturas_disponibles[0] if len(texturas_disponibles) > 0 else None
        else:  # thick
            return texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
    
    # Generar triángulos
    triangles = generate_penrose_rhombi(divisions)
    
    # Renderizar cada triángulo individualmente con su textura
    triangulos_renderizados = 0
    errores_renderizado = 0
    
    for triangle in triangles:
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        # Crear path del triángulo
        ctx.move_to(v1.real, v1.imag)
        ctx.line_to(v2.real, v2.imag)
        ctx.line_to(v3.real, v3.imag)
        ctx.close_path()
        
        # Asignar textura específica para este triángulo
        textura_nombre = asignar_textura_triangulo(triangle, texturas_disponibles, accent_pattern)
        textura_info = _texturas_dict.get(textura_nombre) if textura_nombre else None
        
        # Aplicar textura individual
        if textura_info:
            if aplicar_textura_a_triangulo_individual(ctx, vertices, textura_info, escala_textura):
                ctx.fill_preserve()
                triangulos_renderizados += 1
            else:
                # Fallback a color sólido si falla la textura
                if shape == "thin":
                    ctx.set_source_rgb(0.3, 0.7, 0.9)
                else:
                    ctx.set_source_rgb(0.1, 0.4, 0.8)
                ctx.fill_preserve()
                errores_renderizado += 1
        else:
            # Fallback a color sólido si no hay textura
            if shape == "thin":
                ctx.set_source_rgb(0.3, 0.7, 0.9)
            else:
                ctx.set_source_rgb(0.1, 0.4, 0.8)
            ctx.fill_preserve()
            errores_renderizado += 1
        
        # Contorno si se solicita
        if line_width > 0:
            ctx.set_line_width(line_width)
            ctx.set_source_rgb(0.0, 0.0, 0.0)
            ctx.stroke()
        else:
            ctx.new_path()
    
    # Convertir a imagen PIL
    buf = surface.get_data()
    a = np.ndarray(shape=(r2, r1, 4), dtype=np.uint8, buffer=buf)
    a = a[:, :, [2, 1, 0, 3]]  # BGRA -> RGBA
    
    # Convertir a PIL Image
    img = Image.fromarray(a)
    
    # Estadísticas
    thin_count = sum(1 for t in triangles if t[0] == 'thin')
    thick_count = len(triangles) - thin_count
    
    return img, {
        'total_pieces': len(triangles),
        'thin_pieces': thin_count,
        'thick_pieces': thick_count,
        'paleta': paleta_nombre,
        'texturas_usadas': texturas_disponibles,
        'accent_pattern': accent_pattern,
        'escala_textura': escala_textura,
        'resolucion': resolution,  # Solo (ancho, alto)
        'triangulos_con_textura': triangulos_renderizados,
        'errores_renderizado': errores_renderizado,
        'dpi_estimado': resolution[0] / 8,  # Para triángulos de 8cm
        'tamaño_impresion_cm': (resolution[0] / 118, resolution[1] / 118)  # A 300 DPI
    }

def crear_vista_previa_paleta(paleta_nombre, texturas_dict):
    """Crea una vista previa de la paleta seleccionada"""
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    
    # Crear imagen de vista previa
    preview_width = 300
    preview_height = 80
    preview_img = Image.new('RGB', (preview_width, preview_height), 'white')
    
    segment_width = preview_width // len(texturas_paleta)
    
    for i, tex_nombre in enumerate(texturas_paleta):
        if tex_nombre in texturas_dict:
            texture = texturas_dict[tex_nombre]['pil']
            texture_resized = texture.resize((segment_width, preview_height), Image.Resampling.LANCZOS)
            
            # Pegar segmento
            x_pos = i * segment_width
            preview_img.paste(texture_resized, (x_pos, 0))
    
    return preview_img

def generar_mural_rectangular_penrose(ancho_cm, alto_cm, paleta_nombre, accent_pattern, lado_triangulo_cm, _texturas_dict):
    """
    Genera un mural rectangular con teselación Penrose usando patrones simples
    Para visualización arquitectónica y cálculo de materiales
    """
    
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None, {}
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    
    # Verificar texturas disponibles
    texturas_disponibles = [tex for tex in texturas_paleta if tex in _texturas_dict]
    
    if not texturas_disponibles:
        return None, {}
    
    # Calcular resolución para buena calidad (150 DPI para visualización)
    dpi = 150
    px_ancho = int(ancho_cm * dpi / 2.54)
    px_alto = int(alto_cm * dpi / 2.54)
    
    # Crear surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, px_ancho, px_alto)
    ctx = cairo.Context(surface)
    
    # Fondo blanco limpio
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()
    
    # Configurar escalas para que un triángulo de 8cm se vea correcto
    escala_cairo = dpi / 2.54  # conversión cm a píxeles
    ctx.scale(escala_cairo, escala_cairo)
    
    # Centrar el origen en el centro del rectángulo
    ctx.translate(ancho_cm / 2, alto_cm / 2)
    
    # Generar teselación Penrose extendida
    phi = (5 ** 0.5 + 1) / 2
    
    def generate_extended_penrose_rhombi(divisions):
        """Genera teselación Penrose extendida para llenar rectángulo"""
        base = 5
        triangles = []
        
        # Generar múltiples centros para cubrir el área rectangular
        centros_x = range(-2, 3)  # Múltiples centros horizontales
        centros_y = range(-1, 2)  # Múltiples centros verticales
        
        for cx in centros_x:
            for cy in centros_y:
                for i in range(base * 2):
                    v2 = cmath.rect(1, (2*i - 1) * math.pi / (base * 2))
                    v3 = cmath.rect(1, (2*i + 1) * math.pi / (base * 2))
                    
                    if i % 2 == 0:
                        v2, v3 = v3, v2
                    
                    # Desplazar por el centro actual
                    offset = complex(cx * 15, cy * 15)  # Separación entre centros
                    triangles.append(("thin", offset, v2 + offset, v3 + offset))
        
        # Aplicar divisiones
        for iteration in range(divisions):
            new_triangles = []
            
            for shape, v1, v2, v3 in triangles:
                if shape == "thin":
                    p1 = v1 + (v2 - v1) / phi
                    new_triangles.append(("thin", v3, p1, v2))
                    new_triangles.append(("thick", p1, v3, v1))
                else:
                    p2 = v2 + (v1 - v2) / phi
                    p3 = v2 + (v3 - v2) / phi
                    new_triangles.append(("thick", p3, v3, v1))
                    new_triangles.append(("thick", p2, p3, v2))
                    new_triangles.append(("thin", p3, p2, v1))
            
            triangles = new_triangles
        
        return triangles
    
    def should_use_accent_pattern_rectangular(triangle, pattern, ancho_cm, alto_cm):
        """Determina si usar patrón de acento centrado en el rectángulo"""
        if pattern is None or pattern == 'Ninguno':
            return False
            
        shape, v1, v2, v3 = triangle
        center = (v1 + v2 + v3) / 3
        
        # Convertir a coordenadas del rectángulo (centro = 0,0)
        x_rel = center.real / (ancho_cm / 2)  # Normalizar a [-1, 1]
        y_rel = center.imag / (alto_cm / 2)   # Normalizar a [-1, 1]
        distance_from_center = math.sqrt(x_rel**2 + y_rel**2)
        
        if pattern == 'center_star':
            return distance_from_center < 0.3
        elif pattern == 'outer_ring':
            return distance_from_center > 0.6 and distance_from_center < 0.8
        elif pattern == 'radial_bands':
            angle = cmath.phase(center) % (2 * math.pi)
            band_angle = angle * 6 / (2 * math.pi)
            return int(band_angle) % 2 == 0 and distance_from_center < 0.7
        
        return False
    
    def esta_dentro_rectangulo(triangle, ancho_cm, alto_cm):
        """Verifica si el triángulo está dentro del rectángulo"""
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        for v in vertices:
            x, y = v.real, v.imag
            if (abs(x) <= ancho_cm / 2 and abs(y) <= alto_cm / 2):
                return True
        
        return False
    
    def recortar_triangulo_a_rectangulo(triangle, ancho_cm, alto_cm):
        """Recorta triángulo a los límites del rectángulo"""
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        # Verificar qué vértices están dentro
        vertices_dentro = []
        for v in vertices:
            x, y = v.real, v.imag
            if (abs(x) <= ancho_cm / 2 and abs(y) <= alto_cm / 2):
                vertices_dentro.append(v)
        
        # Si al menos un vértice está dentro, incluir el triángulo
        if len(vertices_dentro) >= 1:
            return (shape, v1, v2, v3)
        
        return None
    
    def get_pattern_style(texture_name, triangle_type):
        """Define estilos de patrón simple para cada textura"""
        patterns = {
            'azul': ('solid', (0.2, 0.4, 0.8)),
            'verde': ('dots', (0.2, 0.6, 0.3)),
            'rosa': ('lines_h', (0.9, 0.3, 0.5)),
            'amarillo': ('solid', (0.9, 0.8, 0.2)),
            'naranja': ('lines_v', (1.0, 0.5, 0.1)),
            'gris 1': ('dots', (0.5, 0.5, 0.5)),
            'gris2': ('solid', (0.3, 0.3, 0.3)),
            'blanco1': ('solid', (0.95, 0.95, 0.95)),
            'blanco2': ('dots', (0.9, 0.9, 0.9)),
            'blanco 3': ('lines_h', (0.85, 0.85, 0.85)),
            'blanco 4': ('lines_v', (0.8, 0.8, 0.8)),
            'PERU': ('lines_d', (0.8, 0.6, 0.4))
        }
        
        return patterns.get(texture_name, ('solid', (0.7, 0.7, 0.7)))
    
    def draw_pattern_in_triangle(ctx, vertices, pattern_style, color):
        """Dibuja patrón simple dentro del triángulo"""
        style, rgb = pattern_style, color
        
        # Crear path del triángulo
        ctx.move_to(vertices[0].real, vertices[0].imag)
        ctx.line_to(vertices[1].real, vertices[1].imag)
        ctx.line_to(vertices[2].real, vertices[2].imag)
        ctx.close_path()
        
        if style == 'solid':
            ctx.set_source_rgb(*rgb)
            ctx.fill_preserve()
        
        elif style == 'dots':
            # Fondo sólido más claro
            ctx.set_source_rgb(rgb[0] + 0.3, rgb[1] + 0.3, rgb[2] + 0.3)
            ctx.fill_preserve()
            
            # Clip al triángulo para los puntos
            ctx.clip_preserve()
            
            # Dibujar puntos
            xs = [v.real for v in vertices]
            ys = [v.imag for v in vertices]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            ctx.set_source_rgb(*rgb)
            spacing = 0.5  # Espaciado entre puntos en cm
            
            x = min_x
            while x <= max_x:
                y = min_y
                while y <= max_y:
                    ctx.arc(x, y, 0.1, 0, 2 * math.pi)
                    ctx.fill()
                    y += spacing
                x += spacing
            
            ctx.reset_clip()
        
        elif style == 'lines_h':
            # Fondo sólido más claro
            ctx.set_source_rgb(rgb[0] + 0.2, rgb[1] + 0.2, rgb[2] + 0.2)
            ctx.fill_preserve()
            
            # Clip al triángulo
            ctx.clip_preserve()
            
            # Líneas horizontales
            ys = [v.imag for v in vertices]
            min_y, max_y = min(ys), max(ys)
            
            ctx.set_source_rgb(*rgb)
            ctx.set_line_width(0.1)
            spacing = 0.4
            
            y = min_y
            while y <= max_y:
                ctx.move_to(-ancho_cm, y)
                ctx.line_to(ancho_cm, y)
                ctx.stroke()
                y += spacing
            
            ctx.reset_clip()
        
        elif style == 'lines_v':
            # Fondo sólido más claro
            ctx.set_source_rgb(rgb[0] + 0.2, rgb[1] + 0.2, rgb[2] + 0.2)
            ctx.fill_preserve()
            
            # Clip al triángulo
            ctx.clip_preserve()
            
            # Líneas verticales
            xs = [v.real for v in vertices]
            min_x, max_x = min(xs), max(xs)
            
            ctx.set_source_rgb(*rgb)
            ctx.set_line_width(0.1)
            spacing = 0.4
            
            x = min_x
            while x <= max_x:
                ctx.move_to(x, -alto_cm)
                ctx.line_to(x, alto_cm)
                ctx.stroke()
                x += spacing
            
            ctx.reset_clip()
        
        elif style == 'lines_d':
            # Fondo sólido más claro
            ctx.set_source_rgb(rgb[0] + 0.2, rgb[1] + 0.2, rgb[2] + 0.2)
            ctx.fill_preserve()
            
            # Clip al triángulo
            ctx.clip_preserve()
            
            # Líneas diagonales
            ctx.set_source_rgb(*rgb)
            ctx.set_line_width(0.1)
            spacing = 0.4
            
            for i in range(-50, 51):
                y_start = i * spacing
                ctx.move_to(-ancho_cm, y_start - ancho_cm)
                ctx.line_to(ancho_cm, y_start + ancho_cm)
                ctx.stroke()
            
            ctx.reset_clip()
    
    # Generar triángulos
    triangles = generate_extended_penrose_rhombi(6)  # Divisiones fijas para buena densidad
    
    # Filtrar triángulos que están dentro o intersectan el rectángulo
    triangles_filtrados = []
    for triangle in triangles:
        if esta_dentro_rectangulo(triangle, ancho_cm, alto_cm):
            triangle_recortado = recortar_triangulo_a_rectangulo(triangle, ancho_cm, alto_cm)
            if triangle_recortado:
                triangles_filtrados.append(triangle_recortado)
    
    # Contadores para materiales
    contadores = {
        'thin': {},
        'thick': {},
        'accent': {}
    }
    
    for tex_name in texturas_disponibles:
        contadores['thin'][tex_name] = 0
        contadores['thick'][tex_name] = 0
        contadores['accent'][tex_name] = 0
    
    # Renderizar triángulos
    for triangle in triangles_filtrados:
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        # Determinar textura y tipo
        if should_use_accent_pattern_rectangular(triangle, accent_pattern, ancho_cm, alto_cm):
            texture_name = texturas_disponibles[2] if len(texturas_disponibles) > 2 else texturas_disponibles[0]
            contadores['accent'][texture_name] += 1
        elif shape == "thin":
            texture_name = texturas_disponibles[0] if len(texturas_disponibles) > 0 else None
            contadores['thin'][texture_name] += 1
        else:  # thick
            texture_name = texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
            contadores['thick'][texture_name] += 1
        
        # Obtener estilo de patrón
        pattern_style = get_pattern_style(texture_name, shape)
        
        # Dibujar triángulo con patrón
        draw_pattern_in_triangle(ctx, vertices, pattern_style, pattern_style[1])
        
        # Contorno negro
        ctx.move_to(v1.real, v1.imag)
        ctx.line_to(v2.real, v2.imag)
        ctx.line_to(v3.real, v3.imag)
        ctx.close_path()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(0.05)
        ctx.stroke()
    
    # Dibujar borde del rectángulo
    ctx.rectangle(-ancho_cm/2, -alto_cm/2, ancho_cm, alto_cm)
    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_line_width(0.2)
    ctx.stroke()
    
    # Convertir a imagen PIL
    buf = surface.get_data()
    a = np.ndarray(shape=(px_alto, px_ancho, 4), dtype=np.uint8, buffer=buf)
    a = a[:, :, [2, 1, 0, 3]]  # BGRA -> RGBA
    
    img = Image.fromarray(a)
    
    # Calcular totales
    total_triangulos = sum(sum(categoria.values()) for categoria in contadores.values())
    
    return img, {
        'dimensiones_cm': (ancho_cm, alto_cm),
        'dimensiones_px': (px_ancho, px_alto),
        'total_triangulos': total_triangulos,
        'contadores': contadores,
        'paleta': paleta_nombre,
        'texturas_usadas': texturas_disponibles,
        'accent_pattern': accent_pattern,
        'lado_triangulo_cm': lado_triangulo_cm,
        'dpi': dpi
    }
    """Crea una vista previa de la paleta seleccionada"""
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    
    # Crear imagen de vista previa
    preview_width = 300
    preview_height = 80
    preview_img = Image.new('RGB', (preview_width, preview_height), 'white')
    
    segment_width = preview_width // len(texturas_paleta)
    
    for i, tex_nombre in enumerate(texturas_paleta):
        if tex_nombre in texturas_dict:
            texture = texturas_dict[tex_nombre]['pil']
            texture_resized = texture.resize((segment_width, preview_height), Image.Resampling.LANCZOS)
            
            # Pegar segmento
            x_pos = i * segment_width
            preview_img.paste(texture_resized, (x_pos, 0))
    
    return preview_img

def create_download_link(img, filename):
    """Crea un link de descarga para la imagen"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 Descargar {filename}</a>'
    return href

def main():
    # PARCHE DE SEGURIDAD GLOBAL - Evitar KeyError area_m2
    def patch_stats_seguro(stats_dict):
        """Asegura que stats tenga todas las claves necesarias"""
        if isinstance(stats_dict, dict):
            if 'area_m2' not in stats_dict and 'dimensiones_cm' in stats_dict:
                ancho, alto = stats_dict['dimensiones_cm']
                stats_dict['area_m2'] = (ancho * alto) / 10000
            if 'dpi' not in stats_dict:
                stats_dict['dpi'] = 'Auto'
        return stats_dict
    
    # Aplicar parche a todos los stats en session_state
    for key in st.session_state:
        if 'stats' in key and isinstance(st.session_state[key], dict):
            st.session_state[key] = patch_stats_seguro(st.session_state[key])
    
    # Header principal
    st.markdown("""
        <div class="main-header">
            <h1>🎨 Generador de Mosaicos Penrose con Texturas</h1>
            <p>Crea hermosos azulejos geométricos usando patrones de texturas basados en teoría del color</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Cargar texturas
    with st.spinner('🔄 Cargando texturas...'):
        texturas_dict, texturas_encontradas, texturas_faltantes = cargar_texturas_streamlit()
    
    # Mostrar estado de carga de texturas
    if texturas_encontradas:
        st.success(f"✅ Texturas cargadas: {len(texturas_encontradas)}")
        with st.expander("Ver texturas disponibles"):
            cols = st.columns(4)
            for i, tex_nombre in enumerate(texturas_encontradas[:8]):  # Mostrar máximo 8
                with cols[i % 4]:
                    nombre_limpio = tex_nombre.replace('.png', '')
                    if nombre_limpio in texturas_dict:
                        st.image(texturas_dict[nombre_limpio]['pil'], caption=nombre_limpio, width=100)
    
    if texturas_faltantes:
        st.warning(f"⚠️ Texturas no encontradas: {len(texturas_faltantes)}")
        with st.expander("Ver texturas faltantes"):
            for tex in texturas_faltantes:
                st.text(f"• {tex}")
    
    # Sidebar con información de paletas
    st.sidebar.markdown("## 🎨 Paletas de Color Disponibles")
    
    for nombre, info in PALETAS_TEXTURAS.items():
        with st.sidebar.expander(f"{info['descripcion']}"):
            st.write(f"**Teoría:** {info['teoria']}")
            st.write(f"**Texturas:** {', '.join(info['texturas'])}")
            
            # Verificar disponibilidad
            disponibles = [tex for tex in info['texturas'] if tex in texturas_dict]
            if disponibles:
                st.success(f"✅ {len(disponibles)}/{len(info['texturas'])} disponibles")
            else:
                st.error("❌ No hay texturas disponibles")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎨 Generador con Texturas", "🏗️ Configuración Murales", "📐 Mural Rectangular", "🔬 Análisis de Paletas", "📚 Galería de Patrones"])
    
    with tab1:
        st.markdown("### 🎯 Generación con Texturas")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 🎨 Configuración")
            
            # Selección de paleta
            paleta_seleccionada = st.selectbox(
                "🌈 Paleta de Texturas:",
                list(PALETAS_TEXTURAS.keys()),
                help="Selecciona una paleta basada en teoría del color"
            )
            
            # Vista previa de paleta
            if paleta_seleccionada:
                preview_img = crear_vista_previa_paleta(paleta_seleccionada, texturas_dict)
                if preview_img:
                    st.image(preview_img, caption=f"Vista previa: {paleta_seleccionada}", use_container_width=True)
                
                # Información de la paleta
                paleta_info = PALETAS_TEXTURAS[paleta_seleccionada]
                st.markdown(f"""
                    <div class="texture-info">
                        <strong>{paleta_info['descripcion']}</strong><br>
                        <em>{paleta_info['teoria']}</em>
                    </div>
                """, unsafe_allow_html=True)
            
            accent_pattern = st.selectbox(
                "✨ Patrón de Acento:",
                ['Ninguno', 'center_star', 'outer_ring', 'radial_bands', 'spiral_arms', 
                 'diamond_cross', 'petal_flower', 'concentric_rings'],
                help="Agrega elementos especiales al diseño"
            )
            
            divisions = st.slider(
                "🔢 Subdivisiones:",
                min_value=4, max_value=7, value=6,
                help="Más divisiones = más detalle (pero tarda más)"
            )
            
            line_width = st.slider(
                "🖊️ Grosor de Líneas:",
                min_value=0.0, max_value=0.01, value=0.002, step=0.001,
                format="%.3f",
                help="0.0 = sin líneas, 0.01 = líneas gruesas"
            )
            
            resolution = st.selectbox(
                "📐 Resolución:",
                [
                    (800, 800, "Vista previa"),
                    (1600, 1600, "Alta calidad"),
                    (2400, 2400, "Impresión básica"),
                    (3600, 3600, "Impresión profesional"),
                    (4800, 4800, "Mural pequeño"),
                    (7200, 7200, "Mural grande")
                ],
                index=2,
                format_func=lambda x: f"{x[0]}x{x[1]} px - {x[2]}"
            )
            
            # Control de escala de textura para murales
            escala_textura = st.slider(
                "🔍 Detalle de Textura por Triángulo:",
                min_value=1.0, max_value=4.0, value=2.5, step=0.1,
                help="Controla cuánto detalle de textura se ve en cada triángulo individual. Más alto = más detalle visible por pieza."
            )
            
            # Información específica para murales
            st.markdown("""
                <div class="texture-info">
                    <strong>💡 Nuevo Sistema de Texturas:</strong><br>
                    • Cada triángulo tiene su propia textura individual<br>
                    • No hay continuidad entre piezas (como mosaico real)<br>
                    • Cada pieza es independiente para corte e impresión<br>
                    • Escala 2.0+ para texturas bien visibles en triángulos de 8cm
                </div>
            """, unsafe_allow_html=True)
            
            generate_btn = st.button("🎨 Generar Mosaico con Texturas", type="primary")
        
        with col2:
            if generate_btn and texturas_dict:
                with st.spinner('🔄 Generando mosaico con texturas...'):
                    accent = accent_pattern if accent_pattern != 'Ninguno' else None
                    # Extraer información completa de la resolución
                    res_dims = (resolution[0], resolution[1])
                    res_tipo = resolution[2]
                    img, stats = generate_penrose_tiles_with_textures(
                        divisions, res_dims, paleta_seleccionada, accent, line_width, escala_textura, texturas_dict
                    )
                    
                    # Agregar información del tipo de resolución al stats
                    stats['tipo_resolucion'] = res_tipo
                    
                    if img:
                        st.markdown("#### 🖼️ Mosaico Generado")
                        
                        # Controles de visualización
                        col_view1, col_view2 = st.columns(2)
                        with col_view1:
                            zoom_level = st.selectbox(
                                "🔍 Nivel de Zoom:",
                                [("100%", 1.0), ("150%", 1.5), ("200%", 2.0), ("300%", 3.0)],
                                format_func=lambda x: x[0]
                            )
                        with col_view2:
                            mostrar_info_resolucion = st.checkbox("📊 Mostrar info de resolución", value=True)
                        
                        # Calcular tamaño de visualización
                        display_width = int(800 * zoom_level[1])  # Ancho base escalado
                        
                        # Mostrar imagen con zoom
                        st.image(img, 
                                caption=f"Mosaico Penrose - Paleta {paleta_seleccionada} | Resolución: {resolution[0]}x{resolution[1]} | Escala: {escala_textura}x", 
                                width=display_width)
                        
                        # Información adicional de resolución
                        if mostrar_info_resolucion:
                            st.info(f"""
                            **Información de Resolución:**
                            • Imagen generada: {resolution[0]} x {resolution[1]} píxeles
                            • Tipo: {stats.get('tipo_resolucion', 'Personalizada')}
                            • Detalle por triángulo: {escala_textura}x
                            • Cada triángulo: pieza independiente con textura completa
                            • Para triángulos de 8cm: {resolution[0]/90:.1f} x {resolution[1]/90:.1f} cm a 300 DPI
                            """)
                        
                        # Botón para generar vista de detalle
                        if st.button("🔍 Generar Vista de Detalle (Zoom Región Central)"):
                            with st.spinner('Generando vista de detalle...'):
                                # Crear una versión recortada del centro para mostrar detalle
                                center_crop = img.crop((
                                    resolution[0]//4, resolution[1]//4,
                                    3*resolution[0]//4, 3*resolution[1]//4
                                ))
                                st.image(center_crop, 
                                        caption="Vista de detalle - Región central", 
                                        use_container_width=True)
                                
                                # Análisis de la textura en detalle
                                st.write("**🔬 En esta vista puedes ver:**")
                                st.write("• Cada triángulo tiene su textura independiente")
                                st.write("• Los bordes definen cada pieza del mosaico") 
                                st.write("• La calidad de textura dentro de cada triángulo")
                                st.write("• Cómo se verá cada pieza al cortarla individualmente")
                        
                        # Estadísticas mejoradas
                        st.markdown("#### 📊 Estadísticas del Mosaico")
                        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                        
                        with col_stats1:
                            st.metric("Total Piezas", stats['total_pieces'])
                        with col_stats2:
                            st.metric("Triángulos Delgados", stats['thin_pieces'])
                        with col_stats3:
                            st.metric("Triángulos Gruesos", stats['thick_pieces'])
                        with col_stats4:
                            texturizados = stats.get('triangulos_con_textura', 0)
                            porcentaje = (texturizados / stats['total_pieces'] * 100) if stats['total_pieces'] > 0 else 0
                            st.metric("Con Textura", f"{texturizados} ({porcentaje:.1f}%)")
                        
                        # Alerta de calidad si hay errores
                        errores = stats.get('errores_renderizado', 0)
                        if errores > 0:
                            st.warning(f"⚠️ {errores} triángulos usaron color sólido por problemas de textura")
                        else:
                            st.success("✅ Todas las texturas se aplicaron correctamente")
                        
                        # Información específica para murales
                        st.markdown("#### 🏗️ Información para Mural")
                        col_mural1, col_mural2 = st.columns(2)
                        
                        with col_mural1:
                            tamaño_impresion = stats['tamaño_impresion_cm']
                            st.write(f"**Tamaño de impresión (300 DPI):**")
                            st.write(f"{tamaño_impresion[0]:.1f} x {tamaño_impresion[1]:.1f} cm")
                            st.write(f"**Triángulos independientes:** {stats['total_pieces']} piezas")
                            st.write(f"**Cada pieza:** 8cm con textura completa")
                        
                        with col_mural2:
                            st.write(f"**Resolución:** {stats['resolucion'][0]} x {stats['resolucion'][1]} px")
                            st.write(f"**Tipo:** {stats.get('tipo_resolucion', 'Personalizada')}")
                            st.write(f"**DPI recomendado:** 300 DPI para impresión")
                        
                        # Información de texturas usadas
                        st.markdown("#### 🎨 Texturas Aplicadas")
                        st.write(f"**Paleta:** {stats['paleta']}")
                        st.write(f"**Texturas usadas:** {', '.join(stats['texturas_usadas'])}")
                        
                        # Botón de descarga
                        filename = f"penrose_texturas_{paleta_seleccionada}_{accent_pattern}_{divisions}div_{resolution[0]}x{resolution[1]}.png"
                        download_link = create_download_link(img, filename)
                        st.markdown(download_link, unsafe_allow_html=True)
                        
                        # Guardar en session state
                        st.session_state['last_texture_image'] = img
                        st.session_state['last_texture_stats'] = stats
                        st.session_state['last_texture_filename'] = filename
            
            elif 'last_texture_image' in st.session_state:
                st.markdown("#### 🖼️ Último Mosaico Generado")
                st.image(st.session_state['last_texture_image'], use_container_width=True)
                
                if 'last_texture_stats' in st.session_state:
                    stats = st.session_state['last_texture_stats']
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    
                    with col_stats1:
                        st.metric("Total Piezas", stats['total_pieces'])
                    with col_stats2:
                        st.metric("Triángulos Delgados", stats['thin_pieces'])
                    with col_stats3:
                        st.metric("Triángulos Gruesos", stats['thick_pieces'])
                
                if 'last_texture_filename' in st.session_state:
                    download_link = create_download_link(
                        st.session_state['last_texture_image'], 
                        st.session_state['last_texture_filename']
                    )
                    st.markdown(download_link, unsafe_allow_html=True)
            
            elif not texturas_dict:
                st.error("❌ No hay texturas disponibles. Asegúrate de que los archivos PNG estén en el directorio.")
    
    with tab2:
        st.markdown("### 🏗️ Configuración Especializada para Murales")
        
        if texturas_dict:
            st.markdown("""
                <div class="texture-info">
                    <h4>🎯 Guía para Murales de Triángulos de 8cm</h4>
                    <p>Esta sección te ayuda a configurar el mosaico perfecto para impresión en gran formato.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Calculadora de tamaño de mural
            st.markdown("#### 📐 Calculadora de Tamaño de Mural")
            
            col_calc1, col_calc2 = st.columns(2)
            
            with col_calc1:
                ancho_mural_cm = st.number_input(
                    "Ancho del mural (cm):",
                    min_value=50, max_value=500, value=120, step=10
                )
                
                alto_mural_cm = st.number_input(
                    "Alto del mural (cm):",
                    min_value=50, max_value=500, value=120, step=10
                )
                
                dpi_impresion = st.selectbox(
                    "Calidad de impresión:",
                    [(150, "Borrador rápido"), (300, "Calidad estándar"), (600, "Alta calidad")],
                    index=1,
                    format_func=lambda x: f"{x[0]} DPI - {x[1]}"
                )
            
            with col_calc2:
                # Calcular resolución recomendada
                px_ancho = int(ancho_mural_cm * dpi_impresion[0] / 2.54)
                px_alto = int(alto_mural_cm * dpi_impresion[0] / 2.54)
                
                st.markdown(f"""
                    **📊 Resolución Recomendada:**
                    - **{px_ancho} x {px_alto} píxeles**
                    - Tamaño de archivo estimado: {(px_ancho * px_alto * 3 / 1024 / 1024):.1f} MB
                    - Triángulos de 8cm cada uno
                    - Aproximadamente {int((ancho_mural_cm * alto_mural_cm) / 64)} triángulos
                """)
                
                # Escala de textura recomendada
                triangulos_por_textura = max(1, int(px_ancho / 800))  # Estimación
                escala_recomendada = max(1.0, min(5.0, triangulos_por_textura * 0.5))
                
                st.markdown(f"""
                    **🔍 Configuración Recomendada:**
                    - Escala de textura: **{escala_recomendada:.1f}x**
                    - Subdivisiones: **6-7** (para buena definición)
                    - Grosor de líneas: **0.001-0.003**
                """)
            
            # Generador específico para murales
            st.markdown("#### 🎨 Generador Optimizado para Murales")
            
            col_mural1, col_mural2 = st.columns([1, 2])
            
            with col_mural1:
                mural_paleta = st.selectbox(
                    "🌈 Paleta para Mural:",
                    list(PALETAS_TEXTURAS.keys()),
                    help="Paletas optimizadas para gran formato"
                )
                
                usar_resolucion_calculada = st.checkbox(
                    "Usar resolución calculada",
                    value=True,
                    help="Usa la resolución calculada arriba"
                )
                
                if not usar_resolucion_calculada:
                    mural_resolution = st.selectbox(
                        "Resolución personalizada:",
                        [
                            (2400, 2400, "Mural pequeño"),
                            (3600, 3600, "Mural mediano"),
                            (4800, 4800, "Mural grande"),
                            (7200, 7200, "Mural extra grande")
                        ],
                        format_func=lambda x: f"{x[0]}x{x[1]} - {x[2]}"
                    )
                else:
                    mural_resolution = (px_ancho, px_alto, "Calculado")
                
                mural_escala = st.slider(
                    "🔍 Escala de textura:",
                    min_value=1.0, max_value=5.0, 
                    value=escala_recomendada, step=0.1
                )
                
                mural_divisions = st.slider(
                    "🔢 Subdivisiones:",
                    min_value=5, max_value=8, value=6
                )
                
                if st.button("🏗️ Generar Mural", type="primary"):
                    if mural_resolution[0] > 5000 or mural_resolution[1] > 5000:
                        st.warning("⚠️ Resolución muy alta. La generación puede tardar varios minutos.")
                    
                    with st.spinner('🔄 Generando mural de alta resolución...'):
                        try:
                            res_dims = (mural_resolution[0], mural_resolution[1])
                            img_mural, stats_mural = generate_penrose_tiles_with_textures(
                                mural_divisions, res_dims, mural_paleta, None, 0.002, mural_escala, texturas_dict
                            )
                            
                            if img_mural:
                                # Mostrar información de la versión de alta resolución - CORREGIDO COMPLETAMENTE
                                area_hires_segura = calcular_area_segura(stats_mural)
                                dpi_hires_seguro = obtener_dpi_seguro(stats_mural)
                                
                                st.success("✅ Mural generado exitosamente!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error generando mural: {str(e)}")
                            st.info("💡 Intenta con una resolución menor o contacta soporte.")
            
            with col_mural2:
                if 'mural_image' in st.session_state:
                    img_mural = st.session_state['mural_image']
                    stats_mural = st.session_state['mural_stats']
                    
                    st.markdown("#### 🖼️ Mural Generado")
                    
                    # Vista previa redimensionada
                    preview_img = img_mural.copy()
                    preview_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    
                    st.image(preview_img, 
                            caption=f"Vista previa del mural - Resolución original: {img_mural.size[0]}x{img_mural.size[1]}", 
                            use_container_width=True)
                    
                    # Estadísticas del mural
                    st.markdown("#### 📊 Especificaciones del Mural")
                    
                    col_spec1, col_spec2 = st.columns(2)
                    
                    with col_spec1:
                        st.metric("Resolución", f"{img_mural.size[0]}x{img_mural.size[1]} px")
                        st.metric("Total Triángulos", stats_mural['total_pieces'])
                        st.metric("Tamaño Archivo", f"{(img_mural.size[0] * img_mural.size[1] * 3 / 1024 / 1024):.1f} MB")
                    
                    with col_spec2:
                        area_mural_segura = calcular_area_segura(stats_mural)
                        dpi_mural_seguro = obtener_dpi_seguro(stats_mural)
                        
                        st.metric("Escala Textura", f"{stats_mural.get('escala_textura', 'N/A')}x")
                        st.metric("Tamaño Impresión", f"{ancho_mural_cm}x{alto_mural_cm} cm")
                        st.metric("DPI", f"{dpi_impresion[0]} DPI")
                    
                    # Descargas en diferentes formatos
                    st.markdown("#### 📥 Descargas Disponibles")
                    
                    # Descarga principal
                    filename_mural = f"mural_penrose_{mural_paleta}_{img_mural.size[0]}x{img_mural.size[1]}.png"
                    download_link_mural = create_download_link(img_mural, filename_mural)
                    st.markdown(download_link_mural, unsafe_allow_html=True)
                    
                    # Vista de detalle adicional
                    if st.button("🔍 Generar Vista de Detalle del Mural"):
                        # Recorte del centro para mostrar detalle
                        w, h = img_mural.size
                        detail_crop = img_mural.crop((w//3, h//3, 2*w//3, 2*h//3))
                        
                        st.image(detail_crop, 
                                caption="Vista de detalle - Región central del mural", 
                                use_container_width=True)
                        
                        # Información sobre calidad de impresión
                        st.info("""
                        **🔬 Análisis de Calidad:**
                        • En esta vista puedes evaluar la nitidez de las texturas
                        • Verifica que los detalles se vean claramente
                        • Esta calidad se mantendrá en la impresión final
                        """)
                else:
                    st.markdown("""
                        <div class="pattern-preview">
                            <h4>🎯 Configuración Lista</h4>
                            <p>Haz clic en "Generar Mural" para crear tu mosaico optimizado</p>
                            <p><strong>Configuración actual:</strong></p>
                            <ul>
                                <li>Tamaño: """ + f"{ancho_mural_cm}x{alto_mural_cm} cm" + """</li>
                                <li>Resolución: """ + f"{px_ancho}x{px_alto} px" + """</li>
                                <li>Calidad: """ + f"{dpi_impresion[0]} DPI" + """</li>
                            </ul>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("❌ No hay texturas disponibles para configurar murales")

    with tab5:
        st.markdown("### 🔬 Análisis de Paletas de Color")
        
        if texturas_dict:
            # Comparación de paletas
            st.markdown("#### 🎨 Comparación de Paletas")
            
            paletas_seleccionadas = st.multiselect(
                "Selecciona paletas para comparar:",
                list(PALETAS_TEXTURAS.keys()),
                default=['Fuego', 'Océano', 'Contraste']
            )
            
            if paletas_seleccionadas:
                cols = st.columns(len(paletas_seleccionadas))
                
                for i, paleta in enumerate(paletas_seleccionadas):
                    with cols[i]:
                        preview_img = crear_vista_previa_paleta(paleta, texturas_dict)
                        if preview_img:
                            st.image(preview_img, caption=paleta, use_container_width=True)
                        
                        info = PALETAS_TEXTURAS[paleta]
                        st.write(f"**{info['descripcion']}**")
                        st.write(f"*{info['teoria']}*")
                        
                        # Texturas disponibles
                        disponibles = [tex for tex in info['texturas'] if tex in texturas_dict]
                        st.write(f"📊 {len(disponibles)}/{len(info['texturas'])} texturas disponibles")
            
            # Análisis individual de texturas
            st.markdown("#### 🔍 Análisis Individual de Texturas")
            
            textura_analizar = st.selectbox(
                "Selecciona textura para analizar:",
                list(texturas_dict.keys())
            )
            
            if textura_analizar:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.image(texturas_dict[textura_analizar]['pil'], caption=textura_analizar, use_container_width=True)
                
                with col2:
                    info = texturas_dict[textura_analizar]
                    st.write(f"**Tamaño:** {info['size']} píxeles")
                    st.write(f"**Forma del array:** {info['array'].shape}")
                    
                    # Encontrar en qué paletas aparece
                    paletas_que_contienen = []
                    for nombre_paleta, paleta_info in PALETAS_TEXTURAS.items():
                        if textura_analizar in paleta_info['texturas']:
                            paletas_que_contienen.append(nombre_paleta)
                    
                    if paletas_que_contienen:
                        st.write(f"**Aparece en paletas:** {', '.join(paletas_que_contienen)}")
                    else:
                        st.write("**No aparece en ninguna paleta definida**")
        else:
            st.error("❌ No hay texturas cargadas para analizar")
    
    with tab3:
        st.markdown("### 📐 Mural Rectangular - Visualización Arquitectónica")
        
        if texturas_dict:
            st.markdown("""
                <div class="texture-info">
                    <h4>🏗️ Generador para Murales Rectangulares</h4>
                    <p>Sistema optimizado para visualización arquitectónica y cálculo de materiales.</p>
                    <p><strong>Características:</strong> Patrones simples, exportable a gran formato, lista de materiales incluida.</p>
                    <p><strong>⚠️ Importante:</strong> El sistema optimiza automáticamente la resolución para prevenir archivos excesivos. Para murales grandes use múltiples resoluciones según necesidad.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Configuración del mural rectangular
            st.markdown("#### 📏 Dimensiones del Mural")
            
            col_dim1, col_dim2 = st.columns(2)
            
            with col_dim1:
                # Dimensiones predefinidas o personalizadas
                tipo_pared = st.selectbox(
                    "Tipo de pared:",
                    [
                        ("Estándar", 240, 388),  # 2.4m x 3.88m (áureo)
                        ("Pared alta", 300, 485),  # 3.0m x 4.85m (áureo)
                        ("Pared baja", 200, 324),  # 2.0m x 3.24m (áureo)
                        ("Personalizada", 0, 0)
                    ],
                    format_func=lambda x: f"{x[0]} ({x[1]/100:.1f}m x {x[2]/100:.1f}m)" if x[1] > 0 else x[0]
                )
                
                if tipo_pared[0] == "Personalizada":
                    alto_mural = st.number_input(
                        "Alto del mural (cm):",
                        min_value=100, max_value=350, value=240, step=10,
                        help="Máximo 350cm para evitar archivos excesivos"
                    )
                    
                    usar_proporcion_aurea = st.checkbox(
                        "Usar proporción áurea (1:1.618)",
                        value=True
                    )
                    
                    if usar_proporcion_aurea:
                        ancho_mural = int(alto_mural * 1.61803399)
                        if ancho_mural > 500:
                            st.warning(f"⚠️ Ancho calculado ({ancho_mural}cm) es muy grande. Considera reducir la altura.")
                            ancho_mural = min(500, ancho_mural)
                        st.info(f"Ancho calculado: {ancho_mural} cm")
                    else:
                        ancho_mural = st.number_input(
                            "Ancho del mural (cm):",
                            min_value=100, max_value=500, value=388, step=10,
                            help="Máximo 500cm para evitar archivos excesivos"
                        )
                else:
                    alto_mural = tipo_pared[1]
                    ancho_mural = tipo_pared[2]
                
                # Verificación de límites
                area_total = ancho_mural * alto_mural
                if area_total > 150000:  # 15 m²
                    st.error("❌ Área muy grande (>15m²). Reduce las dimensiones para evitar problemas de memoria.")
                    st.stop()
                elif area_total > 100000:  # 10 m²
                    st.warning("⚠️ Área grande (>10m²). La generación puede tardar varios minutos.")
                
                lado_triangulo = st.number_input(
                    "Lado mayor del triángulo (cm):",
                    min_value=5, max_value=15, value=8, step=1,
                    help="Tamaño de la pieza física más grande"
                )
            
            with col_dim2:
                # Información calculada con advertencias de rendimiento
                area_m2 = (ancho_mural * alto_mural) / 10000
                triangulos_estimados = int(area_m2 * 100)  # Estimación aproximada
                
                # Código de color para rendimiento
                if area_m2 > 10:
                    performance_color = "🔴"
                    performance_text = "Muy lento"
                elif area_m2 > 5:
                    performance_color = "🟡"
                    performance_text = "Lento"
                else:
                    performance_color = "🟢"
                    performance_text = "Rápido"
                
                st.markdown(f"""
                    **📊 Información del Mural:**
                    - **Dimensiones:** {ancho_mural} × {alto_mural} cm
                    - **Área total:** {area_m2:.2f} m²
                    - **Proporción:** {ancho_mural/alto_mural:.3f} (áureo = 1.618)
                    - **Triángulo base:** {lado_triangulo} cm
                    
                    **🎯 Estimación:**
                    - ~{triangulos_estimados} triángulos
                    - Tiempo colocación: ~{int(triangulos_estimados / 50)} horas
                    - Rendimiento: {performance_color} {performance_text}
                """)
                
                if area_m2 > 8:
                    st.info("💡 Para murales grandes, considera usar resoluciones más bajas o dividir en secciones.")
            
            # Configuración de diseño
            st.markdown("#### 🎨 Configuración de Diseño")
            
            col_design1, col_design2 = st.columns(2)
            
            with col_design1:
                mural_paleta = st.selectbox(
                    "🌈 Paleta de colores:",
                    list(PALETAS_TEXTURAS.keys()),
                    help="Paleta basada en teoría del color"
                )
                
                mural_accent = st.selectbox(
                    "✨ Patrón de acento:",
                    ['Ninguno', 'center_star', 'outer_ring', 'radial_bands'],
                    help="Patrón especial en el centro del mural"
                )
            
            with col_design2:
                # Vista previa de patrones
                st.markdown("**🎨 Patrones que se usarán:**")
                if mural_paleta in PALETAS_TEXTURAS:
                    texturas_mural = PALETAS_TEXTURAS[mural_paleta]['texturas']
                    for i, tex_name in enumerate(texturas_mural[:3]):  # Máximo 3
                        if tex_name in texturas_dict:
                            if i == 0:
                                st.write(f"• **Triángulos delgados:** {tex_name} (color sólido)")
                            elif i == 1:
                                st.write(f"• **Triángulos gruesos:** {tex_name} (puntos/rayas)")
                            elif i == 2:
                                st.write(f"• **Acentos:** {tex_name} (patrón especial)")
            
            # Botón de generación
            if st.button("🏗️ Generar Mural Rectangular", type="primary"):
                with st.spinner('🔄 Generando mural rectangular para visualización arquitectónica...'):
                    try:
                        img_rect, stats_rect = generar_mural_rectangular_penrose(
                            ancho_mural, alto_mural, mural_paleta, mural_accent, lado_triangulo, texturas_dict
                        )
                        
                        if img_rect:
                            st.session_state['mural_rectangular'] = img_rect
                            st.session_state['stats_rectangular'] = stats_rect
                            st.success("✅ Mural rectangular generado!")
                            st.rerun()
                        else:
                            st.error("❌ Error generando el mural rectangular")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
                            # Mostrar resultado
            if 'mural_rectangular' in st.session_state:
                img_rect = st.session_state['mural_rectangular']
                stats_rect = st.session_state['stats_rectangular']
                
                st.markdown("#### 🖼️ Mural Rectangular Generado")
                
                # Vista previa optimizada para Streamlit
                st.markdown(f"""
                    **📊 Información de generación:**
                    • Resolución generada: {stats_rect['dimensiones_px'][0]} × {stats_rect['dimensiones_px'][1]} px
                    • DPI efectivo: {stats_rect['dpi']:.1f}
                    • Total píxeles: {stats_rect['dimensiones_px'][0] * stats_rect['dimensiones_px'][1]:,}
                    • Área: {stats_rect['area_m2']:.2f} m²
                """)
                
                # Crear thumbnail para visualización segura
                display_img = img_rect.copy()
                
                # Redimensionar para visualización si es muy grande
                if display_img.size[0] > 1200 or display_img.size[1] > 800:
                    display_img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                    st.info(f"Vista previa redimensionada a {display_img.size[0]}×{display_img.size[1]} px para visualización")
                
                # Mostrar imagen
                st.image(display_img, 
                        caption=f"Mural {stats_rect['dimensiones_cm'][0]}×{stats_rect['dimensiones_cm'][1]} cm - Paleta: {stats_rect['paleta']}", 
                        use_container_width=True)
                
                # Control de zoom para detalles
                if st.button("🔍 Ver Detalle del Centro"):
                    # Crear recorte del centro
                    w, h = img_rect.size
                    center_crop = img_rect.crop((w//3, h//3, 2*w//3, 2*h//3))
                    
                    st.image(center_crop, 
                            caption="Vista de detalle - Región central", 
                            use_container_width=True)
                    
                    st.info("🔬 Esta vista muestra la calidad real de los patrones y la definición de cada triángulo.")
                
                # Información del mural
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("#### 📊 Especificaciones Técnicas")
                    area_total_segura = calcular_area_segura(stats_rect)
                    dpi_seguro = obtener_dpi_seguro(stats_rect)
                    
                    st.write(f"**Dimensiones:** {stats_rect['dimensiones_cm'][0]} × {stats_rect['dimensiones_cm'][1]} cm")
                    st.write(f"**Resolución generada:** {stats_rect['dimensiones_px'][0]} × {stats_rect['dimensiones_px'][1]} px")
                    st.write(f"**DPI:** {dpi_seguro} (auto-optimizado)")
                    st.write(f"**Total triángulos:** {stats_rect['total_triangulos']}")
                    st.write(f"**Tamaño de pieza:** {stats_rect['lado_triangulo_cm']} cm")
                    st.write(f"**Área total:** {area_total_segura:.2f} m²")
                
                with col_info2:
                    st.markdown("#### 🧮 Lista de Materiales")
                    
                    contadores = stats_rect['contadores']
                    
                    # Crear tabla de materiales
                    materiales_data = []
                    
                    for categoria, items in contadores.items():
                        for tex_name, cantidad in items.items():
                            if cantidad > 0:
                                if categoria == 'thin':
                                    tipo = "Delgado (sólido)"
                                elif categoria == 'thick':
                                    tipo = "Grueso (patrón)"
                                else:
                                    tipo = "Acento (especial)"
                                
                                materiales_data.append({
                                    'Textura': tex_name,
                                    'Tipo': tipo,
                                    'Cantidad': cantidad,
                                    'Área (cm²)': int(cantidad * stats_rect['lado_triangulo_cm']**2 * 0.4)
                                })
                    
                    if materiales_data:
                        # Mostrar tabla de materiales
                        st.write("**Lista de materiales necesarios:**")
                        for item in materiales_data:
                            st.write(f"• **{item['Textura']}** ({item['Tipo']}): {item['Cantidad']} piezas - {item['Área (cm²)']} cm²")
                        
                        # Resumen total
                        total_area = sum(item['Área (cm²)'] for item in materiales_data)
                        st.write(f"**Área total de triángulos:** {total_area/10000:.2f} m²")
                    else:
                        st.write("No se generaron materiales")
                
                # Opciones de exportación
                st.markdown("#### 📤 Exportación")
                
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    st.markdown("**🖼️ Imagen para Visualización:**")
                    filename_viz = f"mural_rectangular_{stats_rect['paleta']}_{ancho_mural}x{alto_mural}cm.png"
                    download_link_viz = create_download_link(img_rect, filename_viz)
                    st.markdown(download_link_viz, unsafe_allow_html=True)
                    
                    st.info("""
                    **💡 Uso recomendado:**
                    • Importar a D5 Render como textura
                    • Aplicar a superficies arquitectónicas
                    • Visualización de proyectos
                    """)
                
                with col_export2:
                    if materiales_data:
                        st.markdown("**📋 Lista de Materiales (CSV):**")
                        
                        # Crear CSV de materiales
                        import io
                        import csv
                        
                        csv_buffer = io.StringIO()
                        csv_writer = csv.DictWriter(csv_buffer, fieldnames=['Textura', 'Tipo', 'Cantidad', 'Área (cm²)'])
                        csv_writer.writeheader()
                        csv_writer.writerows(materiales_data)
                        csv_content = csv_buffer.getvalue()
                        
                        csv_b64 = base64.b64encode(csv_content.encode()).decode()
                        csv_href = f'<a href="data:text/csv;base64,{csv_b64}" download="materiales_mural_{ancho_mural}x{alto_mural}.csv">📥 Descargar Lista de Materiales</a>'
                        st.markdown(csv_href, unsafe_allow_html=True)
                        
                        st.info("""
                        **📊 Contenido del CSV:**
                        • Lista completa de piezas necesarias
                        • Tipos y cantidades por textura
                        • Cálculo de áreas por categoría
                        """)
                
                # Botón para generar alta resolución
                st.markdown("#### 🔍 Versión de Alta Resolución")
                
                col_hires1, col_hires2 = st.columns(2)
                
                with col_hires1:
                    dpi_seleccionado = st.selectbox(
                        "Calidad de impresión:",
                        [
                            (100, "Visualización (100 DPI)"),
                            (150, "Impresión básica (150 DPI)"),
                            (200, "Impresión media (200 DPI)"),
                            (300, "Impresión profesional (300 DPI)")
                        ],
                        index=2,
                        format_func=lambda x: x[1]
                    )
                    
                    # Calcular tamaño estimado
                    dpi_valor = dpi_seleccionado[0]
                    px_estimado_ancho = int(ancho_mural * dpi_valor / 2.54)
                    px_estimado_alto = int(alto_mural * dpi_valor / 2.54)
                    pixels_totales = px_estimado_ancho * px_estimado_alto
                    mb_estimados = (pixels_totales * 3) / (1024 * 1024)
                
                with col_hires2:
                    st.markdown(f"""
                        **📐 Estimación para {dpi_valor} DPI:**
                        • Resolución: {px_estimado_ancho:,} × {px_estimado_alto:,} px
                        • Total píxeles: {pixels_totales:,}
                        • Tamaño archivo: ~{mb_estimados:.1f} MB
                        • Tiempo estimado: ~{max(1, int(mb_estimados/20))} minutos
                    """)
                    
                    if pixels_totales > 50_000_000:
                        st.warning("⚠️ Resolución muy alta. La generación puede tardar mucho tiempo.")
                    elif pixels_totales > 25_000_000:
                        st.info("💡 Resolución alta. Se aplicarán optimizaciones automáticas.")
                
                if st.button(f"📐 Generar Versión {dpi_seleccionado[1]}", help="Genera una versión optimizada para impresión"):
                    with st.spinner(f'🔄 Generando versión de {dpi_valor} DPI (puede tardar unos minutos)...'):
                        try:
                            # Generar versión de alta resolución con DPI específico
                            img_hires, stats_hires = generar_mural_rectangular_penrose(
                                ancho_mural, alto_mural, mural_paleta, mural_accent, lado_triangulo, texturas_dict, dpi_valor
                            )
                            
                            if img_hires:
                                # Mostrar información de la versión de alta resolución
                                dpi_hires_seguro = obtener_dpi_seguro(stats_hires)
                                
                                st.success("✅ Versión de alta resolución generada!")
                                st.write(f"**Resolución real:** {img_hires.size[0]} × {img_hires.size[1]} px")
                                st.write(f"**DPI efectivo:** {dpi_hires_seguro}")
                                actual_mb = (img_hires.size[0] * img_hires.size[1] * 3 / 1024 / 1024)
                                st.write(f"**Tamaño de archivo:** ~{actual_mb:.1f} MB")
                                
                                dpi_hires_num = stats_hires.get('dpi', 0)
                                if isinstance(dpi_hires_num, (int, float)) and dpi_hires_num < dpi_valor:
                                    st.info(f"💡 Resolución optimizada automáticamente de {dpi_valor} a {dpi_hires_num:.1f} DPI para evitar archivos excesivos.")
                                
                                # Vista previa thumbnail
                                thumb = img_hires.copy()
                                thumb.thumbnail((600, 400), Image.Resampling.LANCZOS)
                                st.image(thumb, caption=f"Vista previa de {dpi_hires_seguro} DPI", width=400)
                                
                                # Descarga de alta resolución
                                filename_hires = f"mural_HIRES_{stats_rect['paleta']}_{ancho_mural}x{alto_mural}cm_{dpi_hires_seguro}dpi.png"
                                download_link_hires = create_download_link(img_hires, filename_hires)
                                st.markdown(download_link_hires, unsafe_allow_html=True)
                                
                                # Información de uso
                                dpi_value_safe = stats_hires.get('dpi', 0)
                                if isinstance(dpi_value_safe, (int, float)):
                                    if dpi_value_safe >= 200:
                                        st.success("✅ Calidad perfecta para impresión profesional y visualización arquitectónica.")
                                    elif dpi_value_safe >= 150:
                                        st.info("💡 Calidad buena para impresión estándar y visualización.")
                                    else:
                                        st.warning("⚠️ Resolución optimizada para visualización rápida. Para impresión usar 200+ DPI.")
                                else:
                                    st.info("💡 Resolución optimizada automáticamente para mejor rendimiento.")
                            else:
                                st.error("❌ Error generando versión de alta resolución")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.info("💡 Si el error persiste, intenta recargar la página y generar nuevamente.")
                            st.info("💡 Si persiste el error, usa una dimensión menor o DPI más bajo.")
            
            else:
                st.markdown("""
                    <div class="pattern-preview">
                        <h4>🎯 Configuración Lista para Mural Rectangular</h4>
                        <p>Sistema diseñado para:</p>
                        <ul>
                            <li><strong>Visualización arquitectónica</strong> - Compatible con D5 Render</li>
                            <li><strong>Cálculo de materiales</strong> - Lista completa de piezas necesarias</li>
                            <li><strong>Patrones simples</strong> - Colores sólidos, puntos y rayas</li>
                            <li><strong>Exportación profesional</strong> - Múltiples formatos y resoluciones</li>
                        </ul>
                        <p>Haz clic en "Generar Mural Rectangular" para empezar.</p>
                    </div>
                """, unsafe_allow_html=True)
        
        else:
            st.error("❌ No hay texturas disponibles para generar murales rectangulares")

    with tab4:
        st.markdown("### 📚 Galería de Patrones con Texturas")
        
        if texturas_dict:
            # Generar ejemplos de cada paleta
            st.markdown("#### 🎨 Ejemplos de Cada Paleta")
            
            for paleta_nombre in PALETAS_TEXTURAS.keys():
                with st.expander(f"Ver ejemplo de paleta: {paleta_nombre}"):
                    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write(f"**{paleta_info['descripcion']}**")
                        st.write(f"*{paleta_info['teoria']}*")
                        
                        # Vista previa
                        preview_img = crear_vista_previa_paleta(paleta_nombre, texturas_dict)
                        if preview_img:
                            st.image(preview_img, caption="Vista previa de texturas", use_container_width=True)
                        
                        if st.button(f"Generar ejemplo {paleta_nombre}", key=f"gallery_{paleta_nombre}"):
                            with st.spinner(f'Generando ejemplo de {paleta_nombre}...'):
                                img, stats = generate_penrose_tiles_with_textures(
                                    5, (1600, 1600), paleta_nombre, None, 0.002, 2.0, texturas_dict
                                )
                                
                                if img:
                                    # Guardar en session state con clave única
                                    st.session_state[f'gallery_img_{paleta_nombre}'] = img
                                    st.session_state[f'gallery_stats_{paleta_nombre}'] = stats
                                    st.rerun()
                    
                    with col2:
                        # Mostrar imagen generada si existe
                        if f'gallery_img_{paleta_nombre}' in st.session_state:
                            img = st.session_state[f'gallery_img_{paleta_nombre}']
                            stats = st.session_state[f'gallery_stats_{paleta_nombre}']
                            
                            st.image(img, caption=f"Ejemplo: {paleta_nombre}", use_container_width=True)
                            st.write(f"**Piezas totales:** {stats['total_pieces']}")
                            
                            # Botón de descarga
                            filename = f"gallery_{paleta_nombre}_example.png"
                            download_link = create_download_link(img, filename)
                            st.markdown(download_link, unsafe_allow_html=True)
        else:
            st.error("❌ No hay texturas disponibles para la galería")
    
    # Footer con información
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>🎨 Generador de Mosaicos Penrose con Texturas Individuales | Cada Triángulo = Una Pieza</p>
            <p>💡 Paletas diseñadas siguiendo principios de armonía cromática</p>
            <p>🧩 Cada triángulo es independiente - perfecto para corte e impresión</p>
            <p>🔧 Tecnologías: Streamlit, Cairo, PIL, NumPy</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()