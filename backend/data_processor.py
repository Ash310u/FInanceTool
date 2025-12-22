"""
Data Processor Module
Handles Excel file loading, data normalization, and validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Loads and processes financial transaction data from Excel files.
    Ensures data quality and normalizes numeric columns.
    """
    
    # Expected column names in Excel file
    EXPECTED_COLUMNS = [
        'Date',
        'Entity Type',
        'Entity Sub Type',
        'Entity Name',
        'Vch Type',
        'Particulars',
        'Cash Dr (R)',
        'Cash Cr (P)',
        'Bank Dr (R)',
        'Bank Cr (P)'
    ]
    
    # Columns that should be numeric
    NUMERIC_COLUMNS = [
        'Cash Dr (R)',
        'Cash Cr (P)',
        'Bank Dr (R)',
        'Bank Cr (P)'
    ]
    
    def __init__(self):
        self.df: pd.DataFrame = None
        self.file_path: str = None
        
    def load_excel_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load Excel file and perform initial validation.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary with status and metadata
        """
        try:
            logger.info(f"Loading Excel file: {file_path}")
            
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Validate columns
            if len(df.columns) < len(self.EXPECTED_COLUMNS):
                return {
                    'success': False,
                    'error': f'Expected {len(self.EXPECTED_COLUMNS)} columns, found {len(df.columns)}'
                }
            
            # Rename columns to expected names (in case of variations)
            df.columns = self.EXPECTED_COLUMNS[:len(df.columns)]
            
            # Keep only expected columns
            df = df[self.EXPECTED_COLUMNS]
            
            # Normalize data
            df = self._normalize_data(df)
            
            self.df = df
            self.file_path = file_path
            
            logger.info(f"Successfully loaded {len(df)} rows")
            
            return {
                'success': True,
                'rows': len(df),
                'columns': list(df.columns),
                'date_range': {
                    'start': str(df['Date'].min()),
                    'end': str(df['Date'].max())
                },
                'entities': {
                    'types': df['Entity Type'].nunique(),
                    'sub_types': df['Entity Sub Type'].nunique(),
                    'names': df['Entity Name'].nunique()
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data types and handle missing values.
        
        Args:
            df: Raw dataframe
            
        Returns:
            Normalized dataframe
        """
        # Parse dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert date to string format for grouping (YYYY-MM-DD)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Handle missing dates
        df['Date'].fillna('Unknown', inplace=True)
        
        # Normalize string columns (strip whitespace, handle nulls)
        string_columns = ['Entity Type', 'Entity Sub Type', 'Entity Name', 'Vch Type', 'Particulars']
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            df[col].replace(['nan', 'None', ''], 'Unknown', inplace=True)
        
        # Normalize numeric columns (empty → 0, non-numeric → 0)
        for col in self.NUMERIC_COLUMNS:
            # Convert to numeric, coerce errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Fill NaN with 0
            df[col].fillna(0.0, inplace=True)
            # Ensure float type
            df[col] = df[col].astype(float)
        
        # Remove rows where all numeric columns are 0 (optional - can be configured)
        # df = df[df[self.NUMERIC_COLUMNS].sum(axis=1) != 0]
        
        return df
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Get unique values for each filter dimension.
        
        Returns:
            Dictionary with filter options
        """
        if self.df is None:
            return {}
        
        return {
            'dates': sorted(self.df['Date'].unique().tolist()),
            'entity_types': sorted(self.df['Entity Type'].unique().tolist()),
            'entity_sub_types': sorted(self.df['Entity Sub Type'].unique().tolist()),
            'entity_names': sorted(self.df['Entity Name'].unique().tolist())
        }
    
    def get_filtered_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to the dataset.
        
        Args:
            filters: Dictionary with filter criteria
                {
                    'date': str or None,
                    'entity_type': str or None,
                    'entity_sub_type': str or None,
                    'entity_name': str or None
                }
        
        Returns:
            Filtered dataframe
        """
        if self.df is None:
            return pd.DataFrame()
        
        filtered_df = self.df.copy()
        
        # Apply each filter if provided
        if filters.get('date'):
            filtered_df = filtered_df[filtered_df['Date'] == filters['date']]
        
        if filters.get('entity_type'):
            filtered_df = filtered_df[filtered_df['Entity Type'] == filters['entity_type']]
        
        if filters.get('entity_sub_type'):
            filtered_df = filtered_df[filtered_df['Entity Sub Type'] == filters['entity_sub_type']]
        
        if filters.get('entity_name'):
            filtered_df = filtered_df[filtered_df['Entity Name'] == filters['entity_name']]
        
        return filtered_df
    
    def calculate_totals(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate aggregate totals for numeric columns.
        
        Args:
            df: Dataframe to aggregate
            
        Returns:
            Dictionary with totals
        """
        if df is None or len(df) == 0:
            return {col: 0.0 for col in self.NUMERIC_COLUMNS}
        
        totals = {}
        for col in self.NUMERIC_COLUMNS:
            totals[col] = float(df[col].sum())
        
        return totals
    
    def export_to_excel(self, df: pd.DataFrame, output_path: str, include_totals: bool = True) -> Dict[str, Any]:
        """
        Export dataframe to Excel file.
        
        Args:
            df: Dataframe to export
            output_path: Output file path
            include_totals: Whether to include totals row
            
        Returns:
            Dictionary with status
        """
        try:
            if include_totals:
                # Create totals row
                totals_row = {col: '' for col in df.columns}
                totals_row['Particulars'] = 'TOTAL'
                for col in self.NUMERIC_COLUMNS:
                    totals_row[col] = df[col].sum()
                
                # Append totals
                df_with_totals = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)
            else:
                df_with_totals = df
            
            # Export to Excel
            df_with_totals.to_excel(output_path, index=False, engine='xlsxwriter')
            
            logger.info(f"Exported {len(df)} rows to {output_path}")
            
            return {
                'success': True,
                'rows': len(df),
                'path': output_path
            }
            
        except Exception as e:
            logger.error(f"Error exporting file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

