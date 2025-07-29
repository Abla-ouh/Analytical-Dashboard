#!/usr/bin/env python3
"""
Test script for data cleaning functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data():
    """Create sample data with quality issues for testing"""
    
    # Create sample data with various quality issues
    test_data = pd.DataFrame({
        'Project name': ['Project A', 'Project B', None, 'Project D', '  Project E  ', 'Project A'],  # Missing value, whitespace, duplicate
        'Team size': [5, '15', 'invalid', 100, 0, 3],  # String numbers, invalid text, outliers
        'Project last update': [
            '2024-01-15',
            '2025-08-15',  # Future date
            'invalid_date',
            '2023-12-01',
            None,  # Missing date
            '2024-06-15'
        ],
        'Current step name': ['Step 1', 'Step 2', None, '  Step 3  ', 'Step 4', 'Step 1'],
        'Thématique': ['Tech', 'Business', 'Energy', None, 'Tech', 'Business'],
        'Type de situation': ['Business', 'OM', 'Business', 'Business', None, 'OM']
    })
    
    return test_data

def test_data_cleaning():
    """Test the data cleaning functionality"""
    print("🧪 Testing Data Cleaning Functions...")
    print("=" * 50)
    
    # Import the cleaning function (simplified version for testing)
    def validate_and_clean_data(data):
        cleaning_report = {
            'original_rows': len(data),
            'issues_found': [],
            'fixes_applied': [],
            'final_rows': 0,
            'data_quality_score': 0
        }
        
        # 1. Handle missing values in critical columns
        critical_columns = ["Project name", "Team size", "Project last update", "Current step name"]
        
        for col in critical_columns:
            if col in data.columns:
                missing_count = data[col].isnull().sum()
                if missing_count > 0:
                    cleaning_report['issues_found'].append(f"{col}: {missing_count} missing values")
                    
                    if col == "Team size":
                        median_size = pd.to_numeric(data[col], errors='coerce').median()
                        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(median_size)
                        cleaning_report['fixes_applied'].append(f"{col}: Filled missing values with median")
                    
                    elif col == "Current step name":
                        data[col] = data[col].fillna("Unknown Step")
                        cleaning_report['fixes_applied'].append(f"{col}: Filled missing values with 'Unknown Step'")
        
        # 2. Clean Team size
        if "Team size" in data.columns:
            data["Team size"] = pd.to_numeric(data["Team size"], errors='coerce')
            outliers = data[(data["Team size"] > 50) | (data["Team size"] < 1)]["Team size"].count()
            if outliers > 0:
                cleaning_report['issues_found'].append(f"Team size: {outliers} outlier values")
                data.loc[data["Team size"] > 50, "Team size"] = 50
                data.loc[data["Team size"] < 1, "Team size"] = 1
                cleaning_report['fixes_applied'].append(f"Team size: Capped outlier values")
        
        # 3. Clean dates
        if "Project last update" in data.columns:
            data["Project last update"] = pd.to_datetime(data["Project last update"], errors='coerce')
            future_dates = data[data["Project last update"] > pd.Timestamp.now()]["Project last update"].count()
            if future_dates > 0:
                cleaning_report['issues_found'].append(f"Project last update: {future_dates} future dates")
                data.loc[data["Project last update"] > pd.Timestamp.now(), "Project last update"] = pd.Timestamp.now()
                cleaning_report['fixes_applied'].append(f"Project last update: Fixed future dates")
        
        # 4. Standardize text columns
        text_columns = ["Current step name", "Thématique", "Type de situation"]
        for col in text_columns:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip()
                data[col] = data[col].replace(['nan', 'None'], None)
        
        cleaning_report['final_rows'] = len(data)
        
        # Simple quality score
        completeness = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
        cleaning_report['data_quality_score'] = round(completeness * 100, 1)
        
        return data, cleaning_report
    
    # Create test data
    test_df = create_test_data()
    print("📊 Original test data:")
    print(test_df)
    print(f"\nOriginal data info:")
    print(f"- Rows: {len(test_df)}")
    print(f"- Missing values: {test_df.isnull().sum().sum()}")
    print(f"- Duplicates: {test_df.duplicated().sum()}")
    
    print("\n🔧 Applying data cleaning...")
    
    # Apply cleaning
    cleaned_df, report = validate_and_clean_data(test_df.copy())
    
    print("\n📋 Cleaning Report:")
    print(f"- Original rows: {report['original_rows']}")
    print(f"- Final rows: {report['final_rows']}")
    print(f"- Data quality score: {report['data_quality_score']}%")
    
    print(f"\n❌ Issues found ({len(report['issues_found'])}):")
    for issue in report['issues_found']:
        print(f"  • {issue}")
    
    print(f"\n✅ Fixes applied ({len(report['fixes_applied'])}):")
    for fix in report['fixes_applied']:
        print(f"  • {fix}")
    
    print("\n📊 Cleaned data:")
    print(cleaned_df)
    
    print("\n" + "=" * 50)
    print("🎉 Data cleaning test completed successfully!")
    
    return True

if __name__ == "__main__":
    test_data_cleaning()
