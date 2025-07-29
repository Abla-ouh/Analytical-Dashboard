#!/usr/bin/env python3
"""
Detailed comparison of date handling between CSV and Excel files
"""

import pandas as pd
from datetime import datetime

def detailed_date_comparison():
    """Compare how dates are handled in both formats"""
    print("📅 DETAILED DATE COMPARISON")
    print("=" * 50)
    
    # Load files
    excel_df = pd.read_excel("data/Clean_Dashboard_Data.xlsx")
    csv_df = pd.read_csv("data/Clean_Dashboard_Data.csv")
    
    date_col = "Project last update"
    
    print(f"Analyzing column: {date_col}")
    print(f"Excel raw values (first 3): {excel_df[date_col].head(3).tolist()}")
    print(f"CSV raw values (first 3): {csv_df[date_col].head(3).tolist()}")
    
    # Check data types
    print(f"\nRaw data types:")
    print(f"Excel: {excel_df[date_col].dtype}")
    print(f"CSV: {csv_df[date_col].dtype}")
    
    # Convert with proper date parsing
    print(f"\nConverting with proper date parsing...")
    
    # Excel dates (should already be datetime)
    if excel_df[date_col].dtype == 'datetime64[ns]':
        excel_dates = excel_df[date_col]
        print("Excel: Already datetime format ✅")
    else:
        excel_dates = pd.to_datetime(excel_df[date_col], errors='coerce')
        print("Excel: Converted to datetime")
    
    # CSV dates (need to specify format to avoid warning)
    csv_dates_auto = pd.to_datetime(csv_df[date_col], errors='coerce')
    csv_dates_format = pd.to_datetime(csv_df[date_col], format='%d/%m/%Y', errors='coerce')
    
    print(f"\nCSV parsing results:")
    print(f"Auto parsing valid: {csv_dates_auto.notna().sum()}/{len(csv_dates_auto)}")
    print(f"DD/MM/YYYY parsing valid: {csv_dates_format.notna().sum()}/{len(csv_dates_format)}")
    
    # Compare the actual date values
    print(f"\nDate value comparison (first 5 valid dates):")
    valid_excel = excel_dates.dropna().head(5)
    valid_csv_auto = csv_dates_auto.dropna().head(5)
    valid_csv_format = csv_dates_format.dropna().head(5)
    
    print("Excel dates:", valid_excel.dt.strftime('%Y-%m-%d').tolist())
    print("CSV auto:", valid_csv_auto.dt.strftime('%Y-%m-%d').tolist())
    print("CSV DD/MM/YYYY:", valid_csv_format.dt.strftime('%Y-%m-%d').tolist())
    
    # Check if using format fixes the issue
    if len(valid_excel) > 0 and len(valid_csv_format) > 0:
        # Compare first few dates
        matches = 0
        for i in range(min(len(valid_excel), len(valid_csv_format))):
            if valid_excel.iloc[i].date() == valid_csv_format.iloc[i].date():
                matches += 1
        
        print(f"\nDate matching with DD/MM/YYYY format: {matches}/{min(len(valid_excel), len(valid_csv_format))}")
    
    print(f"\n💡 RECOMMENDATION:")
    print("The dashboard should use format='%d/%m/%Y' when parsing CSV dates")
    print("Excel format preserves dates better and doesn't need format specification")

if __name__ == "__main__":
    detailed_date_comparison()
