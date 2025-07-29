#!/usr/bin/env python3
"""
Quick test script to validate dashboard functionality
"""

import pandas as pd
import sys
import os

def test_data_loading():
    """Test if data files exist and can be loaded"""
    try:
        # Check if data files exist
        data_files = [
            "data/Clean_Dashboard_Data.xlsx",
            "data/Clean_Dashboard_Data.csv",
            "data/GoMvmt.xlsx"
        ]
        
        for file in data_files:
            if os.path.exists(file):
                print(f"✅ {file} exists")
                if file.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    print(f"   📊 {len(df)} rows, {len(df.columns)} columns")
                elif file.endswith('.csv'):
                    df = pd.read_csv(file)
                    print(f"   📊 {len(df)} rows, {len(df.columns)} columns")
            else:
                print(f"❌ {file} missing")
        
        return True
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def test_required_columns():
    """Test if required columns exist in main data file"""
    try:
        df = pd.read_excel("data/Clean_Dashboard_Data.xlsx")
        required_columns = [
            "Project name", "Team size", "Project last update",
            "Current step name", "Thématique", "Type de situation"
        ]
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return False
        else:
            print("✅ All required columns present")
            return True
            
    except Exception as e:
        print(f"❌ Error checking columns: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Dashboard Components...")
    print("=" * 50)
    
    success = True
    success &= test_data_loading()
    success &= test_required_columns()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed! Dashboard should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    sys.exit(0 if success else 1)
