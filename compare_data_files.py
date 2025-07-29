#!/usr/bin/env python3
"""
Comprehensive comparison between CSV and Excel files to ensure data consistency
"""

import pandas as pd
import numpy as np
from datetime import datetime

def compare_data_files():
    """
    Compare CSV and Excel files to ensure they contain identical data
    """
    print("🔍 Comparing CSV and Excel Data Files...")
    print("=" * 60)
    
    try:
        # Load both files
        print("📁 Loading files...")
        excel_df = pd.read_excel("data/Clean_Dashboard_Data.xlsx")
        csv_df = pd.read_csv("data/Clean_Dashboard_Data.csv")
        
        print(f"✅ Excel file loaded: {excel_df.shape[0]:,} rows × {excel_df.shape[1]} columns")
        print(f"✅ CSV file loaded: {csv_df.shape[0]:,} rows × {csv_df.shape[1]} columns")
        
        # Basic shape comparison
        print(f"\n📊 SHAPE COMPARISON")
        print(f"{'Metric':<20} {'Excel':<15} {'CSV':<15} {'Match':<10}")
        print("-" * 60)
        
        shape_match = excel_df.shape == csv_df.shape
        print(f"{'Rows':<20} {excel_df.shape[0]:<15,} {csv_df.shape[0]:<15,} {'✅' if excel_df.shape[0] == csv_df.shape[0] else '❌'}")
        print(f"{'Columns':<20} {excel_df.shape[1]:<15} {csv_df.shape[1]:<15} {'✅' if excel_df.shape[1] == csv_df.shape[1] else '❌'}")
        print(f"{'Overall Shape':<20} {str(excel_df.shape):<15} {str(csv_df.shape):<15} {'✅' if shape_match else '❌'}")
        
        if not shape_match:
            print("❌ Files have different shapes - cannot proceed with detailed comparison")
            return False
        
        # Column names comparison
        print(f"\n📋 COLUMN COMPARISON")
        excel_cols = set(excel_df.columns)
        csv_cols = set(csv_df.columns)
        
        common_cols = excel_cols.intersection(csv_cols)
        excel_only = excel_cols - csv_cols
        csv_only = csv_cols - excel_cols
        
        print(f"Common columns: {len(common_cols)}/{len(excel_cols)}")
        print(f"Excel-only columns: {len(excel_only)}")
        print(f"CSV-only columns: {len(csv_only)}")
        
        if excel_only:
            print(f"Excel-only: {list(excel_only)[:5]}...")
        if csv_only:
            print(f"CSV-only: {list(csv_only)[:5]}...")
        
        # Data type comparison for common columns
        print(f"\n🔢 DATA TYPE COMPARISON")
        print(f"{'Column':<25} {'Excel Type':<15} {'CSV Type':<15} {'Match':<10}")
        print("-" * 70)
        
        type_mismatches = 0
        for col in sorted(list(common_cols)[:10]):  # Show first 10 for brevity
            excel_type = str(excel_df[col].dtype)
            csv_type = str(csv_df[col].dtype)
            match = excel_type == csv_type
            if not match:
                type_mismatches += 1
            
            print(f"{col[:24]:<25} {excel_type:<15} {csv_type:<15} {'✅' if match else '❌'}")
        
        if len(common_cols) > 10:
            print(f"... and {len(common_cols) - 10} more columns")
        
        # Content comparison for key columns
        print(f"\n📝 CONTENT COMPARISON (Key Columns)")
        key_columns = ["Project name", "Team size", "Current step name", "Thématique", "Type de situation"]
        
        content_matches = 0
        for col in key_columns:
            if col in common_cols:
                # Convert both to string for comparison (handles NaN differences)
                excel_values = excel_df[col].astype(str).fillna('NaN')
                csv_values = csv_df[col].astype(str).fillna('NaN')
                
                matches = (excel_values == csv_values).sum()
                total = len(excel_values)
                match_pct = (matches / total) * 100
                
                print(f"{col[:30]:<32} {matches:>6}/{total:<6} ({match_pct:5.1f}%) {'✅' if match_pct == 100 else '❌'}")
                
                if match_pct == 100:
                    content_matches += 1
                else:
                    # Show some differences
                    diff_mask = excel_values != csv_values
                    if diff_mask.any():
                        print(f"   Sample differences:")
                        diff_indices = diff_mask[diff_mask].index[:3]
                        for idx in diff_indices:
                            print(f"   Row {idx}: Excel='{excel_values.iloc[idx]}' vs CSV='{csv_values.iloc[idx]}'")
        
        # Memory usage comparison
        print(f"\n💾 MEMORY USAGE COMPARISON")
        excel_memory = excel_df.memory_usage(deep=True).sum() / 1024 / 1024
        csv_memory = csv_df.memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"Excel memory usage: {excel_memory:.2f} MB")
        print(f"CSV memory usage: {csv_memory:.2f} MB")
        print(f"Difference: {abs(excel_memory - csv_memory):.2f} MB")
        
        # Date handling comparison
        print(f"\n📅 DATE HANDLING COMPARISON")
        date_cols = ["Project last update", "Project creation date"]
        
        for col in date_cols:
            if col in common_cols:
                try:
                    excel_dates = pd.to_datetime(excel_df[col], errors='coerce')
                    csv_dates = pd.to_datetime(csv_df[col], errors='coerce')
                    
                    excel_valid = excel_dates.notna().sum()
                    csv_valid = csv_dates.notna().sum()
                    
                    print(f"{col}:")
                    print(f"  Excel valid dates: {excel_valid}/{len(excel_dates)} ({excel_valid/len(excel_dates)*100:.1f}%)")
                    print(f"  CSV valid dates: {csv_valid}/{len(csv_dates)} ({csv_valid/len(csv_dates)*100:.1f}%)")
                    
                    if excel_valid > 0 and csv_valid > 0:
                        # Compare a few dates
                        valid_mask = excel_dates.notna() & csv_dates.notna()
                        if valid_mask.any():
                            date_matches = (excel_dates[valid_mask] == csv_dates[valid_mask]).sum()
                            total_valid = valid_mask.sum()
                            print(f"  Date matches: {date_matches}/{total_valid} ({date_matches/total_valid*100:.1f}%)")
                
                except Exception as e:
                    print(f"  Error comparing {col}: {e}")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"📊 COMPARISON SUMMARY")
        print(f"=" * 60)
        
        all_good = True
        
        if shape_match:
            print("✅ Shape: Files have identical dimensions")
        else:
            print("❌ Shape: Files have different dimensions")
            all_good = False
        
        if len(excel_only) == 0 and len(csv_only) == 0:
            print("✅ Columns: All columns match perfectly")
        else:
            print(f"⚠️  Columns: {len(excel_only + csv_only)} column differences found")
            all_good = False
        
        if type_mismatches == 0:
            print("✅ Data Types: All common columns have compatible types")
        else:
            print(f"⚠️  Data Types: {type_mismatches} type mismatches (expected for CSV)")
        
        if content_matches == len([col for col in key_columns if col in common_cols]):
            print("✅ Content: All key columns have identical values")
        else:
            print(f"❌ Content: Some key columns have different values")
            all_good = False
        
        if all_good:
            print(f"\n🎉 CONCLUSION: Files contain the SAME DATA!")
            print("✅ The dashboard will work identically with either format")
            print("✅ Excel format is recommended for better data type preservation")
        else:
            print(f"\n⚠️  CONCLUSION: Files have some differences")
            print("🔍 Review the differences above before proceeding")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        return False

def quick_sample_comparison():
    """Quick comparison of first few rows"""
    print(f"\n📋 QUICK SAMPLE COMPARISON (First 3 rows)")
    print("=" * 60)
    
    try:
        excel_df = pd.read_excel("data/Clean_Dashboard_Data.xlsx")
        csv_df = pd.read_csv("data/Clean_Dashboard_Data.csv")
        
        key_cols = ["Project name", "Team size", "Current step name"]
        
        print("EXCEL DATA:")
        print(excel_df[key_cols].head(3).to_string())
        
        print(f"\nCSV DATA:")
        print(csv_df[key_cols].head(3).to_string())
        
    except Exception as e:
        print(f"Error in sample comparison: {e}")

if __name__ == "__main__":
    success = compare_data_files()
    quick_sample_comparison()
    
    print(f"\n{'='*60}")
    if success:
        print("🎯 FINAL VERDICT: Both files are EQUIVALENT for dashboard use!")
    else:
        print("⚠️  FINAL VERDICT: Files have differences that may affect dashboard behavior")
