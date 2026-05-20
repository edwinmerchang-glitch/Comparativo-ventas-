import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class DataProcessor:
    """Procesador de datos de ventas con carga desde Excel"""
    
    def __init__(self):
        self.df = None
        self.last_upload_time = None
        self.mapping = {
            'categorias': {},
            'marcas': {},
            'proveedores': {}
        }
    
    def load_excel(self, file) -> bool:
        """Carga datos desde archivo Excel"""
        try:
            # Cargar el archivo Excel
            self.df = pd.read_excel(file, engine='openpyxl')
            
            # Normalizar nombres de columnas (ajustar según tu Excel)
            # Mapeo de columnas esperadas a nombres reales en tu Excel
            column_mapping = {
                'fecha': ['fecha', 'date', 'fechaventa', 'fecha_venta'],
                'producto': ['producto', 'product', 'nombre_producto', 'articulo'],
                'categoria': ['categoria', 'category', 'categoría', 'cat'],
                'marca': ['marca', 'brand', 'marca_producto'],
                'proveedor': ['proveedor', 'provider', 'proveedor_nombre'],
                'unidades': ['unidades', 'units', 'cantidad', 'qty', 'volumen'],
                'año': ['año', 'year', 'ano'],
                'mes': ['mes', 'month']
            }
            
            # Encontrar las columnas reales
            for target, possible_names in column_mapping.items():
                for col in self.df.columns:
                    if col.lower() in possible_names or col.lower() == target:
                        self.mapping[target] = col
                        break
            
            # Validar columnas necesarias
            required = ['fecha', 'unidades']
            missing = [r for r in required if r not in self.mapping]
            if missing:
                raise ValueError(f"Faltan columnas requeridas: {missing}")
            
            # Procesar fechas si no hay año/mes explícito
            if 'año' not in self.mapping or 'mes' not in self.mapping:
                self.df['fecha_procesada'] = pd.to_datetime(self.df[self.mapping['fecha']])
                self.df['año'] = self.df['fecha_procesada'].dt.year
                self.df['mes'] = self.df['fecha_procesada'].dt.month - 1  # 0-index
                self.mapping['año'] = 'año'
                self.mapping['mes'] = 'mes'
            
            # Asegurar tipos de datos
            self.df[self.mapping['unidades']] = pd.to_numeric(self.df[self.mapping['unidades']], errors='coerce').fillna(0)
            
            # Crear índices para búsqueda rápida
            self._create_indexes()
            
            self.last_upload_time = datetime.now()
            return True
            
        except Exception as e:
            print(f"Error cargando Excel: {e}")
            return False
    
    def _create_indexes(self):
        """Crea índices para búsqueda rápida"""
        # Crear diccionarios de mapeo para filtros
        if 'categoria' in self.mapping and self.mapping['categoria'] in self.df.columns:
            self.categorias = sorted(self.df[self.mapping['categoria']].dropna().unique())
        else:
            self.categorias = []
            
        if 'marca' in self.mapping and self.mapping['marca'] in self.df.columns:
            self.marcas = sorted(self.df[self.mapping['marca']].dropna().unique())
        else:
            self.marcas = []
            
        if 'proveedor' in self.mapping and self.mapping['proveedor'] in self.df.columns:
            self.proveedores = sorted(self.df[self.mapping['proveedor']].dropna().unique())
        else:
            self.proveedores = []
    
    def get_available_years(self) -> List[int]:
        """Obtiene años disponibles en los datos"""
        if self.df is None:
            return [2024, 2025, 2026]
        return sorted(self.df[self.mapping['año']].unique())
    
    def filter_data(self, years: List[int], months: List[int], 
                   category: Optional[str], marca: Optional[str], 
                   provider: Optional[str]) -> pd.DataFrame:
        """Filtra los datos según criterios"""
        if self.df is None:
            return pd.DataFrame()
        
        df_filtered = self.df.copy()
        
        # Filtrar por año
        if years and -1 not in years:
            df_filtered = df_filtered[df_filtered[self.mapping['año']].isin(years)]
        
        # Filtrar por mes
        if months and -1 not in months:
            df_filtered = df_filtered[df_filtered[self.mapping['mes']].isin(months)]
        
        # Filtrar por categoría
        if category and 'categoria' in self.mapping:
            df_filtered = df_filtered[df_filtered[self.mapping['categoria']] == category]
        
        # Filtrar por marca
        if marca and 'marca' in self.mapping:
            df_filtered = df_filtered[df_filtered[self.mapping['marca']] == marca]
        
        # Filtrar por proveedor
        if provider and 'proveedor' in self.mapping:
            df_filtered = df_filtered[df_filtered[self.mapping['proveedor']] == provider]
        
        return df_filtered
    
    def aggregate_data(self, df: pd.DataFrame) -> Dict:
        """Agrega datos para los KPIs y gráficos"""
        if df.empty:
            return self._get_empty_aggregation()
        
        # Unidades por año y mes
        df['year_idx'] = df[self.mapping['año']].map({2024: 0, 2025: 1, 2026: 2}).fillna(0).astype(int)
        
        # Agregaciones principales
        by_year = df.groupby('year_idx')[self.mapping['unidades']].sum().to_dict()
        for i in range(3):
            if i not in by_year:
                by_year[i] = 0
        
        # Por mes (todos los años)
        by_month = df.groupby(self.mapping['mes'])[self.mapping['unidades']].sum().reindex(range(12), fill_value=0).tolist()
        
        # Serie temporal por año
        monthly_by_year = {}
        for year_idx in range(3):
            year_data = df[df['year_idx'] == year_idx]
            monthly = year_data.groupby(self.mapping['mes'])[self.mapping['unidades']].sum().reindex(range(12), fill_value=0).tolist()
            monthly_by_year[year_idx] = monthly
        
        # Por categoría
        by_category = {}
        if 'categoria' in self.mapping:
            cat_data = df.groupby(self.mapping['categoria'])[self.mapping['unidades']].sum()
            by_category = cat_data.sort_values(ascending=False).to_dict()
        
        # Por marca
        by_brand = {}
        if 'marca' in self.mapping:
            brand_data = df.groupby(self.mapping['marca'])[self.mapping['unidades']].sum()
            by_brand = brand_data.sort_values(ascending=False).to_dict()
        
        # Por proveedor
        by_provider = {}
        if 'proveedor' in self.mapping:
            provider_data = df.groupby(self.mapping['proveedor'])[self.mapping['unidades']].sum()
            by_provider = provider_data.sort_values(ascending=False).to_dict()
        
        # Categorías por año para stacked chart
        cat_by_year = {}
        if 'categoria' in self.mapping:
            for year_idx in range(3):
                year_df = df[df['year_idx'] == year_idx]
                if not year_df.empty:
                    cat_by_year[year_idx] = year_df.groupby(self.mapping['categoria'])[self.mapping['unidades']].sum().to_dict()
                else:
                    cat_by_year[year_idx] = {}
        
        # Productos top para tabla
        products_df = None
        if 'producto' in self.mapping:
            # Agregar por producto y año
            product_year = df.groupby([self.mapping['producto'], 'year_idx'])[self.mapping['unidades']].sum().unstack(fill_value=0)
            product_year.columns = ['u2024', 'u2025', 'u2026']
            product_year['total'] = product_year.sum(axis=1)
            product_year = product_year.sort_values('total', ascending=False).head(50)
            products_df = product_year.reset_index()
        
        total = df[self.mapping['unidades']].sum()
        
        return {
            'total': total,
            'by_year': by_year,
            'by_month': by_month,
            'monthly_by_year': monthly_by_year,
            'by_category': by_category,
            'by_brand': by_brand,
            'by_provider': by_provider,
            'cat_by_year': cat_by_year,
            'products_df': products_df,
            'total_records': len(df)
        }
    
    def _get_empty_aggregation(self) -> Dict:
        """Retorna estructura vacía cuando no hay datos"""
        return {
            'total': 0,
            'by_year': {0: 0, 1: 0, 2: 0},
            'by_month': [0] * 12,
            'monthly_by_year': {0: [0]*12, 1: [0]*12, 2: [0]*12},
            'by_category': {},
            'by_brand': {},
            'by_provider': {},
            'cat_by_year': {0: {}, 1: {}, 2: {}},
            'products_df': None,
            'total_records': 0
        }
    
    def get_product_table_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara datos para la tabla comparativa de productos"""
        if df.empty or 'producto' not in self.mapping:
            return pd.DataFrame()
        
        # Agregar por producto y año
        product_data = df.groupby([self.mapping['producto'], self.mapping['año']])[self.mapping['unidades']].sum().unstack(fill_value=0)
        
        # Asegurar que todos los años existen
        for year in [2024, 2025, 2026]:
            if year not in product_data.columns:
                product_data[year] = 0
        
        product_data = product_data[[2024, 2025, 2026]]
        product_data.columns = ['u2024', 'u2025', 'u2026']
        
        # Calcular diferencias y porcentajes
        product_data['diff_2425'] = product_data['u2025'] - product_data['u2024']
        product_data['pct_2425'] = np.where(
            product_data['u2024'] > 0,
            (product_data['diff_2425'] / product_data['u2024'] * 100),
            np.where(product_data['u2025'] > 0, 99999, 0)
        )
        
        product_data['diff_2526'] = product_data['u2026'] - product_data['u2025']
        product_data['pct_2526'] = np.where(
            product_data['u2025'] > 0,
            (product_data['diff_2526'] / product_data['u2025'] * 100),
            np.where(product_data['u2026'] > 0, 99999, 0)
        )
        
        product_data['total'] = product_data[['u2024', 'u2025', 'u2026']].sum(axis=1)
        
        # Ordenar por total
        product_data = product_data.sort_values('total', ascending=False)
        
        return product_data.reset_index()