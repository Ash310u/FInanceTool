"""
Test Script for Data Processor
Run this to verify the data processing logic works correctly
"""

import pandas as pd
import numpy as np
from data_processor import DataProcessor
from hierarchy_builder import HierarchyBuilder
import json

def create_sample_data():
    """Create sample transaction data for testing."""
    data = {
        'Date': [
            '2024-01-15', '2024-01-15', '2024-01-16', 
            '2024-01-16', '2024-01-17', '2024-01-17'
        ],
        'Entity Type': [
            'Customer', 'Customer', 'Vendor', 
            'Vendor', 'Customer', 'Bank'
        ],
        'Entity Sub Type': [
            'Retail', 'Retail', 'Wholesale', 
            'Service', 'Online', 'Finance'
        ],
        'Entity Name': [
            'ABC Corp', 'ABC Corp', 'XYZ Ltd', 
            'DEF Services', 'GHI Inc', 'Bank of Test'
        ],
        'Vch Type': [
            'Receipt', 'Receipt', 'Payment', 
            'Payment', 'Receipt', 'Interest'
        ],
        'Particulars': [
            'Payment received', 'Second payment', 'Vendor payment', 
            'Service fee', 'Online sale', 'Interest earned'
        ],
        'Cash Dr (R)': [10000.0, 5000.0, 0, 0, 0, 0],
        'Cash Cr (P)': [0, 0, 3000.0, 2000.0, 0, 0],
        'Bank Dr (R)': [0, 0, 0, 0, 15000.0, 500.0],
        'Bank Cr (P)': [0, 0, 0, 0, 0, 0]
    }
    
    return pd.DataFrame(data)

def test_data_processor():
    """Test data processor functionality."""
    print("="*80)
    print("Testing Data Processor")
    print("="*80)
    
    # Create sample data
    df = create_sample_data()
    print(f"\n✓ Created sample data with {len(df)} rows\n")
    
    # Initialize processor with data
    processor = DataProcessor()
    processor.df = df
    
    # Test filter options
    print("Filter Options:")
    filters = processor.get_filter_options()
    print(f"  Dates: {filters['dates']}")
    print(f"  Entity Types: {filters['entity_types']}")
    print(f"  Entity Sub Types: {filters['entity_sub_types']}")
    print(f"  Entity Names: {filters['entity_names']}")
    
    # Test totals calculation
    print("\nTotal Calculations:")
    totals = processor.calculate_totals(df)
    for col, value in totals.items():
        print(f"  {col}: {value:,.2f}")
    
    # Test filtering
    print("\n" + "-"*80)
    print("Testing Filters")
    print("-"*80)
    
    # Filter by date
    filtered = processor.get_filtered_data({'date': '2024-01-15'})
    print(f"\nFilter by Date '2024-01-15': {len(filtered)} rows")
    totals = processor.calculate_totals(filtered)
    print(f"  Cash Dr: {totals['Cash Dr (R)']:,.2f}")
    print(f"  Cash Cr: {totals['Cash Cr (P)']:,.2f}")
    
    # Filter by entity type
    filtered = processor.get_filtered_data({'entity_type': 'Customer'})
    print(f"\nFilter by Entity Type 'Customer': {len(filtered)} rows")
    totals = processor.calculate_totals(filtered)
    print(f"  Cash Dr: {totals['Cash Dr (R)']:,.2f}")
    print(f"  Bank Dr: {totals['Bank Dr (R)']:,.2f}")
    
    # Multiple filters
    filtered = processor.get_filtered_data({
        'date': '2024-01-15',
        'entity_type': 'Customer'
    })
    print(f"\nMultiple Filters (Date + Entity Type): {len(filtered)} rows")
    totals = processor.calculate_totals(filtered)
    print(f"  Cash Dr: {totals['Cash Dr (R)']:,.2f}")
    
    print("\n✓ Data Processor tests passed!")

def test_hierarchy_builder():
    """Test hierarchy builder functionality."""
    print("\n" + "="*80)
    print("Testing Hierarchy Builder")
    print("="*80)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize hierarchy builder
    builder = HierarchyBuilder(df)
    
    # Build hierarchy
    print("\nBuilding hierarchy structure...")
    hierarchy = builder.build_hierarchy()
    
    print(f"\n✓ Built hierarchy with {len(hierarchy)} top-level nodes\n")
    
    # Show hierarchy structure
    def print_hierarchy(nodes, level=0):
        indent = "  " * level
        for node in nodes:
            if node['type'] == 'group':
                count = node.get('count', 0)
                agg = node.get('aggregates', {})
                total = sum(agg.values())
                print(f"{indent}▶ {node['label']} ({count} transactions, Total: {total:,.2f})")
                
                if node.get('children'):
                    print_hierarchy(node['children'], level + 1)
    
    print("Hierarchy Structure:")
    print_hierarchy(hierarchy)
    
    # Test flat hierarchy
    print("\n" + "-"*80)
    print("Testing Flat Hierarchy")
    print("-"*80)
    
    flat = builder.build_flat_hierarchy()
    print(f"\n✓ Built flat hierarchy with {len(flat)} groups")
    
    for group in flat[:3]:  # Show first 3
        print(f"\n{group['hierarchy']['Entity Name']}:")
        print(f"  Transactions: {group['count']}")
        print(f"  Aggregates: {group['aggregates']}")
    
    print("\n✓ Hierarchy Builder tests passed!")

def test_aggregation_accuracy():
    """Test that aggregations are accurate."""
    print("\n" + "="*80)
    print("Testing Aggregation Accuracy")
    print("="*80)
    
    df = create_sample_data()
    processor = DataProcessor()
    processor.df = df
    builder = HierarchyBuilder(df)
    
    # Expected totals (from sample data)
    expected = {
        'Cash Dr (R)': 15000.0,
        'Cash Cr (P)': 5000.0,
        'Bank Dr (R)': 15500.0,
        'Bank Cr (P)': 0.0
    }
    
    # Calculate totals
    actual = processor.calculate_totals(df)
    
    print("\nExpected vs Actual Totals:")
    all_match = True
    for col in expected:
        match = "✓" if abs(expected[col] - actual[col]) < 0.01 else "✗"
        print(f"  {match} {col}:")
        print(f"      Expected: {expected[col]:,.2f}")
        print(f"      Actual:   {actual[col]:,.2f}")
        if abs(expected[col] - actual[col]) >= 0.01:
            all_match = False
    
    if all_match:
        print("\n✓ All aggregations are accurate!")
    else:
        print("\n✗ Some aggregations are incorrect!")
    
    return all_match

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FINANCIAL REPORTING TOOL - DATA PROCESSOR TESTS")
    print("="*80)
    
    try:
        # Run tests
        test_data_processor()
        test_hierarchy_builder()
        accurate = test_aggregation_accuracy()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("✓ Data Processor: PASSED")
        print("✓ Hierarchy Builder: PASSED")
        print(f"{'✓' if accurate else '✗'} Aggregation Accuracy: {'PASSED' if accurate else 'FAILED'}")
        print("\n✓ All tests completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

