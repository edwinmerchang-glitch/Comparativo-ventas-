import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inicializar procesador en sesión
if 'processor' not in st.session_state:
    st.session_state.processor = DataProcessor()
    st.session_state.data_loaded = False
    st.session_state.current_data = None
    st.session_state.aggregated = None

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
    signo = '+' if v > 0 else ''
    return f"{signo}{v:.1f}%"

# Header
col1, col2, col3 = st.columns([2, 1.5, 1.5])

with col1:
    st.markdown("### 📊 Dashboard de Ventas — Restrepo")
    if st.session_state.data_loaded:
        st.caption(f"{st.session_state.processor.df.shape[0]:,} registros · Datos actualizados: {st.session_state.processor.last_upload_time.strftime('%d/%m/%Y %H:%M')}")
    else:
        st.caption("Cargue un archivo Excel para comenzar")

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
    if st.session_state.data_loaded:
        st.markdown(f'<div class="badge" style="float:right">Actualizado: {st.session_state.processor.last_upload_time.strftime("%d/%m")}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge" style="float:right">Esperando datos</div>', unsafe_allow_html=True)

# Cargar datos cuando se sube un archivo
if uploaded_file is not None:
    with st.spinner("Cargando datos..."):
        if st.session_state.processor.load_excel(uploaded_file):
            st.session_state.data_loaded = True
            st.session_state.filters = {
                'years': [-1],
                'months': [-1],
                'category': None,
                'marca': None,
                'provider': None
            }
            st.rerun()
        else:
            st.error("Error al cargar el archivo. Verifique el formato.")

# Si no hay datos cargados, mostrar mensaje
if not st.session_state.data_loaded:
    st.info("""
    ### 📋 Instrucciones:
    1. Prepare un archivo Excel con las siguientes columnas (mínimo):
       - **fecha** o **fechaventa**: Fecha de la transacción
       - **unidades** o **cantidad**: Número de unidades vendidas
       - **producto**: Nombre del producto (opcional para tabla)
       - **categoria**: Categoría del producto
       - **marca**: Marca del producto  
       - **proveedor**: Proveedor del producto
    
    2. Haga clic en "Browse files" para cargar su archivo
    
    3. El dashboard se actualizará automáticamente
    """)
    st.stop()

# Filtros
st.markdown('<div class="fbar">', unsafe_allow_html=True)

# Obtener años disponibles
available_years = st.session_state.processor.get_available_years()
available_years_map = {year: idx for idx, year in enumerate(available_years)}

# Filtros en fila
col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([1, 1.5, 1.2, 1.2, 1.2, 0.5])

with col_f1:
    st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">AÑO</label>', unsafe_allow_html=True)
    years_selected = []
    cols_y = st.columns(len(available_years) + 1)
    
    with cols_y[0]:
        if st.button("Todos", key="y_all", use_container_width=True):
            st.session_state.filters['years'] = [-1]
            st.rerun()
    
    for i, year in enumerate(available_years, 1):
        with cols_y[i]:
            btn_label = str(year)
            if st.button(btn_label, key=f"y_{year}", use_container_width=True):
                if -1 in st.session_state.filters['years']:
                    st.session_state.filters['years'] = [year]
                elif year in st.session_state.filters['years']:
                    st.session_state.filters['years'] = [-1] if len(st.session_state.filters['years']) == 1 else [y for y in st.session_state.filters['years'] if y != year]
                else:
                    st.session_state.filters['years'].append(year)
                st.rerun()

with col_f2:
    st.markdown('<label style="font-size:10px;font-weight:700;color:#5a6070">MES</label>', unsafe_allow_html=True)
    meses_nombres = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    meses_selected = st.multiselect("", meses_nombres, key="mes_filter", label_visibility="collapsed", 
                                     default=[] if -1 in st.session_state.filters['months'] else [meses_nombres[m] for m in st.session_state.filters['months'] if m != -1])
    
    if meses_selected:
        st.session_state.filters['months'] = [meses_nombres.index(m) for m in meses_selected]
    else:
        st.session_state.filters['months'] = [-1]

with col_f3:
    categorias_opts = ["Todas"] + st.session_state.processor.categorias
    cat_idx = st.selectbox("Categoría", categorias_opts, key="cat_filter")
    st.session_state.filters['category'] = None if cat_idx == "Todas" else cat_idx

with col_f4:
    marcas_opts = ["Todas"] + st.session_state.processor.marcas
    marca_idx = st.selectbox("Marca", marcas_opts, key="marca_filter")
    st.session_state.filters['marca'] = None if marca_idx == "Todas" else marca_idx

with col_f5:
    prov_opts = ["Todos"] + st.session_state.processor.proveedores
    prov_idx = st.selectbox("Proveedor", prov_opts, key="prov_filter")
    st.session_state.filters['provider'] = None if prov_idx == "Todos" else prov_idx

