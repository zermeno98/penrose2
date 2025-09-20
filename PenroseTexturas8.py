import streamlit as st
import math, cmath, cairo, random
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime
import base64
import json 


import numpy as np
from sklearn.cluster import KMeans
import colorsys

# Configuración de la página
st.set_page_config(
    page_title="🎨 Generador Mosaicos Penrose con Texturas",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# CSS personalizado con logo
st.markdown("""
    <style>
    .main-header {
        display: flex;
        align-items: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .logo-container {
        margin-right: 2rem;
        flex-shrink: 0;
    }
    .logo-container img {
        height: 80px;
        width: auto;
        border-radius: 8px;
        background: white;
        padding: 8px;
    }
    .header-content {
        flex: 1;
    }
    .header-content h1 {
        margin: 0 0 0.5rem 0;
        font-size: 2.2rem;
    }
    .header-content p {
        margin: 0;
        font-size: 1.1rem;
        opacity: 0.9;
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


# Header principal con logo integrado
try:
    if os.path.exists("logo.png"):
        # Leer la imagen y convertir a base64 para incluir en HTML
        import base64
        with open("logo.png", "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        
        st.markdown(f"""
            <div class="main-header">
                <div class="logo-container">
                    <img src="data:image/png;base64,{img_base64}" alt="Logo Empresa">
                </div>
                <div class="header-content">
                    <h1>🎨 Generador de Mosaicos Penrose VER 2 AI </h2>
                    <p>Crea hermosos azulejos geométricos usando patrones de texturas basados en teoría del color</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback sin logo
        st.markdown("""
            <div class="main-header">
                <div class="header-content">
                    <h1>🏢 🎨 Generador de Mosaicos Penrose </h2>
                    <p>Crea hermosos azulejos geométricos usando patrones de texturas basados en teoría del color</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.warning("⚠️ Logo no encontrado: coloca 'logo.png' en el directorio del proyecto")

except Exception as e:
    # Fallback en caso de error
    st.markdown("""
        <div class="main-header">
            <div class="header-content">
                <h1>🎨 Generador de Mosaicos Penrose </h2>
                <p>Crea hermosos azulejos geométricos usando patrones de texturas basados en teoría del color</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.error(f"Error cargando logo: {str(e)}")
    

# Definición de paletas basadas en teoría del color
PALETAS_TEXTURAS = {
    'Fuego': {
        'texturas': ['rosa', 'amarillo', 'naranja'],
        'descripcion': '🔥 Análoga Cálida - Rosa, Amarillo, Naranja',
        'teoria': 'Colores análogos en el espectro cálido para energía y dinamismo'
    },
    'Océano': {
        'texturas': ['azul', 'turquesa', 'verde'],
        'descripcion': '🌊 Análoga Fría - Azul, Turquesa, Verde',
        'teoria': 'Colores fríos consecutivos que transmiten calma y naturaleza'
    },
    'Contraste': {
        'texturas': ['azul', 'naranja', 'blanco1'],
        'descripcion': '⚡ Complementaria - Azul, Naranja, Blanco',
        'teoria': 'Colores opuestos que crean máximo impacto visual'
    },
    
    'Elegante': {
        'texturas': ['gris2', 'gris 1', 'blanco1'],  # Quitar blanco 4
        'descripcion': '🏛️ Monocromática - Escala de Grises',
        'teoria': 'Escala de valores en un solo tono para sofisticación'
    },
    

    'Triádica': {
        'texturas': ['rosa', 'verde', 'amarillo'],
        'descripcion': '🎨 Triádica Vibrante - Rosa, Verde, Amarillo',
        'teoria': 'Tres colores equidistantes para balance dinámico'
    },
    'Sunset': {
        'texturas': ['amarillo', 'naranja', 'rosa'],
        'descripcion': '🌅 Atardecer - Amarillo, Naranja, Rosa',
        'teoria': 'Progresión natural de colores cálidos como en un atardecer'
    },
    'Premium': {
        'texturas': ['negro', 'gris2', 'beige'],
        'descripcion': '👔 Elegante Premium - Negro, Gris, Beige',
        'teoria': 'Monocromática sofisticada con contraste dramático'
    },
    'Tropical': {
        'texturas': ['turquesa', 'verde', 'amarillo'],
        'descripcion': '🏝️ Tropical - Turquesa, Verde, Amarillo',
        'teoria': 'Triádica natural inspirada en paisajes tropicales'
    },
    'Royal': {
        'texturas': ['morado', 'amarillo', 'blanco1'],
        'descripcion': '👑 Real - Morado, Amarillo, Blanco',
        'teoria': 'Complementaria clásica de elegancia imperial'
    }
}

@st.cache_data
def cargar_texturas_streamlit():
    """Carga texturas para Streamlit con manejo de errores"""
    texturas = {}    
    nombres_texturas = [
        "verde.png", "blanco1.png", "naranja.png", "blanco2.png", 
        "azul.png", "blanco 3.png", "gris 1.png", "gris2.png", 
        "blanco 4.png", "amarillo.png", "rosa.png",
        "morado.png", "turquesa.png", "negro.png", "beige.png"
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
        
        # Patrones originales
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
        
        # NUEVOS PATRONES (agregar estos)
        elif pattern == 'geometric_burst':
            burst_rays = 8
            ray_angle = angle * burst_rays / (2 * math.pi)
            in_ray = abs(ray_angle - round(ray_angle)) < 0.3
            return in_ray and distance > 0.2 and distance < 0.7
        
        elif pattern == 'wave_pattern':
            wave_freq = 4
            wave_amplitude = 0.2
            wave_center = 0.5
            wave_function = wave_center + wave_amplitude * math.sin(angle * wave_freq)
            return abs(distance - wave_function) < 0.1
        
        elif pattern == 'triangular_grid':
            x, y = center.real, center.imag
            grid_size = 0.3
            grid_x = int(x / grid_size)
            grid_y = int(y / grid_size)
            return (grid_x + grid_y) % 3 == 0 and distance < 0.8
        
        elif pattern == 'hexagonal_core':
            hex_radius = 0.4
            if distance > hex_radius:
                return False
            hex_angle = angle * 3 / math.pi
            hex_sector = int(hex_angle) % 6
            return hex_sector % 2 == 0
        
        elif pattern == 'lightning_bolt':
            x, y = center.real, center.imag
            zigzag_freq = 6
            zigzag_amplitude = 0.15
            zigzag_path = zigzag_amplitude * math.sin(y * zigzag_freq)
            bolt_width = 0.08
            return abs(x - zigzag_path) < bolt_width and abs(y) < 0.6
        
        elif pattern == 'celtic_knot':
            knot_freq = 3
            knot_phase1 = math.sin(angle * knot_freq)
            knot_phase2 = math.cos(angle * knot_freq + math.pi/4)
            knot_function = 0.4 + 0.2 * knot_phase1 * knot_phase2
            return abs(distance - knot_function) < 0.1
        
        elif pattern == 'mandala_rings':
            ring_count = 5
            ring_spacing = 0.12
            mandala_detail = math.sin(angle * 8) * 0.03
            for i in range(1, ring_count + 1):
                ring_radius = i * ring_spacing + mandala_detail
                if abs(distance - ring_radius) < 0.04:
                    return True
            return False
        
        elif pattern == 'fractal_branch':
            branch_angle1 = math.pi / 4
            branch_angle2 = 3 * math.pi / 4
            branch_angle3 = 5 * math.pi / 4
            branch_angle4 = 7 * math.pi / 4
            
            branch_tolerance = 0.2
            branch_angles = [branch_angle1, branch_angle2, branch_angle3, branch_angle4]
            
            for b_angle in branch_angles:
                angle_diff = abs(angle - b_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                if angle_diff < branch_tolerance and distance > 0.1 and distance < 0.8:
                    secondary_freq = distance * 10
                    if math.sin(secondary_freq) > 0.3:
                        return True
            return False
            
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
    Genera un mural rectangular usando el MISMO patrón Penrose que funciona bien
    Solo cambia de polígono a rectángulo - como un "tapiz" horizontal
    """
    
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None, {}
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    
    # Verificar texturas disponibles
    texturas_disponibles = [tex for tex in texturas_paleta if tex in _texturas_dict]
    
    if not texturas_disponibles:
        return None, {}
    
    # **USAR EL MISMO SISTEMA QUE FUNCIONA EN EL GENERADOR PRINCIPAL**
    # Calcular resolución para el rectángulo manteniendo proporción áurea
    if abs(ancho_cm / alto_cm - 1.618) < 0.1:  # Si es proporción áurea
        r1 = 1200  # Ancho base
        r2 = int(r1 / 1.618)  # Alto proporcional
    else:
        r1 = 1200
        r2 = int(r1 * alto_cm / ancho_cm)
    
    phi = (5 ** 0.5 + 1) / 2
    
    # Crear surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, r1, r2)
    ctx = cairo.Context(surface)
    
    # Configurar escalas IGUAL que en el generador principal
    scale = min(r1, r2) * 0.4
    ctx.scale(scale, scale)
    ctx.translate(0.5 * r1/scale, 0.5 * r2/scale)
    
    # Fondo blanco
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()
    
    # **DEFINIR LÍMITES RECTANGULARES GLOBALMENTE AL PRINCIPIO**
    ratio = ancho_cm / alto_cm
    x_limit = ratio * 0.45  # **ZOOM MAYOR** - aumentado de 0.6 a 0.8
    y_limit = 0.45          # **ZOOM MAYOR** - aumentado de 0.6 a 0.8
    
    # Generar patrón Penrose CONTINUO desde el centro**
    def generate_penrose_rhombi_extended(divisions):
        """Genera un solo patrón grande desde el centro para evitar desfases"""
        base = 5
        triangles = []
        
        # **GENERAR UN SOLO PATRÓN GRANDE** desde el centro
        for i in range(base * 2):
            v2 = cmath.rect(1, (2*i - 1) * math.pi / (base * 2))
            v3 = cmath.rect(1, (2*i + 1) * math.pi / (base * 2))
            
            if i % 2 == 0:
                v2, v3 = v3, v2
            
            triangles.append(("thin", 0+0j, v2, v3))
        
        # **MÁS DIVISIONES** para que el patrón sea más grande y cubra el rectángulo
        for iteration in range(divisions + 1):  # Una división extra para cobertura
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
        x_rel = center.real / (ancho_cm / alto_cm / 2)  # Normalizar al rectángulo
        y_rel = center.imag / 0.5   # Normalizar verticalmente
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
    
    def triangulo_esta_en_rectangulo(triangle, ancho_cm, alto_cm):
        """Verifica si el triángulo está dentro de un RECTÁNGULO PURO"""
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        # **USAR LOS LÍMITES GLOBALES YA DEFINIDOS**
        # Verificar si CUALQUIER parte del triángulo está dentro del rectángulo
        for v in vertices:
            if abs(v.real) <= x_limit and abs(v.imag) <= y_limit:
                return True
        
        # Verificar centro del triángulo
        centro = (v1 + v2 + v3) / 3
        if abs(centro.real) <= x_limit and abs(centro.imag) <= y_limit:
            return True
        
        return False
    
        
    def get_pattern_style(texture_name):
        """Define estilos de patrón para todas las texturas"""
        patterns = {
            'azul': ('solid', (0.2, 0.4, 0.8)),
            'verde': ('solid', (0.2, 0.6, 0.3)),
            'rosa': ('solid', (0.91, 0.12, 0.39)),          # Nuevo
            'amarillo': ('solid', (1.0, 0.76, 0.03)),       # Nuevo
            'naranja': ('solid', (1.0, 0.5, 0.1)),
            'morado': ('solid', (0.40, 0.23, 0.72)),        # Nuevo
            'turquesa': ('solid', (0.15, 0.65, 0.60)),      # Nuevo
            'negro': ('solid', (0.13, 0.13, 0.13)),         # Nuevo
            'beige': ('solid', (0.84, 0.80, 0.78)),         # Nuevo
            'gris 1': ('solid', (0.5, 0.5, 0.5)),
            'gris2': ('solid', (0.3, 0.3, 0.3)),
            'blanco1': ('solid', (0.95, 0.95, 0.95)),
            'blanco2': ('solid', (0.9, 0.9, 0.9)),
            'blanco 3': ('solid', (0.85, 0.85, 0.85)),
            'blanco 4': ('solid', (0.8, 0.8, 0.8)),
        }
        
        return patterns.get(texture_name, ('solid', (0.7, 0.7, 0.7)))
        
    # **GENERAR PATRÓN EXTENDIDO** (6 divisiones como en el original)
    triangles = generate_penrose_rhombi_extended(6)
    
    # **FILTRAR SOLO POR RECTÁNGULO** en lugar de polígono
    triangles_en_rectangulo = []
    for triangle in triangles:
        if triangulo_esta_en_rectangulo(triangle, ancho_cm, alto_cm):
            triangles_en_rectangulo.append(triangle)
    
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
    
    # **RENDERIZAR IGUAL QUE EN EL GENERADOR PRINCIPAL**
    for triangle in triangles_en_rectangulo:
        shape, v1, v2, v3 = triangle
        
        # Crear path del triángulo
        ctx.move_to(v1.real, v1.imag)
        ctx.line_to(v2.real, v2.imag)
        ctx.line_to(v3.real, v3.imag)
        ctx.close_path()
        
        # Determinar textura según tipo
        if should_use_accent_pattern_rectangular(triangle, accent_pattern, ancho_cm, alto_cm):
            texture_name = texturas_disponibles[2] if len(texturas_disponibles) > 2 else texturas_disponibles[0]
            contadores['accent'][texture_name] += 1
        elif shape == "thin":
            texture_name = texturas_disponibles[0] if len(texturas_disponibles) > 0 else None
            contadores['thin'][texture_name] += 1
        else:  # thick
            texture_name = texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
            contadores['thick'][texture_name] += 1
        
        # Obtener estilo y aplicar color
        pattern_style = get_pattern_style(texture_name)
        style, rgb = pattern_style
        
        ctx.set_source_rgb(*rgb)
        ctx.fill_preserve()
        
        # Contorno
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(0.002)
        ctx.stroke()
    
    # **DIBUJAR MARCO RECTANGULAR FINAL**
    ctx.reset_clip()  # Quitar la máscara para dibujar el marco
    ctx.rectangle(-x_limit, -y_limit, 2*x_limit, 2*y_limit)
    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_line_width(0.01)
    ctx.stroke()
    
    # Convertir a imagen PIL
    buf = surface.get_data()
    a = np.ndarray(shape=(r2, r1, 4), dtype=np.uint8, buffer=buf)
    a = a[:, :, [2, 1, 0, 3]]  # BGRA -> RGBA
    
    img_tapiz = Image.fromarray(a)
    
    # **YA NO NECESITAMOS RECORTE** - el patrón ya es rectangular desde el principio
    
    # Calcular totales
    total_triangulos = sum(sum(categoria.values()) for categoria in contadores.values())
    
    return img_tapiz, {
        'dimensiones_cm': (ancho_cm, alto_cm),
        'dimensiones_px': (r1, r2),
        'dimensiones_reales_cm': (ancho_cm, alto_cm),
        'total_triangulos': total_triangulos,
        'contadores': contadores,
        'paleta': paleta_nombre,
        'texturas_usadas': texturas_disponibles,
        'accent_pattern': accent_pattern,
        'lado_triangulo_cm': lado_triangulo_cm,
        'dpi': 150,  # Para compatibilidad
        'es_visualizacion_escalada': True,
        'area_real_m2': (ancho_cm * alto_cm) / 10000,
        'patron_origen': 'Mismo que generador principal',
        'formato': 'Rectángulo horizontal (tapiz)'
    }

# -----------   mural simple


def generar_mural_rectangular_penrose_simplificado(ancho_cm, alto_cm, paleta_nombre, accent_pattern, lado_triangulo_cm, _texturas_dict):
    """
    Genera mural con PROPORCIONES REALES pero resolución optimizada
    """
    
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None, {}
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    texturas_disponibles = [tex for tex in texturas_paleta if tex in _texturas_dict]
    
    if not texturas_disponibles:
        return None, {}
    
    # **RESOLUCIÓN FIJA** (igual que el generador principal)
    r1 = 1200
    r2 = int(r1 * alto_cm / ancho_cm)
    if r2 > 900:
        r2 = 900
        r1 = int(r2 * ancho_cm / alto_cm)
    
    phi = (5 ** 0.5 + 1) / 2
    
    # Crear surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, r1, r2)
    ctx = cairo.Context(surface)
    
    # **USAR LA MISMA ESCALA QUE FUNCIONA EN EL GENERADOR PRINCIPAL**
    scale = min(r1, r2) * 0.4
    ctx.scale(scale, scale)
    ctx.translate(0.5 * r1/scale, 0.5 * r2/scale)
    
    # Fondo blanco
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()
    
    # **LÍMITES RECTANGULARES COMO EN LA FUNCIÓN ORIGINAL**
    ratio = ancho_cm / alto_cm
    x_limit = ratio * 0.45  # Igual que en la función original
    y_limit = 0.45          # Igual que en la función original
    
    def generate_penrose_rhombi_extended(divisions):
        """Igual que en la función original que funciona"""
        base = 5
        triangles = []
        
        for i in range(base * 2):
            v2 = cmath.rect(1, (2*i - 1) * math.pi / (base * 2))
            v3 = cmath.rect(1, (2*i + 1) * math.pi / (base * 2))
            
            if i % 2 == 0:
                v2, v3 = v3, v2
            
            triangles.append(("thin", 0+0j, v2, v3))
        
        # **USAR 6 DIVISIONES** como en el generador principal
        for iteration in range(min(divisions, 6)):
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
    
    def triangulo_esta_en_rectangulo(triangle):
        """Igual que en la función original"""
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        for v in vertices:
            if abs(v.real) <= x_limit and abs(v.imag) <= y_limit:
                return True
        
        centro = (v1 + v2 + v3) / 3
        if abs(centro.real) <= x_limit and abs(centro.imag) <= y_limit:
            return True
        
        return False
    
    def should_use_accent_pattern_rectangular(triangle, pattern, ancho_cm, alto_cm):
        """Determina si usar patrón de acento centrado en el rectángulo"""
        if pattern is None or pattern == 'Ninguno':
            return False
            
        shape, v1, v2, v3 = triangle
        center = (v1 + v2 + v3) / 3
        
        # Convertir a coordenadas del rectángulo (centro = 0,0)
        x_rel = center.real / (ancho_cm / alto_cm / 2)  # Normalizar al rectángulo
        y_rel = center.imag / 0.5   # Normalizar verticalmente
        distance_from_center = math.sqrt(x_rel**2 + y_rel**2)
        angle = cmath.phase(center) % (2 * math.pi)
        
        # Patrones originales
        if pattern == 'center_star':
            return distance_from_center < 0.3
        elif pattern == 'outer_ring':
            return distance_from_center > 0.6 and distance_from_center < 0.8
        elif pattern == 'radial_bands':
            band_angle = angle * 6 / (2 * math.pi)
            return int(band_angle) % 2 == 0 and distance_from_center < 0.7
        elif pattern == 'spiral_arms':
            spiral_angle = (angle + distance_from_center * 2 * math.pi) % (2 * math.pi)
            arm_width = 0.4
            arm_spacing = 2 * math.pi / 5
            
            for i in range(5):
                arm_center = i * arm_spacing
                if abs(spiral_angle - arm_center) < arm_width or \
                abs(spiral_angle - arm_center - 2*math.pi) < arm_width:
                    return distance_from_center > 0.2 and distance_from_center < 0.8
            return False
        elif pattern == 'diamond_cross':
            x, y = center.real, center.imag
            main_cross = (abs(x) < 0.15 and abs(y) < 0.6) or \
                        (abs(y) < 0.15 and abs(x) < 0.6)
            diagonal_cross = (abs(x - y) < 0.12 and distance_from_center < 0.6) or \
                        (abs(x + y) < 0.12 and distance_from_center < 0.6)
            return main_cross or diagonal_cross
        elif pattern == 'petal_flower':
            if distance_from_center < 0.15 or distance_from_center > 0.7:
                return False
            petal_function = math.sin(5 * angle) * 0.3 + 0.4
            petal_tolerance = 0.08
            return abs(distance_from_center - petal_function) < petal_tolerance
        elif pattern == 'concentric_rings':
            ring_width = 0.15
            ring_number = int(distance_from_center / ring_width)
            return ring_number % 2 == 1
        
        # NUEVOS PATRONES
        elif pattern == 'geometric_burst':
            # Explosión geométrica desde el centro
            burst_rays = 8
            ray_angle = angle * burst_rays / (2 * math.pi)
            in_ray = abs(ray_angle - round(ray_angle)) < 0.3
            return in_ray and distance_from_center > 0.2 and distance_from_center < 0.7
        
        elif pattern == 'wave_pattern':
            # Ondas sinusoidales
            wave_freq = 4
            wave_amplitude = 0.2
            wave_center = 0.5
            wave_function = wave_center + wave_amplitude * math.sin(angle * wave_freq)
            return abs(distance_from_center - wave_function) < 0.1
        
        elif pattern == 'triangular_grid':
            # Grilla triangular adaptada al rectángulo
            x, y = center.real, center.imag
            grid_size = 0.3
            grid_x = int(x / grid_size)
            grid_y = int(y / grid_size)
            return (grid_x + grid_y) % 3 == 0 and distance_from_center < 0.8
        
        elif pattern == 'hexagonal_core':
            # Núcleo hexagonal
            hex_radius = 0.4
            if distance_from_center > hex_radius:
                return False
            hex_angle = angle * 3 / math.pi
            hex_sector = int(hex_angle) % 6
            return hex_sector % 2 == 0
        
        elif pattern == 'lightning_bolt':
            # Rayo en zigzag adaptado al rectángulo
            x, y = center.real, center.imag
            zigzag_freq = 6
            zigzag_amplitude = 0.15
            # Ajustar zigzag al ratio del rectángulo
            ratio_factor = ancho_cm / alto_cm
            zigzag_path = zigzag_amplitude * math.sin(y * zigzag_freq * ratio_factor)
            bolt_width = 0.08
            return abs(x - zigzag_path) < bolt_width and abs(y) < 0.6
        
        elif pattern == 'celtic_knot':
            # Nudo celta simplificado
            knot_freq = 3
            knot_phase1 = math.sin(angle * knot_freq)
            knot_phase2 = math.cos(angle * knot_freq + math.pi/4)
            knot_function = 0.4 + 0.2 * knot_phase1 * knot_phase2
            return abs(distance_from_center - knot_function) < 0.1
        
        elif pattern == 'mandala_rings':
            # Anillos de mandala
            ring_count = 5
            ring_spacing = 0.12
            mandala_detail = math.sin(angle * 8) * 0.03
            for i in range(1, ring_count + 1):
                ring_radius = i * ring_spacing + mandala_detail
                if abs(distance_from_center - ring_radius) < 0.04:
                    return True
            return False
        
        elif pattern == 'fractal_branch':
            # Patrón de ramificación fractal
            branch_angle1 = math.pi / 4  # 45 grados
            branch_angle2 = 3 * math.pi / 4  # 135 grados
            branch_angle3 = 5 * math.pi / 4  # 225 grados
            branch_angle4 = 7 * math.pi / 4  # 315 grados
            
            branch_tolerance = 0.2
            branch_angles = [branch_angle1, branch_angle2, branch_angle3, branch_angle4]
            
            for b_angle in branch_angles:
                angle_diff = abs(angle - b_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                if angle_diff < branch_tolerance and distance_from_center > 0.1 and distance_from_center < 0.8:
                    # Ramificación secundaria
                    secondary_freq = distance_from_center * 10
                    if math.sin(secondary_freq) > 0.3:
                        return True
            return False
        
        return False
    
    def get_pattern_style(texture_name):
        """Estilos como en la función original"""
        patterns = {
            'azul': ('solid', (0.2, 0.4, 0.8)),
            'verde': ('solid', (0.2, 0.6, 0.3)),
            'rosa': ('solid', (0.9, 0.3, 0.5)),
            'amarillo': ('solid', (0.9, 0.8, 0.2)),
            'naranja': ('solid', (1.0, 0.5, 0.1)),
            'gris 1': ('solid', (0.5, 0.5, 0.5)),
            'gris2': ('solid', (0.3, 0.3, 0.3)),
            'blanco1': ('solid', (0.95, 0.95, 0.95)),
            'blanco2': ('solid', (0.9, 0.9, 0.9)),
            'blanco 3': ('solid', (0.85, 0.85, 0.85)),
            'blanco 4': ('solid', (0.8, 0.8, 0.8)),
        }
        return patterns.get(texture_name, ('solid', (0.7, 0.7, 0.7)))
    
    # **CÁLCULO DE MATERIALES EXACTOS** (mantenido)
    def calcular_materiales_exactos():
        area_total_cm2 = ancho_cm * alto_cm
        area_triangulo_cm2 = (lado_triangulo_cm ** 2) * 0.433
        triangulos_estimados = int(area_total_cm2 / area_triangulo_cm2 * 0.85)
        
        thin_ratio = 0.618
        thick_ratio = 0.382
        accent_ratio = 0.1 if accent_pattern != 'Ninguno' else 0
        
        if accent_ratio > 0:
            thin_ratio *= (1 - accent_ratio)
            thick_ratio *= (1 - accent_ratio)
        
        triangulos_thin = int(triangulos_estimados * thin_ratio)
        triangulos_thick = int(triangulos_estimados * thick_ratio)
        triangulos_accent = int(triangulos_estimados * accent_ratio)
        
        contadores = {'thin': {}, 'thick': {}, 'accent': {}}
        
        for tex_name in texturas_disponibles:
            contadores['thin'][tex_name] = 0
            contadores['thick'][tex_name] = 0
            contadores['accent'][tex_name] = 0
        
        if len(texturas_disponibles) > 0:
            contadores['thin'][texturas_disponibles[0]] = triangulos_thin
        
        if len(texturas_disponibles) > 1:
            contadores['thick'][texturas_disponibles[1]] = triangulos_thick
        elif len(texturas_disponibles) > 0:
            contadores['thick'][texturas_disponibles[0]] = triangulos_thick
        
        if triangulos_accent > 0 and len(texturas_disponibles) > 2:
            contadores['accent'][texturas_disponibles[2]] = triangulos_accent
        
        return contadores, triangulos_estimados
    
    # **GENERAR PATRÓN IGUAL QUE LA FUNCIÓN ORIGINAL**
    triangles = generate_penrose_rhombi_extended(6)  # 6 divisiones como funciona
    
    # Filtrar triángulos en el rectángulo
    triangles_en_rectangulo = []
    for triangle in triangles:
        if triangulo_esta_en_rectangulo(triangle):
            triangles_en_rectangulo.append(triangle)
    
    # Contadores para visualización
    contadores_visual = {'thin': {}, 'thick': {}, 'accent': {}}
    for tex_name in texturas_disponibles:
        contadores_visual['thin'][tex_name] = 0
        contadores_visual['thick'][tex_name] = 0
        contadores_visual['accent'][tex_name] = 0
    
    # **RENDERIZAR IGUAL QUE LA FUNCIÓN ORIGINAL**
    for triangle in triangles_en_rectangulo:
        shape, v1, v2, v3 = triangle
        
        # Crear path del triángulo
        ctx.move_to(v1.real, v1.imag)
        ctx.line_to(v2.real, v2.imag)
        ctx.line_to(v3.real, v3.imag)
        ctx.close_path()
        
       
        #if should_use_accent_pattern_rectangular(triangle, accent_pattern):
        # Determinar textura
        if should_use_accent_pattern_rectangular(triangle, accent_pattern, ancho_cm, alto_cm):  # ← AGREGAR PARÁMETROS
            texture_name = texturas_disponibles[2] if len(texturas_disponibles) > 2 else texturas_disponibles[0]
            contadores_visual['accent'][texture_name] += 1
        elif shape == "thin":
            texture_name = texturas_disponibles[0] if len(texturas_disponibles) > 0 else None
            contadores_visual['thin'][texture_name] += 1
        else:  # thick
            texture_name = texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
            contadores_visual['thick'][texture_name] += 1
        
        # Obtener estilo y aplicar color
        pattern_style = get_pattern_style(texture_name)
        style, rgb = pattern_style
        
        ctx.set_source_rgb(*rgb)
        ctx.fill_preserve()
        
        # Contorno
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(0.002)
        ctx.stroke()
    
    # **DIBUJAR MARCO RECTANGULAR**
    ctx.rectangle(-x_limit, -y_limit, 2*x_limit, 2*y_limit)
    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.set_line_width(0.01)
    ctx.stroke()
    
    # Calcular materiales exactos (independiente de visualización)
    contadores_exactos, total_triangulos = calcular_materiales_exactos()
    
    # Convertir a imagen PIL
    buf = surface.get_data()
    a = np.ndarray(shape=(r2, r1, 4), dtype=np.uint8, buffer=buf)
    a = a[:, :, [2, 1, 0, 3]]
    
    img_mural = Image.fromarray(a)
    
    return img_mural, {
        'dimensiones_cm': (ancho_cm, alto_cm),
        'dimensiones_px': (r1, r2),
        'total_triangulos': total_triangulos,
        'triangulos_mostrados': len(triangles_en_rectangulo),
        'contadores': contadores_exactos,
        'contadores_visualizacion': contadores_visual,
        'paleta': paleta_nombre,
        'texturas_usadas': texturas_disponibles,
        'accent_pattern': accent_pattern,
        'lado_triangulo_cm': lado_triangulo_cm,
        'es_visualizacion_simplificada': True,
        'area_real_m2': (ancho_cm * alto_cm) / 10000,
        'resolucion_fija': f"{r1}x{r2} (optimizada)"
    }

def generar_mural_svg(ancho_cm, alto_cm, paleta_nombre, accent_pattern, lado_triangulo_cm, _texturas_dict):
    """
    Genera el mismo patrón pero exportado como SVG vectorial
    """
    
    if paleta_nombre not in PALETAS_TEXTURAS:
        return None, {}
    
    paleta_info = PALETAS_TEXTURAS[paleta_nombre]
    texturas_paleta = paleta_info['texturas']
    texturas_disponibles = [tex for tex in texturas_paleta if tex in _texturas_dict]
    
    if not texturas_disponibles:
        return None, {}
    
    phi = (5 ** 0.5 + 1) / 2
    
    # Dimensiones SVG en unidades (usar cm directamente)
    svg_width = ancho_cm
    svg_height = alto_cm
    
    # Escala para centrar el patrón
    escala = min(svg_width, svg_height) * 0.4
    center_x = svg_width / 2
    center_y = svg_height / 2
    
    # Límites del rectángulo
    ratio = ancho_cm / alto_cm
    x_limit = ratio * 0.45
    y_limit = 0.45
    
    def get_svg_color(texture_name):
        """Colores en formato SVG hexadecimal"""
        colors = {
            'azul': '#3366CC',
            'verde': '#33AA55',
            'rosa': '#E91E63',          # Nuevo
            'amarillo': '#FFC107',      # Nuevo
            'naranja': '#FF8833',
            'morado': '#673AB7',        # Nuevo
            'turquesa': '#26A69A',      # Nuevo
            'negro': '#212121',         # Nuevo
            'beige': '#D7CCC8',         # Nuevo
            'gris 1': '#808080',
            'gris2': '#4D4D4D',
            'blanco1': '#F2F2F2',
            'blanco2': '#E6E6E6',
            'blanco 3': '#D9D9D9',
            'blanco 4': '#CCCCCC',
        }
        return colors.get(texture_name, '#B3B3B3')
    
    def generate_penrose_for_svg():
        """Misma generación que la función principal"""
        base = 5
        triangles = []
        
        for i in range(base * 2):
            v2 = cmath.rect(1, (2*i - 1) * math.pi / (base * 2))
            v3 = cmath.rect(1, (2*i + 1) * math.pi / (base * 2))
            
            if i % 2 == 0:
                v2, v3 = v3, v2
            
            triangles.append(("thin", 0+0j, v2, v3))
        
        for iteration in range(6):  # 6 divisiones como en la función principal
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
    
    def triangulo_esta_en_rectangulo_svg(triangle):
        """Filtro rectangular para SVG"""
        shape, v1, v2, v3 = triangle
        vertices = [v1, v2, v3]
        
        for v in vertices:
            if abs(v.real) <= x_limit and abs(v.imag) <= y_limit:
                return True
        
        centro = (v1 + v2 + v3) / 3
        return abs(centro.real) <= x_limit and abs(centro.imag) <= y_limit
    
    def should_use_accent_svg(triangle, pattern):
        """Patrón de acento para SVG"""
        if pattern is None or pattern == 'Ninguno':
            return False
            
        shape, v1, v2, v3 = triangle
        center = (v1 + v2 + v3) / 3
        distance = abs(center)
        angle = cmath.phase(center) % (2 * math.pi)
        
        # Patrones originales
        if pattern == 'center_star':
            return distance < 0.3
        elif pattern == 'outer_ring':
            return distance > 0.6 and distance < 0.8
        elif pattern == 'radial_bands':
            band_angle = angle * 6 / (2 * math.pi)
            return int(band_angle) % 2 == 0 and distance < 0.7
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
        
        # NUEVOS PATRONES
        elif pattern == 'geometric_burst':
            burst_rays = 8
            ray_angle = angle * burst_rays / (2 * math.pi)
            in_ray = abs(ray_angle - round(ray_angle)) < 0.3
            return in_ray and distance > 0.2 and distance < 0.7
        
        elif pattern == 'wave_pattern':
            wave_freq = 4
            wave_amplitude = 0.2
            wave_center = 0.5
            wave_function = wave_center + wave_amplitude * math.sin(angle * wave_freq)
            return abs(distance - wave_function) < 0.1
        
        elif pattern == 'triangular_grid':
            x, y = center.real, center.imag
            grid_size = 0.3
            grid_x = int(x / grid_size)
            grid_y = int(y / grid_size)
            return (grid_x + grid_y) % 3 == 0 and distance < 0.8
        
        elif pattern == 'hexagonal_core':
            hex_radius = 0.4
            if distance > hex_radius:
                return False
            hex_angle = angle * 3 / math.pi
            hex_sector = int(hex_angle) % 6
            return hex_sector % 2 == 0
        
        elif pattern == 'lightning_bolt':
            x, y = center.real, center.imag
            zigzag_freq = 6
            zigzag_amplitude = 0.15
            zigzag_path = zigzag_amplitude * math.sin(y * zigzag_freq)
            bolt_width = 0.08
            return abs(x - zigzag_path) < bolt_width and abs(y) < 0.6
        
        elif pattern == 'celtic_knot':
            knot_freq = 3
            knot_phase1 = math.sin(angle * knot_freq)
            knot_phase2 = math.cos(angle * knot_freq + math.pi/4)
            knot_function = 0.4 + 0.2 * knot_phase1 * knot_phase2
            return abs(distance - knot_function) < 0.1
        
        elif pattern == 'mandala_rings':
            ring_count = 5
            ring_spacing = 0.12
            mandala_detail = math.sin(angle * 8) * 0.03
            for i in range(1, ring_count + 1):
                ring_radius = i * ring_spacing + mandala_detail
                if abs(distance - ring_radius) < 0.04:
                    return True
            return False
        
        elif pattern == 'fractal_branch':
            branch_angle1 = math.pi / 4
            branch_angle2 = 3 * math.pi / 4
            branch_angle3 = 5 * math.pi / 4
            branch_angle4 = 7 * math.pi / 4
            
            branch_tolerance = 0.2
            branch_angles = [branch_angle1, branch_angle2, branch_angle3, branch_angle4]
            
            for b_angle in branch_angles:
                angle_diff = abs(angle - b_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                if angle_diff < branch_tolerance and distance > 0.1 and distance < 0.8:
                    secondary_freq = distance * 10
                    if math.sin(secondary_freq) > 0.3:
                        return True
            return False
        
        return False

    
    def coordenada_svg(punto_complejo):
        """Convertir coordenada compleja a coordenadas SVG"""
        x = center_x + punto_complejo.real * escala
        y = center_y + punto_complejo.imag * escala
        return x, y
    
    # Generar triángulos
    triangles = generate_penrose_for_svg()
    triangles_en_rectangulo = [t for t in triangles if triangulo_esta_en_rectangulo_svg(t)]
    
    # Comenzar SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_width}cm" height="{svg_height}cm" viewBox="0 0 {svg_width} {svg_height}" 
     xmlns="http://www.w3.org/2000/svg">
<title>Mural Penrose {ancho_cm}x{alto_cm}cm - Paleta {paleta_nombre}</title>
<desc>Generado para fabricación - Cada triángulo = {lado_triangulo_cm}cm</desc>

<!-- Fondo blanco -->
<rect width="100%" height="100%" fill="white"/>

<!-- Patrón Penrose -->
<g id="patron-penrose">
'''
    
    # Contadores para metadatos
    contadores_svg = {'thin': {}, 'thick': {}, 'accent': {}}
    for tex_name in texturas_disponibles:
        contadores_svg['thin'][tex_name] = 0
        contadores_svg['thick'][tex_name] = 0
        contadores_svg['accent'][tex_name] = 0
    
    # Agregar cada triángulo
    triangle_id = 0
    for triangle in triangles_en_rectangulo:
        shape, v1, v2, v3 = triangle
        triangle_id += 1
        
        # Convertir coordenadas
        x1, y1 = coordenada_svg(v1)
        x2, y2 = coordenada_svg(v2)
        x3, y3 = coordenada_svg(v3)
        
        # Determinar textura y color
        if should_use_accent_svg(triangle, accent_pattern):
            texture_name = texturas_disponibles[2] if len(texturas_disponibles) > 2 else texturas_disponibles[0]
            categoria = 'accent'
            contadores_svg['accent'][texture_name] += 1
        elif shape == "thin":
            texture_name = texturas_disponibles[0] if len(texturas_disponibles) > 0 else 'default'
            categoria = 'thin'
            contadores_svg['thin'][texture_name] += 1
        else:  # thick
            texture_name = texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
            categoria = 'thick'
            contadores_svg['thick'][texture_name] += 1
        
        color_svg = get_svg_color(texture_name)
        
        # Crear elemento triángulo
        svg_content += f'''  <polygon points="{x1:.2f},{y1:.2f} {x2:.2f},{y2:.2f} {x3:.2f},{y3:.2f}"
           fill="{color_svg}" 
           stroke="black" 
           stroke-width="0.1"
           id="triangulo-{triangle_id}"
           data-tipo="{shape}"
           data-textura="{texture_name}"
           data-categoria="{categoria}"
           data-tamaño="{lado_triangulo_cm}cm" />
'''
    
    # Marco del mural
    margen = 5  # 5cm de margen
    svg_content += f'''
</g>

<!-- Marco del mural -->
<rect x="{margen}" y="{margen}" 
      width="{svg_width - 2*margen}" height="{svg_height - 2*margen}" 
      fill="none" stroke="black" stroke-width="2"/>

<!-- Información del mural -->
<text x="10" y="{svg_height - 10}" font-family="Arial" font-size="12" fill="black">
  Mural {ancho_cm}×{alto_cm}cm | Paleta: {paleta_nombre} | Triángulos: {len(triangles_en_rectangulo)}
</text>

</svg>'''
    
    # Calcular materiales exactos (mismo cálculo que la función principal)
    area_total_cm2 = ancho_cm * alto_cm
    area_triangulo_cm2 = (lado_triangulo_cm ** 2) * 0.433
    triangulos_estimados = int(area_total_cm2 / area_triangulo_cm2 * 0.85)
    
    return svg_content, {
        'formato': 'SVG',
        'dimensiones_cm': (ancho_cm, alto_cm),
        'total_triangulos_calculados': triangulos_estimados,
        'triangulos_en_svg': len(triangles_en_rectangulo),
        'contadores_svg': contadores_svg,
        'paleta': paleta_nombre,
        'texturas_usadas': texturas_disponibles,
        'lado_triangulo_cm': lado_triangulo_cm,
        'es_vectorial': True,
        'compatible_corte_laser': True,
        'escalable_sin_perdida': True
    }

def create_svg_download_link(svg_content, filename):
    """Crea link de descarga para SVG"""
    import base64
    
    svg_b64 = base64.b64encode(svg_content.encode('utf-8')).decode()
    href = f'<a href="data:image/svg+xml;base64,{svg_b64}" download="{filename}">📥 Descargar {filename}</a>'
    return href



    
def create_download_link(img, filename):
    """Crea un link de descarga para la imagen"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 Descargar {filename}</a>'
    return href


def extraer_colores_dominantes(imagen_path, n_colores=5):
    """
    Extrae los colores dominantes de una imagen usando K-means clustering
    """
    # Cargar imagen
    img = Image.open(imagen_path).convert('RGB')
    
    # Redimensionar para procesar más rápido
    img = img.resize((150, 150), Image.Resampling.LANCZOS)
    
    # Convertir a array numpy
    img_array = np.array(img)
    
    # Reshape para clustering (pixels como filas)
    pixels = img_array.reshape((-1, 3))
    
    # Aplicar K-means clustering
    kmeans = KMeans(n_clusters=n_colores, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Obtener colores dominantes
    colores_dominantes = kmeans.cluster_centers_.astype(int)
    
    # Calcular frecuencia de cada color
    labels = kmeans.labels_
    frecuencias = np.bincount(labels) / len(labels)
    
    # Ordenar por frecuencia
    indices_ordenados = np.argsort(frecuencias)[::-1]
    colores_ordenados = colores_dominantes[indices_ordenados]
    frecuencias_ordenadas = frecuencias[indices_ordenados]
    
    return colores_ordenados, frecuencias_ordenadas

def rgb_a_hsl(r, g, b):
    """Convierte RGB a HSL para análisis de armonía"""
    return colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)

def encontrar_texturas_similares(color_objetivo, texturas_dict):
    """
    Encuentra las texturas más similares al color objetivo
    """
    mejores_matches = []
    
    for nombre_textura, info_textura in texturas_dict.items():
        # Obtener color promedio de la textura
        img_array = info_textura['array']
        if len(img_array.shape) == 3:
            color_promedio = np.mean(img_array, axis=(0, 1))[:3]
        else:
            continue
            
        # Calcular distancia euclidiana en espacio RGB
        distancia = np.sqrt(np.sum((color_objetivo - color_promedio) ** 2))
        
        mejores_matches.append((nombre_textura, distancia, color_promedio))
    
    # Ordenar por distancia (menor = más similar)
    mejores_matches.sort(key=lambda x: x[1])
    
    return mejores_matches

def generar_paleta_automatica(imagen_path, texturas_dict, nombre_paleta="Auto-Generada"):
    """
    Genera automáticamente una paleta basada en una imagen de referencia
    """
    try:
        # Extraer colores dominantes
        colores_dominantes, frecuencias = extraer_colores_dominantes(imagen_path, n_colores=8)
        
        # Analizar armonía de colores
        colores_hsl = []
        for color in colores_dominantes:
            h, l, s = rgb_a_hsl(color[0], color[1], color[2])
            colores_hsl.append((h, s, l, color))
        
        # Seleccionar colores para paleta basado en criterios de armonía
        paleta_final = []
        texturas_seleccionadas = []
        
        # 1. Color principal (más frecuente con buena saturación)
        for h, s, l, rgb in colores_hsl:
            if s > 0.3 and l > 0.2 and l < 0.8:  # Evitar colores muy desaturados o extremos
                matches = encontrar_texturas_similares(rgb, texturas_dict)
                if matches and matches[0][0] not in texturas_seleccionadas:
                    texturas_seleccionadas.append(matches[0][0])
                    paleta_final.append(rgb)
                    break
        
        # 2. Color complementario o análogo
        if len(paleta_final) > 0:
            color_base_h = colores_hsl[0][0]
            
            for h, s, l, rgb in colores_hsl[1:]:
                # Buscar color análogo (30-60 grados de diferencia) o complementario (180 grados)
                diff_h = abs(h - color_base_h)
                if diff_h > 0.5:
                    diff_h = 1.0 - diff_h
                
                if (0.08 < diff_h < 0.17) or (0.4 < diff_h < 0.6):  # Análogo o complementario
                    matches = encontrar_texturas_similares(rgb, texturas_dict)
                    if matches and matches[0][0] not in texturas_seleccionadas:
                        texturas_seleccionadas.append(matches[0][0])
                        paleta_final.append(rgb)
                        break
        
        # 3. Color de acento (más saturado o contrastante)
        if len(paleta_final) < 3:
            for h, s, l, rgb in colores_hsl:
                if s > 0.5 or l < 0.3 or l > 0.7:  # Color con características especiales
                    matches = encontrar_texturas_similares(rgb, texturas_dict)
                    if matches and matches[0][0] not in texturas_seleccionadas:
                        texturas_seleccionadas.append(matches[0][0])
                        paleta_final.append(rgb)
                        break
        
        # Completar con mejores matches si faltan colores
        while len(texturas_seleccionadas) < 3 and len(colores_dominantes) > len(texturas_seleccionadas):
            color_restante = colores_dominantes[len(texturas_seleccionadas)]
            matches = encontrar_texturas_similares(color_restante, texturas_dict)
            
            for match in matches:
                if match[0] not in texturas_seleccionadas:
                    texturas_seleccionadas.append(match[0])
                    break
        
        # Asegurar que tenemos exactamente 3 texturas
        if len(texturas_seleccionadas) < 3:
            # Completar con texturas disponibles
            for nombre_textura in texturas_dict.keys():
                if nombre_textura not in texturas_seleccionadas:
                    texturas_seleccionadas.append(nombre_textura)
                    if len(texturas_seleccionadas) == 3:
                        break
        
        # Crear descripción automática
        descripcion = f"🤖 {nombre_paleta} - Generada por IA"
        teoria = "Paleta extraída automáticamente de imagen de referencia usando análisis de color dominante"
        
        return {
            'texturas': texturas_seleccionadas[:3],
            'descripcion': descripcion,
            'teoria': teoria,
            'colores_originales': [tuple(color) for color in colores_dominantes[:3]],
            'imagen_origen': imagen_path
        }
        
    except Exception as e:
        return None

# Integración en Streamlit
def agregar_generador_ai_a_streamlit(texturas_dict):
    """
    Agrega la funcionalidad de generación automática a la interfaz
    """
    st.markdown("#### 🤖 Generador Automático de Paletas")
    
    uploaded_file = st.file_uploader(
        "Sube una imagen de referencia:",
        type=['png', 'jpg', 'jpeg'],
        help="La IA analizará los colores dominantes y creará una paleta automáticamente"
    )
    
    if uploaded_file is not None:
        # Mostrar imagen subida
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(uploaded_file, caption="Imagen de referencia", use_column_width=True)
        
        with col2:
            if st.button("🎨 Generar Paleta Automática"):
                with st.spinner("🤖 Analizando colores..."):
                    # Guardar imagen temporalmente
                    temp_path = f"temp_ref_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Generar paleta
                    paleta_ai = generar_paleta_automatica(temp_path, texturas_dict)
                    
                    # Limpiar archivo temporal
                    import os
                    os.remove(temp_path)
                    
                    if paleta_ai:
                        st.success("✅ Paleta generada automáticamente!")
                        
                        # Mostrar paleta generada
                        st.write(f"**{paleta_ai['descripcion']}**")
                        st.write(f"*{paleta_ai['teoria']}*")
                        st.write(f"**Texturas seleccionadas:** {', '.join(paleta_ai['texturas'])}")
                        
                        # Guardar en session state para usar
                        st.session_state['paleta_ai_generada'] = paleta_ai
                        
                        # Botón para aplicar
                        if st.button("✨ Usar Esta Paleta"):
                            # Agregar a PALETAS_TEXTURAS temporalmente
                            PALETAS_TEXTURAS['AI-Generada'] = paleta_ai
                            st.success("Paleta agregada! Ahora puedes seleccionarla en el generador.")
                            st.rerun()
                    else:
                        st.error("❌ Error generando paleta automática")







def main():
    # Header principal   ya en el CSS INICIAL
    
    
    # Cargar texturas
    with st.spinner('🔄 Cargando texturas...'):
        texturas_dict, texturas_encontradas, texturas_faltantes = cargar_texturas_streamlit()
    
    # Mostrar estado de carga de texturas
    if texturas_encontradas:
        st.success(f"✅ Texturas cargadas: {len(texturas_encontradas)}")
        with st.expander("Ver texturas disponibles"):
            cols = st.columns(4)
            for i, tex_nombre in enumerate(texturas_encontradas[:12]):  # Mostrar máximo 8
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
    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Generador con Texturas", "📐 Mural Rectangular", "🔬 Análisis de Paletas", "📚 Galería de Patrones"])
    
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
                'diamond_cross', 'petal_flower', 'concentric_rings', 'geometric_burst',
                'wave_pattern', 'triangular_grid', 'hexagonal_core', 'lightning_bolt',
                'celtic_knot', 'mandala_rings', 'fractal_branch'],
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
                    (3600, 3600, "Impresión profesional")
                    
                ],
                index=0,
                format_func=lambda x: f"{x[0]}x{x[1]} px - {x[2]}"
            )
            
            # Control de escala de textura para murales
            escala_textura = st.slider(
                "🔍 Detalle de Textura por Triángulo:",
                min_value=1.0, max_value=4.0, value=1.5, step=0.1,
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
    
    

    with tab3:
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
    
    with tab2:
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
                        min_value=50, max_value=600, value=240, step=10,
                        help="Cualquier tamaño - la imagen se optimiza automáticamente"
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
                            min_value=50, max_value=1000, value=388, step=10,
                            help="Cualquier tamaño - la imagen se optimiza automáticamente"
                        )
                else:
                    alto_mural = tipo_pared[1]
                    ancho_mural = tipo_pared[2]
                # Información del área (sin restricciones)
                area_total = ancho_mural * alto_mural
                area_m2 = area_total / 10000
               
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
                [
                    'Ninguno', 'center_star', 'outer_ring', 'radial_bands', 'spiral_arms', 
                    'diamond_cross', 'petal_flower', 'concentric_rings', 'geometric_burst',
                    'wave_pattern', 'triangular_grid', 'hexagonal_core', 'lightning_bolt',
                    'celtic_knot', 'mandala_rings', 'fractal_branch'
                ],
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
                        img_rect, stats_rect = generar_mural_rectangular_penrose_simplificado(
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
                • Mural: {stats_rect['dimensiones_cm'][0]} × {stats_rect['dimensiones_cm'][1]} cm
                • Visualización: {stats_rect['dimensiones_px'][0]} × {stats_rect['dimensiones_px'][1]} px
                • Área total: {stats_rect['area_real_m2']:.2f} m²
                • Total triángulos calculados: {stats_rect['total_triangulos']:,}
            """)

                if stats_rect.get('es_visualizacion_simplificada'):
                    st.success("✅ Imagen optimizada automáticamente - Cálculos de materiales exactos")
                    
                
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
                    st.write(f"**Dimensiones:** {stats_rect['dimensiones_cm'][0]} × {stats_rect['dimensiones_cm'][1]} cm")
                    st.write(f"**Resolución generada:** {stats_rect['dimensiones_px'][0]} × {stats_rect['dimensiones_px'][1]} px")
                    st.write(f"**DPI:** Auto-optimizado")
                    st.write(f"**Total triángulos:** {stats_rect['total_triangulos']}")
                    st.write(f"**Tamaño de pieza:** {stats_rect['lado_triangulo_cm']} cm")
                    st.write(f"**Área total:** {(stats_rect['dimensiones_cm'][0] * stats_rect['dimensiones_cm'][1] / 10000):.2f} m²")
                
                with col_info2:
                    st.markdown("#### 🧮 Lista de Materiales")
                    
                    contadores = stats_rect['contadores']
                    
                    # Crear tabla de materiales
                    materiales_data = []
                    
                    for categoria, items in contadores.items():
                        for tex_name, cantidad in items.items():
                            if cantidad > 0:
                                if categoria == 'thin':
                                    tipo = "Delgado (solido)"  # Sin acento
                                elif categoria == 'thick':
                                    tipo = "Grueso (patron)"   # Sin acento
                                else:
                                    tipo = "Acento (especial)"

                                materiales_data.append({
                                    'Textura': tex_name,
                                    'Tipo': tipo,
                                    'Cantidad': cantidad,
                                    'Area_cm2': int(cantidad * stats_rect['lado_triangulo_cm']**2 * 0.4)  # Sin símbolo ²
                                })
                    
                    if materiales_data:
                        # Mostrar tabla de materiales
                        st.write("**Lista de materiales necesarios:**")
                        for item in materiales_data:
                            st.write(f"• **{item['Textura']}** ({item['Tipo']}): {item['Cantidad']} piezas - {item['Area_cm2']} cm²")
                        
                        # Resumen total
                        total_area = sum(item['Area_cm2'] for item in materiales_data)
                        st.write(f"**Área total de triángulos:** {total_area/10000:.2f} m²")
                    else:
                        st.write("No se generaron materiales")
                
                
                # Opciones de exportación
                st.markdown("#### 📤 Exportación")

                col_export1, col_export2, col_export3 = st.columns(3)

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
                    st.markdown("**📐 Archivo SVG Vectorial:**")
                    
                    if st.button("🎯 Generar SVG para Corte Láser", type="secondary"):
                        with st.spinner('🔄 Generando SVG vectorial...'):
                            try:
                                svg_content, svg_stats = generar_mural_svg(
                                    ancho_mural, alto_mural, mural_paleta, mural_accent, lado_triangulo, texturas_dict
                                )
                                
                                if svg_content:
                                    st.success("✅ SVG generado exitosamente!")
                                    
                                    # Información del SVG
                                    st.write(f"**Triángulos en SVG:** {svg_stats['triangulos_en_svg']}")
                                    st.write(f"**Tamaño archivo:** {len(svg_content.encode('utf-8'))/1024:.1f} KB")
                                    
                                    # Descarga SVG
                                    filename_svg = f"mural_CORTE_LASER_{stats_rect['paleta']}_{ancho_mural}x{alto_mural}cm.svg"
                                    svg_download_link = create_svg_download_link(svg_content, filename_svg)
                                    st.markdown(svg_download_link, unsafe_allow_html=True)
                                    
                                    # Guardar para reutilizar
                                    st.session_state['mural_svg'] = svg_content
                                    st.session_state['svg_filename'] = filename_svg
                                else:
                                    st.error("❌ Error generando SVG")
                            except Exception as e:
                                st.error(f"❌ Error SVG: {str(e)}")
                    
                    # Mostrar descarga si ya existe
                    if 'mural_svg' in st.session_state:
                        st.markdown("**📥 SVG Disponible:**")
                        svg_download_link = create_svg_download_link(
                            st.session_state['mural_svg'], 
                            st.session_state['svg_filename']
                        )
                        st.markdown(svg_download_link, unsafe_allow_html=True)
                    
                    st.info("""
                    **💡 Uso SVG:**
                    • Corte láser de precisión
                    • Escalable sin pérdida
                    • Cada triángulo = elemento separado
                    • Editable en Illustrator
                    """)

                with col_export3:
                    if materiales_data:
                        st.markdown("**📋 Lista de Materiales (CSV):**")
                        
                        # Crear CSV de materiales
                        import io
                        import csv
                        
                        csv_buffer = io.StringIO()
                        csv_writer = csv.DictWriter(csv_buffer, fieldnames=['Textura', 'Tipo', 'Cantidad', 'Area_cm2'])
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
                    else:
                        st.write("No se generaron materiales")
                        

            
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