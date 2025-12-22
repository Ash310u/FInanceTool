"""
Sample Excel File Generator
Creates a test Excel file with sample financial data
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os

def generate_sample_data(num_rows=100):
    """
    Generate sample financial transaction data.
    
    Args:
        num_rows: Number of transaction rows to generate
        
    Returns:
        DataFrame with sample data
    """
    
    # Sample data options
    entity_types = ['Customer', 'Vendor', 'Bank', 'Employee', 'Partner']
    
    entity_sub_types = {
        'Customer': ['Retail', 'Wholesale', 'Online', 'Corporate'],
        'Vendor': ['Service', 'Goods', 'Wholesale', 'Utility'],
        'Bank': ['Savings', 'Current', 'Loan', 'Finance'],
        'Employee': ['Salary', 'Reimbursement', 'Bonus', 'Advance'],
        'Partner': ['Investment', 'Distribution', 'Commission', 'Profit Share']
    }
    
    entity_names = {
        'Customer': ['ABC Corp', 'XYZ Ltd', 'Global Inc', 'Tech Solutions', 'Retail Pro'],
        'Vendor': ['Office Supplies Co', 'Utility Corp', 'Service Provider', 'Material Mart'],
        'Bank': ['National Bank', 'State Bank', 'Commercial Bank', 'Finance Bank'],
        'Employee': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams'],
        'Partner': ['Partner A', 'Partner B', 'Partner C', 'Investor D']
    }
    
    vch_types = ['Receipt', 'Payment', 'Journal', 'Contra', 'Sales', 'Purchase']
    
    particulars = [
        'Payment received', 'Payment made', 'Service charge', 'Product sale',
        'Material purchase', 'Salary payment', 'Commission paid', 'Interest earned',
        'Interest paid', 'Bank charges', 'Rent received', 'Rent paid',
        'Invoice settlement', 'Advance received', 'Advance payment'
    ]
    
    # Generate dates for last 30 days
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(days=random.randint(0, 30)) for _ in range(num_rows)]
    
    # Generate transactions
    transactions = []
    
    for i in range(num_rows):
        # Select entity type
        entity_type = random.choice(entity_types)
        
        # Select corresponding sub type and name
        entity_sub_type = random.choice(entity_sub_types[entity_type])
        entity_name = random.choice(entity_names[entity_type])
        
        # Select voucher type and particulars
        vch_type = random.choice(vch_types)
        particular = random.choice(particulars)
        
        # Generate amounts (only one of the four will be non-zero)
        amount = round(random.uniform(100, 50000), 2)
        amount_type = random.choice(['cash_dr', 'cash_cr', 'bank_dr', 'bank_cr'])
        
        transaction = {
            'Date': dates[i].strftime('%Y-%m-%d'),
            'Entity Type': entity_type,
            'Entity Sub Type': entity_sub_type,
            'Entity Name': entity_name,
            'Vch Type': vch_type,
            'Particulars': particular,
            'Cash Dr (R)': amount if amount_type == 'cash_dr' else 0,
            'Cash Cr (P)': amount if amount_type == 'cash_cr' else 0,
            'Bank Dr (R)': amount if amount_type == 'bank_dr' else 0,
            'Bank Cr (P)': amount if amount_type == 'bank_cr' else 0
        }
        
        transactions.append(transaction)
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    # Sort by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    return df

def create_excel_file(output_path='sample_data.xlsx', num_rows=100):
    """
    Create sample Excel file.
    
    Args:
        output_path: Path for output file
        num_rows: Number of rows to generate
    """
    print(f"Generating {num_rows} sample transactions...")
    
    # Generate data
    df = generate_sample_data(num_rows)
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # Write data
        df.to_excel(writer, index=False, sheet_name='Transactions')
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Transactions']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1
        })
        
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1
        })
        
        text_format = workbook.add_format({
            'border': 1
        })
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 15)  # Entity Type
        worksheet.set_column('C:C', 18)  # Entity Sub Type
        worksheet.set_column('D:D', 20)  # Entity Name
        worksheet.set_column('E:E', 12)  # Vch Type
        worksheet.set_column('F:F', 25)  # Particulars
        worksheet.set_column('G:J', 15)  # Numeric columns
        
        # Format header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Format data rows
        for row_num in range(len(df)):
            # Date
            worksheet.write(row_num + 1, 0, df.iloc[row_num, 0], date_format)
            
            # Text columns
            for col_num in range(1, 6):
                worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], text_format)
            
            # Number columns
            for col_num in range(6, 10):
                worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], number_format)
        
        # Freeze header row
        worksheet.freeze_panes(1, 0)
        
        # Add autofilter
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    
    # Print summary
    print(f"\n✓ Created Excel file: {output_path}")
    print(f"\nSummary:")
    print(f"  Total Rows: {len(df)}")
    print(f"  Date Range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Entity Types: {df['Entity Type'].nunique()}")
    print(f"  Entity Names: {df['Entity Name'].nunique()}")
    print(f"\nTotals:")
    print(f"  Cash Dr (R):  {df['Cash Dr (R)'].sum():>15,.2f}")
    print(f"  Cash Cr (P):  {df['Cash Cr (P)'].sum():>15,.2f}")
    print(f"  Bank Dr (R):  {df['Bank Dr (R)'].sum():>15,.2f}")
    print(f"  Bank Cr (P):  {df['Bank Cr (P)'].sum():>15,.2f}")
    print(f"\nFile ready for testing!")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample Excel file for testing')
    parser.add_argument('-n', '--rows', type=int, default=100, help='Number of rows to generate')
    parser.add_argument('-o', '--output', type=str, default='sample_data.xlsx', help='Output file path')
    
    args = parser.parse_args()
    
    # Create file
    create_excel_file(args.output, args.rows)

if __name__ == '__main__':
    main()