with col_f6:
    if st.button("✕ Limpiar", key="reset_filters", use_container_width=True):
        st.session_state.filters = {
            'years': [-1],
            'months': [-1],
            'category': None,
            'marca': None,
            'provider': None
        }
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Filtrar datos
df_filtered = st.session_state.processor.filter_data(
    years=st.session_state.filters['years'],
    months=st.session_state.filters['months'],
    category=st.session_state.filters['category'],
    marca=st.session_state.filters['marca'],
    provider=st.session_state.filters['provider']
)

# Agregar datos filtrados
aggregated = st.session_state.processor.aggregate_data(df_filtered)
meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
colores = ['#185FA5','#1D9E75','#D85A30','#BA7517','#534AB7','#3B6D11','#A32D2D','#0F6E56','#854F0B','#3C3489','#993556','#639922','#0C447C','#993C1D','#5F5E5A']

# KPIs
st.markdown('<div class="krow" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;">', unsafe_allow_html=True)

years_present = [y for y in st.session_state.filters['years'] if y != -1]
if len(years_present) >= 2:
    y1, y2 = sorted(years_present[:2])
    y1_idx = available_years.index(y1) if y1 in available_years else 0
    y2_idx = available_years.index(y2) if y2 in available_years else 1
    pct_change = ((aggregated['by_year'].get(y2_idx, 0) - aggregated['by_year'].get(y1_idx, 0)) / 
                  max(aggregated['by_year'].get(y1_idx, 1), 1) * 100)
    pct_html = f'<span class="up">▲ {abs(pct_change):.1f}%</span>' if pct_change >= 0 else f'<span class="dn">▼ {abs(pct_change):.1f}%</span>'
    cambio_texto = f"{pct_html} {y1}→{y2}"
else:
    cambio_texto = "Seleccione 2 años"

kpi_data = [
    ('kbl', 'Unidades totales', fmt_number(aggregated['total']), cambio_texto if aggregated['total'] > 0 else 'Sin datos'),
    ('ktl', 'Facturas', fmt_number(aggregated['total_records']), f"{len(years_present)} años"),
    ('kco', 'Categoría líder', list(aggregated['by_category'].keys())[0] if aggregated['by_category'] else '—', 
     f"{fmt_number(list(aggregated['by_category'].values())[0]) if aggregated['by_category'] else '0'} ud."),
    ('kam', 'Marca líder', list(aggregated['by_brand'].keys())[0] if aggregated['by_brand'] else '—',
     f"{fmt_number(list(aggregated['by_brand'].values())[0]) if aggregated['by_brand'] else '0'} ud."),
    ('kpu', 'Proveedor líder', list(aggregated['by_provider'].keys())[0][:20] if aggregated['by_provider'] else '—',
     f"{fmt_number(list(aggregated['by_provider'].values())[0]) if aggregated['by_provider'] else '0'} ud.")
]

