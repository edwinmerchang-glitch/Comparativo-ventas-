import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from data_processor import DataProcessor

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Ventas Restrepo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cargar estilos CSS
try:
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    # Si no existe el archivo CSS, usar estilos básicos
    st.markdown("""
    <style>
    .stApp { background-color: #f0f3f9; }
    .kpi-card { background: white; border: 1px solid #e2e7f0; border-radius: 12px; padding: 13px 15px; margin-bottom: 10px; }
    .klb { font-size: 10px; color: #5a6070; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
    .kv { font-size: 22px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
    .kd { font-size: 11px; font-weight: 600; }
    .up { color: #1D9E75; }
    .dn { color: #A32D2D; }
    .card { background: white; border: 1px solid #e2e7f0; border-radius: 12px; padding: 15px; margin-bottom: 11px; }
    .ct { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
    .cs { font-size: 11px; color: #9097a8; margin-bottom: 10px; }
    .sec { font-size: 13px; font-weight: 700; margin: 18px 0 9px; display: flex; align-items: center; gap: 6px; }
    .sec::before { content: ''; width: 3px; height: 15px; background: #185FA5; border-radius: 2px; display: inline-block; }
    .badge { background: #e6f1fb; color: #185FA5; font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 20px; border: 1px solid #b5d4f4; }
    .fbar { background: white; border: 1px solid #e2e7f0; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar procesador en sesión
if 'processor' not in st.session_state:
    st.session_state.processor = DataProcessor()
    st.session_state.data_loaded = False
    st.session_state.filters = {
        'years': [-1],
        'months': [-1],
        'producto': None,
        'marca': None,
        'provider': None,
        'mundo': None,
        'evento': None
    }

# Funciones helper
def fmt_number(n):
    return f"{int(round(n)):,}".replace(',', '.')

def fmt_k(n):
    abs_n = abs(n)
    if abs_n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    elif abs_n >= 1000:
        return f"{n/1000:.1f}K"
    return str(int(round(n)))

def pct_format(v):
    if v is None or np.isnan(v) or v == 99999:
        return 'Nuevo'
    if v > 1000:
        return 'Nuevo'
    signo = '+' if v > 0 else ''
    return f"{signo}{v:.1f}%"

# Header
col1, col2, col3 = st.columns([2, 1.5, 1.5])

with col1:
    st.markdown("### 📊 Dashboard de Ventas — Restrepo")
    if st.session_state.data_loaded and st.session_state.processor.df is not None:
        st.caption(f"{st.session_state.processor.df.shape[0]:,} registros · {len(st.session_state.processor.productos)} productos · {len(st.session_state.processor.marcas)} marcas")
    else:
        st.caption("Cargue un archivo Excel para comenzar el análisis")

with col2:
    st.markdown('<div style="text-align:right">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📂 Cargar Excel",
        type=['xlsx', 'xls'],
        key="excel_uploader",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    if st.session_state.data_loaded and st.session_state.processor.last_upload_time:
        st.markdown(f'<div class="badge" style="float:right">📅 Actualizado: {st.session_state.processor.last_upload_time.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge" style="float:right">⚠️ Sin datos cargados</div>', unsafe_allow_html=True)

# Cargar datos cuando se sube un archivo
if uploaded_file is not None:
    with st.spinner("Cargando y procesando datos..."):
        if st.session_state.processor.load_excel(uploaded_file):
            st.session_state.data_loaded = True
            st.success(f"✅ Datos cargados exitosamente: {st.session_state.processor.df.shape[0]} registros")
            st.rerun()
        else:
            st.error("❌ Error al cargar el archivo. Verifique que tenga las columnas: FECHA, CANTIDAD, PRODUCTO, MARCA, PROVEEDOR")

# Si no hay datos cargados, mostrar instrucciones
if not st.session_state.data_loaded:
    st.info("""
    ### 📋 Instrucciones para cargar datos:
    
    1. **Prepare su archivo Excel** con las siguientes columnas:
       - `FECHA` (obligatorio): Fecha de la transacción
       - `CANTIDAD` (obligatorio): Número de unidades vendidas
       - `PRODUCTO`: Nombre del producto
       - `MARCA`: Marca del producto
       - `PROVEEDOR`: Proveedor del producto
       - `MUNDO`: Categoría o mundo del producto (opcional)
       - `EVENTO`: Evento o campaña asociada (opcional)
       - `MATERIAL`: Código o referencia del material (opcional)
    
    2. **Haga clic en "Browse files"** y seleccione su archivo Excel
    
    3. **El dashboard se actualizará automáticamente** con sus datos
    """)
    
    # Mostrar ejemplo de formato
    with st.expander("📖 Ver ejemplo de formato esperado"):
        ejemplo = pd.DataFrame({
            'FECHA': ['2024-01-15', '2024-01-20', '2024-02-10'],
            'MATERIAL': ['MAT001', 'MAT002', 'MAT003'],
            'PRODUCTO': ['Producto A', 'Producto B', 'Producto C'],
            'CANTIDAD': [100, 150, 200],
            'PROVEEDOR': ['Proveedor X', 'Proveedor Y', 'Proveedor Z'],
            'MUNDO': ['Mundo 1', 'Mundo 2', 'Mundo 1'],
            'MARCA': ['Marca A', 'Marca B', 'Marca A'],
            'EVENTO': ['Black Friday', 'Cyber Monday', 'Normal']
        })
        st.dataframe(ejemplo, use_container_width=True)
    st.stop()

# ==================== FILTROS ====================
st.markdown('<div class="fbar">', unsafe_allow_html=True)

# Obtener años disponibles
available_years = st.session_state.processor.get_available_years()
meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Crear columnas para filtros
col_f1, col_f2, col_f3, col_f4, col_f5, col_f6, col_f7 = st.columns([0.8, 1, 1.2, 1, 1, 1, 0.5])

with col_f1:
    st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">📅 AÑO</label>', unsafe_allow_html=True)
    year_options = ["Todos"] + [str(y) for y in available_years]
    selected_years_text = st.selectbox("Año", year_options, key="year_filter", label_visibility="collapsed")
    
    if selected_years_text == "Todos":
        st.session_state.filters['years'] = [-1]
    else:
        st.session_state.filters['years'] = [int(selected_years_text)]

with col_f2:
    st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">📆 MES</label>', unsafe_allow_html=True)
    selected_months = st.multiselect("Mes", meses_nombres, key="month_filter", label_visibility="collapsed")
    
    if selected_months:
        st.session_state.filters['months'] = [meses_nombres.index(m) for m in selected_months]
    else:
        st.session_state.filters['months'] = [-1]

with col_f3:
    if st.session_state.processor.productos:
        st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">🏷️ PRODUCTO</label>', unsafe_allow_html=True)
        productos_opts = ["Todos"] + st.session_state.processor.productos[:100]
        producto_idx = st.selectbox("Producto", productos_opts, key="producto_filter", label_visibility="collapsed")
        st.session_state.filters['producto'] = None if producto_idx == "Todos" else producto_idx

with col_f4:
    if st.session_state.processor.marcas:
        st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">⭐ MARCA</label>', unsafe_allow_html=True)
        marcas_opts = ["Todas"] + st.session_state.processor.marcas[:50]
        marca_idx = st.selectbox("Marca", marcas_opts, key="marca_filter", label_visibility="collapsed")
        st.session_state.filters['marca'] = None if marca_idx == "Todas" else marca_idx

with col_f5:
    if st.session_state.processor.proveedores:
        st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">🏢 PROVEEDOR</label>', unsafe_allow_html=True)
        prov_opts = ["Todos"] + st.session_state.processor.proveedores[:50]
        prov_idx = st.selectbox("Proveedor", prov_opts, key="prov_filter", label_visibility="collapsed")
        st.session_state.filters['provider'] = None if prov_idx == "Todos" else prov_idx

with col_f6:
    if st.session_state.processor.mundos:
        st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">🌍 MUNDO</label>', unsafe_allow_html=True)
        mundo_opts = ["Todos"] + st.session_state.processor.mundos
        mundo_idx = st.selectbox("Mundo", mundo_opts, key="mundo_filter", label_visibility="collapsed")
        st.session_state.filters['mundo'] = None if mundo_idx == "Todos" else mundo_idx

with col_f7:
    st.markdown('<div style="margin-top: 18px;"></div>', unsafe_allow_html=True)
    if st.button("✕ Limpiar", key="reset_filters", use_container_width=True):
        st.session_state.filters = {
            'years': [-1],
            'months': [-1],
            'producto': None,
            'marca': None,
            'provider': None,
            'mundo': None,
            'evento': None
        }
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ==================== FILTRAR DATOS ====================
df_filtered = st.session_state.processor.filter_data(
    years=st.session_state.filters['years'],
    months=st.session_state.filters['months'],
    producto=st.session_state.filters.get('producto'),
    marca=st.session_state.filters.get('marca'),
    proveedor=st.session_state.filters.get('provider'),
    mundo=st.session_state.filters.get('mundo'),
    evento=st.session_state.filters.get('evento')
)

# Agregar datos filtrados
aggregated = st.session_state.processor.aggregate_data(df_filtered)

# Colores para gráficos
colores = ['#185FA5', '#1D9E75', '#D85A30', '#BA7517', '#534AB7', '#3B6D11', '#A32D2D', '#0F6E56', '#854F0B', '#3C3489']

# ==================== KPIs ====================
st.markdown('<div class="krow" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;">', unsafe_allow_html=True)

# Calcular variación
years_list = sorted(aggregated['by_year'].keys())
if len(years_list) >= 2:
    y1, y2 = years_list[-2], years_list[-1]
    val1 = aggregated['by_year'].get(y1, 0)
    val2 = aggregated['by_year'].get(y2, 0)
    if val1 > 0:
        pct_change = ((val2 - val1) / val1 * 100)
        pct_html = f'<span class="up">▲ {abs(pct_change):.1f}%</span>' if pct_change >= 0 else f'<span class="dn">▼ {abs(pct_change):.1f}%</span>'
        cambio_texto = f"{pct_html} {y1}→{y2}"
    else:
        cambio_texto = "Sin datos previos"
else:
    cambio_texto = "Seleccione más años"

# Top líderes
top_producto = list(aggregated['by_product'].items())[0] if aggregated['by_product'] else ('—', 0)
top_marca = list(aggregated['by_brand'].items())[0] if aggregated['by_brand'] else ('—', 0)
top_proveedor = list(aggregated['by_provider'].items())[0] if aggregated['by_provider'] else ('—', 0)

kpi_data = [
    ('kbl', '📦 Unidades totales', fmt_number(aggregated['total']), cambio_texto),
    ('ktl', '🧾 Transacciones', fmt_number(aggregated['total_records']), f"{len(years_list)} años analizados"),
    ('kco', '🏆 Producto líder', top_producto[0][:25] if len(top_producto[0]) > 25 else top_producto[0], f"{fmt_number(top_producto[1])} unidades"),
    ('kam', '⭐ Marca líder', top_marca[0][:25] if len(top_marca[0]) > 25 else top_marca[0], f"{fmt_number(top_marca[1])} unidades"),
    ('kpu', '🏢 Proveedor líder', top_proveedor[0][:20] if len(top_proveedor[0]) > 20 else top_proveedor[0], f"{fmt_number(top_proveedor[1])} unidades")
]

for clase, label, valor, detalle in kpi_data:
    st.markdown(f'''
    <div class="kpi-card" style="position:relative;overflow:hidden">
        <div style="position:absolute;top:0;left:0;width:4px;height:100%;background:{'#185FA5' if 'kbl' in clase else '#1D9E75' if 'ktl' in clase else '#D85A30' if 'kco' in clase else '#BA7517' if 'kam' in clase else '#534AB7'};border-radius:3px 0 0 3px"></div>
        <div class="klb">{label}</div>
        <div class="kv">{valor}</div>
        <div class="kd">{detalle}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==================== GRÁFICO DE TENDENCIA ====================
st.markdown('<div class="sec">📈 Tendencia mensual</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Evolución mensual de unidades vendidas</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Comparativa interanual según filtros seleccionados</div>', unsafe_allow_html=True)
    
    if aggregated['monthly_by_year']:
        fig_line = go.Figure()
        
        for i, year in enumerate(sorted(aggregated['monthly_by_year'].keys())):
            fig_line.add_trace(go.Scatter(
                x=meses_nombres,
                y=aggregated['monthly_by_year'][year],
                name=str(year),
                line=dict(color=colores[i % len(colores)], width=2.5),
                fill='tozeroy',
                fillcolor=f"{colores[i % len(colores)]}20",
                mode='lines+markers',
                marker=dict(size=6)
            ))
        
        fig_line.update_layout(
            height=250,
            margin=dict(l=40, r=20, t=20, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified'
        )
        fig_line.update_xaxes(gridcolor='rgba(0,0,0,0.05)', showgrid=True, gridwidth=0.5)
        fig_line.update_yaxes(gridcolor='rgba(0,0,0,0.05)', tickformat=',.0f', showgrid=True, gridwidth=0.5)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar la tendencia")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== GRÁFICOS DE BARRAS ====================
col_g2_1, col_g2_2 = st.columns(2)

with col_g2_1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Total de unidades por año</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Volumen acumulado según filtros activos</div>', unsafe_allow_html=True)
    
    years_list = sorted(aggregated['by_year'].keys())
    if years_list:
        values_list = [aggregated['by_year'].get(year, 0) for year in years_list]
        
        fig_year = go.Figure(data=[
            go.Bar(
                x=[str(y) for y in years_list],
                y=values_list,
                marker_color=colores[:len(years_list)],
                text=[fmt_k(v) for v in values_list],
                textposition='outside',
                textfont=dict(size=11, weight='bold')
            )
        ])
        fig_year.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
        fig_year.update_yaxes(tickformat=',.0f')
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.info("No hay datos de años para mostrar")
    st.markdown('</div>', unsafe_allow_html=True)

with col_g2_2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Distribución por mes</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Total de unidades por mes (todos los años)</div>', unsafe_allow_html=True)
    
    if aggregated['by_month']:
        max_m = max(aggregated['by_month']) if aggregated['by_month'] else 0
        colors_m = [colores[2] if v == max_m and v > 0 else colores[0] for v in aggregated['by_month']]
        
        fig_month = go.Figure(data=[
            go.Bar(
                x=meses_nombres, 
                y=aggregated['by_month'], 
                marker_color=colors_m,
                text=[fmt_k(v) if v > 0 else '' for v in aggregated['by_month']],
                textposition='outside'
            )
        ])
        fig_month.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        fig_month.update_yaxes(tickformat=',.0f')
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("No hay datos de meses para mostrar")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== TOP MARCAS ====================
if aggregated['by_brand']:
    st.markdown('<div class="sec">⭐ Top Marcas</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="ct">Top 10 Marcas con mayor volumen</div>', unsafe_allow_html=True)
        st.markdown('<div class="cs">Análisis de participación por marca</div>', unsafe_allow_html=True)
        
        top_brands = list(aggregated['by_brand'].items())[:10]
        if top_brands:
            fig_brands = go.Figure(data=[
                go.Bar(
                    x=[v for k, v in top_brands],
                    y=[k[:30] + '…' if len(k) > 30 else k for k, v in top_brands],
                    orientation='h',
                    marker_color=colores[:len(top_brands)],
                    text=[fmt_k(v) for k, v in top_brands],
                    textposition='outside'
                )
            ])
            fig_brands.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            fig_brands.update_xaxes(tickformat=',.0f')
            fig_brands.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_brands, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== TABLA DE PRODUCTOS ====================
if aggregated['products_df'] is not None and not aggregated['products_df'].empty:
    st.markdown('<div class="sec">📋 Tabla comparativa de productos</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="ct">Comparativo anual por producto</div>', unsafe_allow_html=True)
        st.markdown('<div class="cs">Top 50 productos con variación interanual</div>', unsafe_allow_html=True)
        
        products_df = aggregated['products_df'].copy()
        
        # Formatear para mostrar
        display_df = products_df.head(20).copy()
        display_df['PRODUCTO'] = display_df['PRODUCTO'].apply(lambda x: x[:50] + '…' if len(x) > 50 else x)
        display_df['u2024'] = display_df['u2024'].apply(lambda x: f"{int(x):,}")
        display_df['u2025'] = display_df['u2025'].apply(lambda x: f"{int(x):,}")
        display_df['u2026'] = display_df['u2026'].apply(lambda x: f"{int(x):,}")
        display_df['diff_2425'] = display_df['diff_2425'].apply(lambda x: f"{int(x):,}")
        display_df['pct_2425'] = display_df['pct_2425'].apply(lambda x: pct_format(x))
        display_df['diff_2526'] = display_df['diff_2526'].apply(lambda x: f"{int(x):,}")
        display_df['pct_2526'] = display_df['pct_2526'].apply(lambda x: pct_format(x))
        
        st.dataframe(
            display_df[['PRODUCTO', 'u2024', 'u2025', 'u2026', 'diff_2425', 'pct_2425', 'diff_2526', 'pct_2526']],
            column_config={
                'PRODUCTO': st.column_config.TextColumn('Producto', width='medium'),
                'u2024': st.column_config.TextColumn('2024', help='Unidades vendidas en 2024'),
                'u2025': st.column_config.TextColumn('2025', help='Unidades vendidas en 2025'),
                'u2026': st.column_config.TextColumn('2026', help='Unidades vendidas en 2026'),
                'diff_2425': st.column_config.TextColumn('Δ 24→25', help='Diferencia 2024 vs 2025'),
                'pct_2425': st.column_config.TextColumn('% 24→25', help='Porcentaje de cambio'),
                'diff_2526': st.column_config.TextColumn('Δ 25→26', help='Diferencia 2025 vs 2026'),
                'pct_2526': st.column_config.TextColumn('% 25→26', help='Porcentaje de cambio'),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("---")
st.caption(f"📊 Dashboard de Ventas — Datos actualizados al {datetime.now().strftime('%d/%m/%Y %H:%M')} | Desarrollado con Streamlit")