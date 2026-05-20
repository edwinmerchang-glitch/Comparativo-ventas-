import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class DataProcessor:
    """Procesador de datos de ventas con carga desde Excel"""
    
    def __init__(self):
        self.df = None
        self.last_upload_time = None
        self.productos = []
        self.marcas = []
        self.proveedores = []
        self.mundos = []
        self.eventos = []
        self.materiales = []
        
    def load_excel(self, file) -> bool:
        """Carga datos desde archivo Excel con la estructura específica"""
        try:
            # Cargar el archivo Excel
            self.df = pd.read_excel(file, engine='openpyxl')
            
            # Verificar columnas requeridas
            required_columns = ['FECHA', 'CANTIDAD']
            missing = [col for col in required_columns if col not in self.df.columns]
            if missing:
                print(f"Faltan columnas requeridas: {missing}")
                return False
            
            # Procesar fechas
            self.df['FECHA_PROCESADA'] = pd.to_datetime(self.df['FECHA'], errors='coerce')
            
            # Eliminar filas con fechas inválidas
            self.df = self.df.dropna(subset=['FECHA_PROCESADA'])
            
            # Extraer año y mes de la fecha
            self.df['AÑO'] = self.df['FECHA_PROCESADA'].dt.year
            self.df['MES'] = self.df['FECHA_PROCESADA'].dt.month - 1  # 0-11 para enero=0
            
            # Asegurar que CANTIDAD sea numérico
            self.df['CANTIDAD'] = pd.to_numeric(self.df['CANTIDAD'], errors='coerce').fillna(0)
            
            # Manejar valores nulos en columnas categóricas
            categorical_cols = ['PRODUCTO', 'PROVEEDOR', 'MARCA', 'MUNDO', 'EVENTO', 'MATERIAL']
            for col in categorical_cols:
                if col in self.df.columns:
                    self.df[col] = self.df[col].fillna('SIN ASIGNAR')
            
            # Crear listas únicas para filtros
            if 'PRODUCTO' in self.df.columns:
                self.productos = sorted(self.df['PRODUCTO'].dropna().unique())
                
            if 'MARCA' in self.df.columns:
                self.marcas = sorted(self.df['MARCA'].dropna().unique())
                
            if 'PROVEEDOR' in self.df.columns:
                self.proveedores = sorted(self.df['PROVEEDOR'].dropna().unique())
            
            if 'MUNDO' in self.df.columns:
                self.mundos = sorted(self.df['MUNDO'].dropna().unique())
            
            if 'EVENTO' in self.df.columns:
                self.eventos = sorted(self.df['EVENTO'].dropna().unique())
            
            if 'MATERIAL' in self.df.columns:
                self.materiales = sorted(self.df['MATERIAL'].dropna().unique())
            
            self.last_upload_time = datetime.now()
            return True
            
        except Exception as e:
            print(f"Error cargando Excel: {e}")
            return False
    
    def get_available_years(self) -> List[int]:
        """Obtiene años disponibles en los datos"""
        if self.df is None or self.df.empty:
            return [2024, 2025, 2026]
        years = sorted(self.df['AÑO'].dropna().unique())
        return [int(y) for y in years if not pd.isna(y)]
    
    def filter_data(self, years: List[int], months: List[int], 
                   producto: Optional[str], marca: Optional[str], 
                   proveedor: Optional[str], mundo: Optional[str] = None,
                   evento: Optional[str] = None) -> pd.DataFrame:
        """Filtra los datos según criterios"""
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        
        df_filtered = self.df.copy()
        
        # Filtrar por año
        if years and -1 not in years:
            df_filtered = df_filtered[df_filtered['AÑO'].isin(years)]
        
        # Filtrar por mes
        if months and -1 not in months:
            df_filtered = df_filtered[df_filtered['MES'].isin(months)]
        
        # Filtrar por producto
        if producto and producto != "Todos" and producto != "Todas":
            df_filtered = df_filtered[df_filtered['PRODUCTO'] == producto]
        
        # Filtrar por marca
        if marca and marca != "Todos" and marca != "Todas":
            df_filtered = df_filtered[df_filtered['MARCA'] == marca]
        
        # Filtrar por proveedor
        if proveedor and proveedor != "Todos" and proveedor != "Todas":
            df_filtered = df_filtered[df_filtered['PROVEEDOR'] == proveedor]
        
        # Filtrar por mundo
        if mundo and mundo != "Todos" and mundo != "Todas":
            df_filtered = df_filtered[df_filtered['MUNDO'] == mundo]
        
        # Filtrar por evento
        if evento and evento != "Todos" and evento != "Todas":
            df_filtered = df_filtered[df_filtered['EVENTO'] == evento]
        
        return df_filtered
    
    def aggregate_data(self, df: pd.DataFrame) -> Dict:
        """Agrega datos para los KPIs y gráficos"""
        if df.empty:
            return self._get_empty_aggregation()
        
        # Obtener años disponibles en los datos filtrados
        years_available = sorted(df['AÑO'].unique())
        
        # Unidades por año
        by_year = {}
        for year in years_available:
            by_year[year] = df[df['AÑO'] == year]['CANTIDAD'].sum()
        
        # Por mes (todos los años)
        by_month = df.groupby('MES')['CANTIDAD'].sum().reindex(range(12), fill_value=0).tolist()
        
        # Serie temporal por año
        monthly_by_year = {}
        for year in years_available:
            year_data = df[df['AÑO'] == year]
            monthly = year_data.groupby('MES')['CANTIDAD'].sum().reindex(range(12), fill_value=0).tolist()
            monthly_by_year[year] = monthly
        
        # Por producto (para ranking)
        by_product = df.groupby('PRODUCTO')['CANTIDAD'].sum().sort_values(ascending=False).to_dict()
        
        # Por marca
        by_brand = df.groupby('MARCA')['CANTIDAD'].sum().sort_values(ascending=False).to_dict()
        
        # Por proveedor
        by_provider = df.groupby('PROVEEDOR')['CANTIDAD'].sum().sort_values(ascending=False).to_dict()
        
        # Por mundo (si existe)
        by_mundo = {}
        if 'MUNDO' in df.columns:
            by_mundo = df.groupby('MUNDO')['CANTIDAD'].sum().sort_values(ascending=False).to_dict()
        
        # Por evento (si existe)
        by_evento = {}
        if 'EVENTO' in df.columns:
            by_evento = df.groupby('EVENTO')['CANTIDAD'].sum().sort_values(ascending=False).to_dict()
        
        # Productos por año para tabla comparativa
        products_df = None
        if 'PRODUCTO' in df.columns:
            # Agregar por producto y año
            product_year = df.groupby(['PRODUCTO', 'AÑO'])['CANTIDAD'].sum().unstack(fill_value=0)
            
            # Asegurar columnas para 2024, 2025, 2026
            for year in [2024, 2025, 2026]:
                if year not in product_year.columns:
                    product_year[year] = 0
            
            product_year = product_year[[2024, 2025, 2026]]
            product_year.columns = ['u2024', 'u2025', 'u2026']
            product_year['total'] = product_year.sum(axis=1)
            product_year = product_year.sort_values('total', ascending=False).head(50)
            products_df = product_year.reset_index()
        
        total = df['CANTIDAD'].sum()
        
        # Datos por año para marcas (stacked)
        brand_by_year = {}
        for year in years_available:
            year_df = df[df['AÑO'] == year]
            brand_by_year[year] = year_df.groupby('MARCA')['CANTIDAD'].sum().nlargest(10).to_dict()
        
        return {
            'total': total,
            'by_year': by_year,
            'by_month': by_month,
            'monthly_by_year': monthly_by_year,
            'by_product': by_product,
            'by_brand': by_brand,
            'by_provider': by_provider,
            'by_mundo': by_mundo,
            'by_evento': by_evento,
            'brand_by_year': brand_by_year,
            'products_df': products_df,
            'total_records': len(df),
            'years_available': years_available
        }
    
    def _get_empty_aggregation(self) -> Dict:
        """Retorna estructura vacía cuando no hay datos"""
        return {
            'total': 0,
            'by_year': {},
            'by_month': [0] * 12,
            'monthly_by_year': {},
            'by_product': {},
            'by_brand': {},
            'by_provider': {},
            'by_mundo': {},
            'by_evento': {},
            'brand_by_year': {},
            'products_df': None,
            'total_records': 0,
            'years_available': []
        }