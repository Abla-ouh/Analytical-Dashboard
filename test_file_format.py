#!/usr/bin/env python3
"""
Test script for file format detection
"""

import pandas as pd
import os
from datetime import datetime

def test_file_format_detection():
    """Test the file format detection logic"""
    print("🔍 Testing File Format Detection...")
    print("=" * 50)
    
    # Define possible file paths in order of preference
    file_paths = [
        "data/Clean_Dashboard_Data.xlsx",  # Primary: Excel format
        "data/Clean_Dashboard_Data.csv"    # Fallback: CSV format
    ]
    
    data = None
    used_file = None
    
    # Try each file format
    for file_path in file_paths:
        print(f"🔍 Trying to load: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            continue
            
        try:
            file_size = os.path.getsize(file_path)
            print(f"   📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            if file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path)
                used_file = file_path
                data_source = f"📊 Excel: {file_path}"
                print(f"   ✅ Successfully loaded Excel file")
                break
            elif file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
                used_file = file_path
                data_source = f"📄 CSV: {file_path}"
                print(f"   ✅ Successfully loaded CSV file")
                break
                
        except FileNotFoundError:
            print(f"   ❌ File not found: {file_path}")
            continue
        except Exception as e:
            print(f"   ❌ Error loading {file_path}: {str(e)}")
            continue
    
    if data is None:
        print("\n❌ No valid data file found!")
        return False
    
    # Show results
    print(f"\n🎉 Successfully loaded data!")
    print(f"📁 Source: {data_source}")
    print(f"📊 Shape: {data.shape[0]:,} rows × {data.shape[1]} columns")
    print(f"💾 Memory usage: {data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # Check required columns
    required_columns = [
        "Project name", "Team size", "Project last update",
        "Current step name", "Thématique", "Type de situation"
    ]
    
    print(f"\n🔍 Checking required columns...")
    missing_cols = [col for col in required_columns if col not in data.columns]
    
    if missing_cols:
        print(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return False
    else:
        print(f"✅ All required columns present!")
    
    # Show data sample
    print(f"\n📋 Data sample:")
    print(data[required_columns].head(3))
    
    print("\n" + "=" * 50)
    print("🎉 File format detection test completed successfully!")
    
    return True

if __name__ == "__main__":
    test_file_format_detection()
