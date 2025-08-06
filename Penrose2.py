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
    page_title="🧩 Generador Mosaicos Penrose",
    page_icon="🧩",
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
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def generate_penrose_tiles_streamlit(divisions, resolution, color_scheme, accent_pattern, line_width):
    """
    Versión optimizada para Streamlit del generador Penrose
    Retorna la imagen como array numpy para mostrar en Streamlit
    """
    
    # PALETAS DE COLORES SÓLIDOS
    color_palettes = {
        'ocean': {
            'thin': [0.2, 0.7, 0.7],
            'thick': [0.1, 0.4, 0.8],
            'outline': [0.05, 0.1, 0.2]
        },
        'sunset': {
            'thin': [1.0, 0.6, 0.2],
            'thick': [0.9, 0.3, 0.4],
            'outline': [0.3, 0.1, 0.1]
        },
        'forest': {
            'thin': [0.4, 0.8, 0.3],
            'thick': [0.2, 0.5, 0.2],
            'outline': [0.1, 0.2, 0.1]
        },
        'royal': {
            'thin': [0.6, 0.4, 0.9],
            'thick': [0.3, 0.2, 0.7],
            'outline': [0.1, 0.05, 0.2]
        },
        'autumn': {
            'thin': [0.9, 0.7, 0.3],
            'thick': [0.8, 0.4, 0.2],
            'outline': [0.3, 0.2, 0.1]
        },
        'mint': {
            'thin': [0.5, 0.9, 0.8],
            'thick': [0.3, 0.7, 0.6],
            'outline': [0.1, 0.3, 0.2]
        },
        'cherry': {
            'thin': [1.0, 0.7, 0.8],
            'thick': [0.8, 0.2, 0.4],
            'outline': [0.2, 0.05, 0.1]
        },
        'steel': {
            'thin': [0.7, 0.8, 0.9],
            'thick': [0.4, 0.5, 0.6],
            'outline': [0.1, 0.1, 0.2]
        }
    }
    
    # PATRONES DE ACENTOS
    accent_patterns = {
        'center_star': {
            'colors': {
                'thin': [1.0, 0.8, 0.0],
                'thick': [0.9, 0.0, 0.0]
            }
        },
        'outer_ring': {
            'colors': {
                'thin': [0.0, 0.9, 0.0],
                'thick': [0.0, 0.0, 0.9]
            }
        },
        'radial_bands': {
            'colors': {
                'thin': [0.9, 0.5, 0.0],
                'thick': [0.5, 0.0, 0.9]
            }
        },
        'spiral_arms': {
            'colors': {
                'thin': [1.0, 0.0, 0.5],
                'thick': [0.0, 0.8, 0.8]
            }
        },
        'diamond_cross': {
            'colors': {
                'thin': [0.9, 0.9, 0.0],
                'thick': [0.7, 0.0, 0.7]
            }
        },
        'petal_flower': {
            'colors': {
                'thin': [1.0, 0.4, 0.7],
                'thick': [0.3, 0.7, 0.3]
            }
        },
        'concentric_rings': {
            'colors': {
                'thin': [0.0, 0.6, 1.0],
                'thick': [1.0, 0.3, 0.0]
            }
        }
    }
    
    r1, r2 = resolution
    phi = (5 ** 0.5 + 1) / 2
    
    colors = color_palettes.get(color_scheme, color_palettes['ocean'])
    accent_colors = accent_patterns.get(accent_pattern, {}).get('colors', {})
    
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
    
    def should_use_accent_color(triangle, pattern):
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
    
    # Generar y renderizar
    triangles = generate_penrose_rhombi(divisions)
    
    # Dibujar rombos delgados
    for triangle in triangles:
        if triangle[0] == "thin":
            shape, v1, v2, v3 = triangle
            
            if should_use_accent_color(triangle, accent_pattern):
                color = accent_colors.get('thin', colors['thin'])
            else:
                color = colors['thin']
            
            ctx.move_to(v1.real, v1.imag)
            ctx.line_to(v2.real, v2.imag)
            ctx.line_to(v3.real, v3.imag)
            ctx.close_path()
            
            ctx.set_source_rgb(color[0], color[1], color[2])
            ctx.fill()
    
    # Dibujar rombos gruesos
    for triangle in triangles:
        if triangle[0] == "thick":
            shape, v1, v2, v3 = triangle
            
            if should_use_accent_color(triangle, accent_pattern):
                color = accent_colors.get('thick', colors['thick'])
            else:
                color = colors['thick']
            
            ctx.move_to(v1.real, v1.imag)
            ctx.line_to(v2.real, v2.imag)
            ctx.line_to(v3.real, v3.imag)
            ctx.close_path()
            
            ctx.set_source_rgb(color[0], color[1], color[2])
            ctx.fill()
    
    # Contornos si se solicitan
    if line_width > 0:
        ctx.set_line_width(line_width)
        ctx.set_source_rgb(colors['outline'][0], colors['outline'][1], colors['outline'][2])
        
        for triangle in triangles:
            shape, v1, v2, v3 = triangle
            
            ctx.move_to(v1.real, v1.imag)
            ctx.line_to(v2.real, v2.imag)
            ctx.line_to(v3.real, v3.imag)
            ctx.close_path()
            ctx.stroke()
    
    # Convertir a imagen PIL para Streamlit
    buf = surface.get_data()
    a = np.ndarray(shape=(r2, r1, 4), dtype=np.uint8, buffer=buf)
    a = a[:, :, [2, 1, 0, 3]]  # BGRA -> RGBA
    
    # Convertir a PIL Image
    img = Image.fromarray(a)
    
    # Calcular estadísticas
    thin_count = sum(1 for t in triangles if t[0] == 'thin')
    thick_count = len(triangles) - thin_count
    
    return img, {
        'total_pieces': len(triangles),
        'thin_pieces': thin_count,
        'thick_pieces': thick_count,
        'color_scheme': color_scheme,
        'accent_pattern': accent_pattern
    }

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
            <h1>🧩 Generador de Mosaicos Penrose Interactivo</h1>
            <p>Crea hermosos azulejos geométricos para imprimir y ensamblar</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con controles
    st.sidebar.markdown("## 🎨 Controles de Diseño")
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["🎨 Generador Básico", "⚙️ Generador Avanzado", "📚 Galería Preestablecida"])
    
    with tab1:
        st.markdown("### 🎯 Generación Rápida")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 🎨 Configuración")
            
            # Controles básicos
            color_scheme = st.selectbox(
                "🌈 Esquema de Color:",
                ['ocean', 'sunset', 'forest', 'royal', 'autumn', 'mint', 'cherry', 'steel'],
                help="Selecciona la paleta de colores principal"
            )
            
            accent_pattern = st.selectbox(
                "✨ Patrón de Acento:",
                ['Ninguno', 'center_star', 'outer_ring', 'radial_bands', 'spiral_arms', 
                 'diamond_cross', 'petal_flower', 'concentric_rings'],
                help="Agrega elementos especiales al diseño"
            )
            
            divisions = st.slider(
                "🔢 Subdivisiones:",
                min_value=4, max_value=8, value=6,
                help="Más divisiones = más detalle (pero tarda más)"
            )
            
            line_width = st.slider(
                "🖊️ Grosor de Líneas:",
                min_value=0.0, max_value=0.01, value=0.003, step=0.001,
                format="%.3f",
                help="0.0 = sin líneas, 0.01 = líneas gruesas"
            )
            
            resolution = st.selectbox(
                "📐 Resolución:",
                [(800, 800), (1200, 1200), (1600, 1600), (2400, 2400)],
                index=1,
                format_func=lambda x: f"{x[0]}x{x[1]} px"
            )
            
            generate_btn = st.button("🎨 Generar Mosaico", type="primary")
        
        with col2:
            if generate_btn:
                with st.spinner('🔄 Generando mosaico Penrose...'):
                    accent = accent_pattern if accent_pattern != 'Ninguno' else None
                    img, stats = generate_penrose_tiles_streamlit(
                        divisions, resolution, color_scheme, accent, line_width
                    )
                    
                    st.markdown("#### 🖼️ Vista Previa")
                    st.image(img, caption=f"Mosaico Penrose - {color_scheme.title()}", use_container_width=True)
                    
                    # Estadísticas
                    st.markdown("#### 📊 Estadísticas")
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    
                    with col_stats1:
                        st.metric("Total Piezas", stats['total_pieces'])
                    with col_stats2:
                        st.metric("Rombos Delgados", stats['thin_pieces'])
                    with col_stats3:
                        st.metric("Rombos Gruesos", stats['thick_pieces'])
                    
                    # Botón de descarga
                    filename = f"penrose_{color_scheme}_{accent_pattern}_{divisions}div.png"
                    download_link = create_download_link(img, filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # Guardar en session state para persistencia
                    st.session_state['last_image'] = img
                    st.session_state['last_stats'] = stats
                    st.session_state['last_filename'] = filename
            
            elif 'last_image' in st.session_state:
                st.markdown("#### 🖼️ Último Mosaico Generado")
                st.image(st.session_state['last_image'], use_container_width=True)
                
                # Mostrar estadísticas del último
                if 'last_stats' in st.session_state:
                    stats = st.session_state['last_stats']
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    
                    with col_stats1:
                        st.metric("Total Piezas", stats['total_pieces'])
                    with col_stats2:
                        st.metric("Rombos Delgados", stats['thin_pieces'])
                    with col_stats3:
                        st.metric("Rombos Gruesos", stats['thick_pieces'])
                
                # Botón de descarga del último
                if 'last_filename' in st.session_state:
                    download_link = create_download_link(
                        st.session_state['last_image'], 
                        st.session_state['last_filename']
                    )
                    st.markdown(download_link, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### ⚙️ Generación Avanzada - Múltiples Mosaicos")
        
        # Generación batch
        st.markdown("#### 🔄 Generación en Lote")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_schemes = st.multiselect(
                "🎨 Esquemas a Generar:",
                ['ocean', 'sunset', 'forest', 'royal', 'autumn', 'mint', 'cherry', 'steel'],
                default=['ocean', 'royal', 'forest']
            )
            
            selected_patterns = st.multiselect(
                "✨ Patrones a Aplicar:",
                ['Ninguno', 'center_star', 'outer_ring', 'radial_bands'],
                default=['Ninguno', 'center_star']
            )
            
            batch_resolution = st.selectbox(
                "📐 Resolución para Lote:",
                [(800, 800), (1200, 1200), (1600, 1600)],
                index=1,
                format_func=lambda x: f"{x[0]}x{x[1]} px"
            )
        
        with col2:
            batch_divisions = st.slider(
                "🔢 Subdivisiones para Lote:",
                min_value=4, max_value=7, value=6
            )
            
            batch_line_width = st.slider(
                "🖊️ Grosor de Líneas para Lote:",
                min_value=0.0, max_value=0.01, value=0.002, step=0.001,
                format="%.3f"
            )
            
            if st.button("🚀 Generar Lote Completo", type="primary"):
                total_combinations = len(selected_schemes) * len(selected_patterns)
                
                if total_combinations > 0:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    generated_images = []
                    current = 0
                    
                    for scheme in selected_schemes:
                        for pattern in selected_patterns:
                            current += 1
                            status_text.text(f"Generando {current}/{total_combinations}: {scheme} + {pattern}")
                            
                            accent = pattern if pattern != 'Ninguno' else None
                            img, stats = generate_penrose_tiles_streamlit(
                                batch_divisions, batch_resolution, scheme, accent, batch_line_width
                            )
                            
                            generated_images.append({
                                'image': img,
                                'stats': stats,
                                'scheme': scheme,
                                'pattern': pattern,
                                'filename': f"penrose_{scheme}_{pattern}_{batch_divisions}div.png"
                            })
                            
                            progress_bar.progress(current / total_combinations)
                    
                    status_text.text("✅ ¡Generación completada!")
                    
                    # Mostrar resultados en grid
                    st.markdown("#### 🖼️ Resultados Generados")
                    
                    cols_per_row = 3
                    for i in range(0, len(generated_images), cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for j, col in enumerate(cols):
                            if i + j < len(generated_images):
                                item = generated_images[i + j]
                                
                                with col:
                                    st.image(
                                        item['image'], 
                                        caption=f"{item['scheme']} + {item['pattern']}", 
                                        use_container_width=True
                                    )
                                    
                                    st.text(f"Piezas: {item['stats']['total_pieces']}")
                                    
                                    download_link = create_download_link(
                                        item['image'], 
                                        item['filename']
                                    )
                                    st.markdown(download_link, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### 📚 Galería de Patrones Preestablecidos")
        
        # Ejemplos predefinidos
        preset_configs = [
            {
                'name': '🌊 Océano Clásico',
                'scheme': 'ocean',
                'pattern': None,
                'divisions': 6,
                'description': 'El patrón original azul tradicional'
            },
            {
                'name': '👑 Royal con Estrella',
                'scheme': 'royal',
                'pattern': 'center_star',
                'divisions': 6,
                'description': 'Púrpura elegante con estrella dorada central'
            },
            {
                'name': '🌌 Galaxia Espiral',
                'scheme': 'steel',
                'pattern': 'spiral_arms',
                'divisions': 6,
                'description': 'Brazos espirales metálicos tipo galaxia'
            },
            {
                'name': '🌸 Pétalos de Flor',
                'scheme': 'mint',
                'pattern': 'petal_flower',
                'divisions': 6,
                'description': 'Suave menta con pétalos florales'
            },
            {
                'name': '🍂 Otoño con Bandas',
                'scheme': 'autumn',
                'pattern': 'radial_bands',
                'divisions': 6,
                'description': 'Colores otoñales con bandas radiales'
            },
            {
                'name': '🎯 Anillos Concéntricos',
                'scheme': 'cherry',
                'pattern': 'concentric_rings',
                'divisions': 6,
                'description': 'Rosa cereza con anillos alternados'
            }
        ]
        
        # Mostrar presets en grid
        cols = st.columns(2)
        
        for i, preset in enumerate(preset_configs):
            with cols[i % 2]:
                st.markdown(f"#### {preset['name']}")
                st.write(preset['description'])
                
                if st.button(f"Generar {preset['name']}", key=f"preset_{i}"):
                    with st.spinner(f'Generando {preset["name"]}...'):
                        img, stats = generate_penrose_tiles_streamlit(
                            preset['divisions'], (1200, 1200), preset['scheme'], 
                            preset['pattern'], 0.003
                        )
                        
                        st.image(img, caption=preset['name'], use_container_width=True)
                        
                        # Estadísticas
                        st.write(f"**Total piezas:** {stats['total_pieces']}")
                        
                        # Descarga
                        filename = f"preset_{preset['scheme']}_{preset['pattern'] or 'basic'}.png"
                        download_link = create_download_link(img, filename)
                        st.markdown(download_link, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>🧩 Generador de Mosaicos Penrose | Creado con Streamlit y Cairo</p>
            <p>💡 Cada mosaico puede ser impreso y cortado como azulejos individuales</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()