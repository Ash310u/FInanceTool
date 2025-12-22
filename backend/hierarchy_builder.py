"""
Hierarchy Builder Module
Constructs hierarchical data structure with aggregation at each level.

Hierarchy Levels:
  Level 0: Date
  Level 1: Entity Type
  Level 2: Entity Sub Type
  Level 3: Entity Name
  Level 4: Individual Transactions
"""

import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class HierarchyBuilder:
    """
    Builds hierarchical tree structure from flat transaction data.
    Supports drill-down and aggregation at each level.
    """
    
    # Define hierarchy levels
    HIERARCHY_LEVELS = [
        'Date',
        'Entity Type',
        'Entity Sub Type',
        'Entity Name'
    ]
    
    NUMERIC_COLUMNS = [
        'Cash Dr (R)',
        'Cash Cr (P)',
        'Bank Dr (R)',
        'Bank Cr (P)'
    ]
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize hierarchy builder with dataframe.
        
        Args:
            df: Normalized transaction dataframe
        """
        self.df = df
    
    def build_hierarchy(self, filters: Dict[str, Any] = None, max_transactions: int = 10000) -> List[Dict[str, Any]]:
        """
        Build hierarchical structure with aggregation.
        
        Args:
            filters: Optional filters to apply
            max_transactions: Maximum number of transaction rows to return
            
        Returns:
            List of hierarchical nodes
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # Apply filters if provided
        filtered_df = self.df.copy()
        if filters:
            for key, value in filters.items():
                if value and key in self.HIERARCHY_LEVELS:
                    filtered_df = filtered_df[filtered_df[key] == value]
        
        # Build hierarchy tree
        hierarchy = self._build_level(filtered_df, level=0, parent_path='', max_transactions=max_transactions)
        
        return hierarchy
    
    def _build_level(self, df: pd.DataFrame, level: int, parent_path: str, max_transactions: int) -> List[Dict[str, Any]]:
        """
        Recursively build hierarchy at specified level.
        
        Args:
            df: Dataframe for this level
            level: Current hierarchy level (0-3)
            parent_path: Path from root to current node
            max_transactions: Maximum transactions to include
            
        Returns:
            List of nodes at this level
        """
        nodes = []
        
        # Base case: if we've reached transaction level
        if level >= len(self.HIERARCHY_LEVELS):
            # Return individual transaction rows (limited)
            transaction_count = 0
            for idx, row in df.iterrows():
                if transaction_count >= max_transactions:
                    # Add indicator that there are more transactions
                    nodes.append({
                        'id': f"{parent_path}/more",
                        'type': 'info',
                        'level': level,
                        'label': f'... and {len(df) - max_transactions} more transactions',
                        'isLeaf': True
                    })
                    break
                
                node = self._create_transaction_node(row, level, parent_path, idx)
                nodes.append(node)
                transaction_count += 1
            
            return nodes
        
        # Get current level column
        level_column = self.HIERARCHY_LEVELS[level]
        
        # Group by current level
        grouped = df.groupby(level_column, dropna=False)
        
        for group_name, group_df in grouped:
            # Create aggregated node for this group
            node_id = f"{parent_path}/{level}/{group_name}"
            
            # Calculate aggregates
            aggregates = self._calculate_aggregates(group_df)
            
            # Build child nodes (next level)
            children = self._build_level(group_df, level + 1, node_id, max_transactions)
            
            # Create node
            node = {
                'id': node_id,
                'type': 'group',
                'level': level,
                'label': str(group_name),
                'column': level_column,
                'value': str(group_name),
                'count': len(group_df),
                'aggregates': aggregates,
                'hasChildren': len(children) > 0,
                'children': children,
                'isExpanded': False,  # Initially collapsed
                'isLeaf': False
            }
            
            nodes.append(node)
        
        # Sort nodes by label
        nodes.sort(key=lambda x: x.get('label', ''))
        
        return nodes
    
    def _create_transaction_node(self, row: pd.Series, level: int, parent_path: str, idx: Any) -> Dict[str, Any]:
        """
        Create a leaf node representing a single transaction.
        
        Args:
            row: Transaction data row
            level: Hierarchy level
            parent_path: Parent node path
            idx: Row index
            
        Returns:
            Transaction node dictionary
        """
        return {
            'id': f"{parent_path}/tx/{idx}",
            'type': 'transaction',
            'level': level,
            'isLeaf': True,
            'data': {
                'Date': str(row['Date']),
                'Entity Type': str(row['Entity Type']),
                'Entity Sub Type': str(row['Entity Sub Type']),
                'Entity Name': str(row['Entity Name']),
                'Vch Type': str(row['Vch Type']),
                'Particulars': str(row['Particulars']),
                'Cash Dr (R)': float(row['Cash Dr (R)']),
                'Cash Cr (P)': float(row['Cash Cr (P)']),
                'Bank Dr (R)': float(row['Bank Dr (R)']),
                'Bank Cr (P)': float(row['Bank Cr (P)'])
            }
        }
    
    def _calculate_aggregates(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate aggregate sums for numeric columns.
        
        Args:
            df: Dataframe to aggregate
            
        Returns:
            Dictionary of aggregated values
        """
        aggregates = {}
        for col in self.NUMERIC_COLUMNS:
            aggregates[col] = float(df[col].sum())
        
        return aggregates
    
    def build_flat_hierarchy(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Build a flattened hierarchy for grid display.
        Each row contains full hierarchy path and aggregates.
        
        Args:
            filters: Optional filters
            
        Returns:
            Flattened list of rows for grid
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # Apply filters
        filtered_df = self.df.copy()
        if filters:
            for key, value in filters.items():
                if value and key in self.HIERARCHY_LEVELS:
                    filtered_df = filtered_df[filtered_df[key] == value]
        
        rows = []
        
        # Group by all hierarchy levels
        grouped = filtered_df.groupby(self.HIERARCHY_LEVELS, dropna=False)
        
        for group_keys, group_df in grouped:
            # Create hierarchical row for group
            row = {
                'id': '/'.join([str(k) for k in group_keys]),
                'type': 'group',
                'level': 3,  # Entity Name level
                'hierarchy': {
                    'Date': str(group_keys[0]),
                    'Entity Type': str(group_keys[1]),
                    'Entity Sub Type': str(group_keys[2]),
                    'Entity Name': str(group_keys[3])
                },
                'count': len(group_df),
                'aggregates': self._calculate_aggregates(group_df),
                'transactions': []
            }
            
            # Add individual transactions
            for idx, tx_row in group_df.iterrows():
                transaction = {
                    'Date': str(tx_row['Date']),
                    'Entity Type': str(tx_row['Entity Type']),
                    'Entity Sub Type': str(tx_row['Entity Sub Type']),
                    'Entity Name': str(tx_row['Entity Name']),
                    'Vch Type': str(tx_row['Vch Type']),
                    'Particulars': str(tx_row['Particulars']),
                    'Cash Dr (R)': float(tx_row['Cash Dr (R)']),
                    'Cash Cr (P)': float(tx_row['Cash Cr (P)']),
                    'Bank Dr (R)': float(tx_row['Bank Dr (R)']),
                    'Bank Cr (P)': float(tx_row['Bank Cr (P)'])
                }
                row['transactions'].append(transaction)
            
            rows.append(row)
        
        return rows