for clase, label, valor, detalle in kpi_data:
    st.markdown(f'''
    <div class="kpi-card {clase}">
        <div class="klb">{label}</div>
        <div class="kv">{valor}</div>
        <div class="kd">{detalle}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Gráfico de tendencia mensual
st.markdown('<div class="sec">📈 Tendencia mensual</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Evolución mensual de unidades vendidas</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Aplica todos los filtros activos — identifica estacionalidad y picos de demanda</div>', unsafe_allow_html=True)
    
    fig_line = go.Figure()
    years_in_data = [y for y in available_years if y in st.session_state.filters['years'] or -1 in st.session_state.filters['years']]
    
    for i, year in enumerate(years_in_data):
        year_idx = available_years.index(year)
        fig_line.add_trace(go.Scatter(
            x=meses,
            y=aggregated['monthly_by_year'][year_idx],
            name=str(year),
            line=dict(color=colores[i % len(colores)], width=2),
            fill='tozeroy',
            fillcolor=f"{colores[i % len(colores)]}28",
            mode='lines+markers'
        ))
    
    fig_line.update_layout(
        height=215,
        margin=dict(l=40, r=20, t=20, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified'
    )
    fig_line.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
    fig_line.update_yaxes(gridcolor='rgba(0,0,0,0.05)', tickformat=',.0f')
    st.plotly_chart(fig_line, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Gráficos de barras año y mes
col_g2_1, col_g2_2 = st.columns(2)

with col_g2_1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Total de unidades por año</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Volumen acumulado según filtros activos</div>', unsafe_allow_html=True)
    
    years_list = [str(y) for y in available_years]
    values_list = [aggregated['by_year'].get(available_years.index(y), 0) for y in available_years]
    
    fig_year = go.Figure(data=[
        go.Bar(
            x=years_list,
            y=values_list,
            marker_color=colores[:len(years_list)],
            text=[fmt_k(v) for v in values_list],
            textposition='outside'
        )
    ])
    fig_year.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
    fig_year.update_yaxes(tickformat=',.0f')
    st.plotly_chart(fig_year, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_g2_2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="ct">Distribución por mes</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs">Suma total de unidades por mes (todos los años filtrados)</div>', unsafe_allow_html=True)
    
    max_m = max(aggregated['by_month']) if aggregated['by_month'] else 0
    colors_m = [colores[2] if v == max_m else colores[0] for v in aggregated['by_month']]
    
    fig_month = go.Figure(data=[
        go.Bar(x=meses, y=aggregated['by_month'], marker_color=colors_m, text=[fmt_k(v) for v in aggregated['by_month']], textposition='outside')
    ])
    fig_month.update_layout(height=180, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
    fig_month.update_yaxes(tickformat=',.0f')
    st.plotly_chart(fig_month, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Categorías (si hay datos de categoría)
if aggregated['by_category']:
    st.markdown('<div class="sec">🗂 Categorías</div>', unsafe_allow_html=True)
    
    col_cat1, col_cat2 = st.columns(2)
    
    with col_cat1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="ct">Ranking de categorías</div>', unsafe_allow_html=True)
        st.markdown('<div class="cs">Por volumen total según filtros</div>', unsafe_allow_html=True)
        
        top_cats = list(aggregated['by_category'].items())[:12]
        fig_cat = go.Figure(data=[
            go.Bar(
                x=[v for k, v in top_cats],
                y=[k[:20] + '…' if len(k) > 20 else k for k, v in top_cats],
                orientation='h',
                marker_color=colores[:len(top_cats)],
                text=[fmt_k(v) for k, v in top_cats],
                textposition='outside'
            )
        ])
        fig_cat.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        fig_cat.update_xaxes(tickformat=',.0f')
        fig_cat.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_cat2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="ct">Categorías apiladas por año</div>', unsafe_allow_html=True)
        st.markdown('<div class="cs">Participación y variación interanual</div>', unsafe_allow_html=True)
        
        top_cats_stack = list(aggregated['by_category'].items())[:10]
        fig_stack = go.Figure()
        for i, (cat, _) in enumerate(top_cats_stack):
            cat_values = []
            for year in available_years:
                year_idx = available_years.index(year)
                cat_values.append(aggregated['cat_by_year'][year_idx].get(cat, 0))
            fig_stack.add_trace(go.Bar(
                name=cat[:15] + '…' if len(cat) > 15 else cat,
                x=[str(y) for y in available_years],
                y=cat_values,
                marker_color=colores[i % len(colores)]
            ))
        
        fig_stack.update_layout(
            height=300,
            barmode='stack',
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            legend_font_size=9
        )
        fig_stack.update_yaxes(tickformat=',.0f')
        st.plotly_chart(fig_stack, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Tabla comparativa de productos
if aggregated['products_df'] is not None and not aggregated['products_df'].empty:
    st.markdown('<div class="sec">📋 Tabla comparativa de productos</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="ct">Comparativo por producto en unidades y variación %</div>', unsafe_allow_html=True)
        st.markdown('<div class="cs">Top 50 productos según filtros activos</div>', unsafe_allow_html=True)
        
        products_df = aggregated['products_df'].copy()
        
        # Formatear para mostrar
        display_df = products_df.head(20).copy()
        display_df['u2024'] = display_df['u2024'].apply(lambda x: f"{int(x):,}")
        display_df['u2025'] = display_df['u2025'].apply(lambda x: f"{int(x):,}")
        display_df['u2026'] = display_df['u2026'].apply(lambda x: f"{int(x):,}")
        display_df['diff_2425'] = display_df['diff_2425'].apply(lambda x: f"{int(x):,}")
        display_df['pct_2425'] = display_df['pct_2425'].apply(lambda x: pct_format(x))
        display_df['diff_2526'] = display_df['diff_2526'].apply(lambda x: f"{int(x):,}")
        display_df['pct_2526'] = display_df['pct_2526'].apply(lambda x: pct_format(x))
        
        st.dataframe(
            display_df,
            column_config={
                st.session_state.processor.mapping.get('producto', 'producto'): st.column_config.TextColumn('Producto', width='medium'),
                'u2024': st.column_config.TextColumn('2024', help='Unidades 2024'),
                'u2025': st.column_config.TextColumn('2025', help='Unidades 2025'),
                'u2026': st.column_config.TextColumn('2026', help='Unidades 2026'),
                'diff_2425': st.column_config.TextColumn('Dif 24→25'),
                'pct_2425': st.column_config.TextColumn('% 24→25'),
                'diff_2526': st.column_config.TextColumn('Dif 25→26'),
                'pct_2526': st.column_config.TextColumn('% 25→26'),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Dashboard de Ventas — Datos actualizables diariamente mediante carga de Excel")