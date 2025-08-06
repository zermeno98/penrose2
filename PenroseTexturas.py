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
                # Redimensionar para optimizar rendimiento
                if texture.size[0] > 500 or texture.size[1] > 500:
                    texture = texture.resize((300, 300), Image.Resampling.LANCZOS)
                
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

def crear_patron_textura_cairo(textura_info, ancho, alto):
    """Crea un patrón de textura para Cairo"""
    if textura_info is None:
        return None
    
    # Convertir PIL a surface de Cairo
    texture_pil = textura_info['pil']
    
    # Redimensionar si es necesario
    if texture_pil.size != (ancho, alto):
        texture_pil = texture_pil.resize((ancho, alto), Image.Resampling.LANCZOS)
    
    # Convertir a RGBA si no lo está
    if texture_pil.mode != 'RGBA':
        texture_pil = texture_pil.convert('RGBA')
    
    # Crear surface de Cairo
    texture_array = np.array(texture_pil)
    height, width = texture_array.shape[:2]
    
    # Crear surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    
    # Convertir array numpy a formato Cairo (BGRA)
    if len(texture_array.shape) == 3:
        # Reordenar canales RGBA -> BGRA
        bgra_array = texture_array[:, :, [2, 1, 0, 3]] if texture_array.shape[2] == 4 else texture_array[:, :, [2, 1, 0]]
    else:
        bgra_array = texture_array
    
    # Copiar datos a la surface
    buf = surface.get_data()
    buf[:] = bgra_array.flatten()
    surface.mark_dirty()
    
    # Crear patrón
    pattern = cairo.SurfacePattern(surface)
    pattern.set_extend(cairo.EXTEND_REPEAT)
    
    return pattern

@st.cache_data
def generate_penrose_tiles_with_textures(divisions, resolution, paleta_nombre, accent_pattern, line_width, _texturas_dict):
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
    
    # Preparar patrones de texturas
    texture_size = 200  # Tamaño optimizado para rendimiento
    
    # Crear patrones para triángulos delgados y gruesos
    thin_texture_name = texturas_disponibles[0] if len(texturas_disponibles) > 0 else None
    thick_texture_name = texturas_disponibles[1] if len(texturas_disponibles) > 1 else texturas_disponibles[0]
    accent_texture_name = texturas_disponibles[2] if len(texturas_disponibles) > 2 else texturas_disponibles[0]
    
    thin_pattern = crear_patron_textura_cairo(_texturas_dict.get(thin_texture_name), texture_size, texture_size)
    thick_pattern = crear_patron_textura_cairo(_texturas_dict.get(thick_texture_name), texture_size, texture_size)
    accent_pattern_obj = crear_patron_textura_cairo(_texturas_dict.get(accent_texture_name), texture_size, texture_size)
    
    # Generar triángulos
    triangles = generate_penrose_rhombi(divisions)
    
    # Renderizar triángulos con texturas
    for triangle in triangles:
        shape, v1, v2, v3 = triangle
        
        # Crear path del triángulo
        ctx.move_to(v1.real, v1.imag)
        ctx.line_to(v2.real, v2.imag)
        ctx.line_to(v3.real, v3.imag)
        ctx.close_path()
        
        # Seleccionar textura
        if should_use_accent_texture(triangle, accent_pattern):
            pattern = accent_pattern_obj
        elif shape == "thin":
            pattern = thin_pattern
        else:
            pattern = thick_pattern
        
        # Aplicar textura
        if pattern:
            ctx.set_source(pattern)
            ctx.fill_preserve()
        else:
            # Fallback a color sólido si no hay textura
            if shape == "thin":
                ctx.set_source_rgb(0.3, 0.7, 0.9)
            else:
                ctx.set_source_rgb(0.1, 0.4, 0.8)
            ctx.fill_preserve()
        
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
        'accent_pattern': accent_pattern
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

def create_download_link(img, filename):
    """Crea un link de descarga para la imagen"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 Descargar {filename}</a>'
    return href

def main():
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
    tab1, tab2, tab3 = st.tabs(["🎨 Generador con Texturas", "🔬 Análisis de Paletas", "📚 Galería de Patrones"])
    
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
                [(800, 800), (1200, 1200), (1600, 1600)],
                index=1,
                format_func=lambda x: f"{x[0]}x{x[1]} px"
            )
            
            generate_btn = st.button("🎨 Generar Mosaico con Texturas", type="primary")
        
        with col2:
            if generate_btn and texturas_dict:
                with st.spinner('🔄 Generando mosaico con texturas...'):
                    accent = accent_pattern if accent_pattern != 'Ninguno' else None
                    img, stats = generate_penrose_tiles_with_textures(
                        divisions, resolution, paleta_seleccionada, accent, line_width, texturas_dict
                    )
                    
                    if img:
                        st.markdown("#### 🖼️ Mosaico Generado")
                        st.image(img, caption=f"Mosaico Penrose - Paleta {paleta_seleccionada}", use_container_width=True)
                        
                        # Estadísticas
                        st.markdown("#### 📊 Estadísticas")
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        
                        with col_stats1:
                            st.metric("Total Piezas", stats['total_pieces'])
                        with col_stats2:
                            st.metric("Triángulos Delgados", stats['thin_pieces'])
                        with col_stats3:
                            st.metric("Triángulos Gruesos", stats['thick_pieces'])
                        
                        # Información de texturas usadas
                        st.markdown("#### 🎨 Texturas Aplicadas")
                        st.write(f"**Paleta:** {stats['paleta']}")
                        st.write(f"**Texturas usadas:** {', '.join(stats['texturas_usadas'])}")
                        
                        # Botón de descarga
                        filename = f"penrose_texturas_{paleta_seleccionada}_{accent_pattern}_{divisions}div.png"
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
                                    5, (800, 800), paleta_nombre, None, 0.002, texturas_dict
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
            <p>🎨 Generador de Mosaicos Penrose con Texturas | Basado en Teoría del Color</p>
            <p>💡 Paletas diseñadas siguiendo principios de armonía cromática</p>
            <p>🔧 Tecnologías: Streamlit, Cairo, PIL, NumPy</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()