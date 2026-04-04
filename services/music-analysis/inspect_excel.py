#!/usr/bin/env python3
"""
Inspect Excel file structure to understand SoundCloud data format
"""
import pandas as pd
from pathlib import Path

def inspect_excel():
    """Inspect the Excel file to understand its structure"""
    excel_file = Path("../WordsOnText/SoundCloud to X Reposter.xlsx")
    
    print(f"🔍 Inspecting Excel file: {excel_file}")
    print(f"📁 File exists: {excel_file.exists()}")
    
    if not excel_file.exists():
        print("❌ Excel file not found!")
        return
    
    try:
        # Get all sheet names
        xls = pd.ExcelFile(excel_file)
        print(f"📊 Available sheets: {xls.sheet_names}")
        
        # Inspect each sheet
        for sheet_name in xls.sheet_names:
            print(f"\n🔍 Sheet: {sheet_name}")
            print("-" * 40)
            
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                print(f"📐 Shape: {df.shape} (rows, columns)")
                print(f"📋 Columns: {list(df.columns)}")
                
                # Show first few rows
                print("\n📝 First 3 rows:")
                print(df.head(3).to_string())
                
                # Look for URLs
                soundcloud_urls = 0
                for col in df.columns:
                    for val in df[col].astype(str):
                        if 'soundcloud.com' in val:
                            soundcloud_urls += 1
                
                print(f"\n🔗 SoundCloud URLs found: {soundcloud_urls}")
                
                # Check for non-null values in key columns
                potential_url_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['url', 'link', 'soundcloud'])]
                if potential_url_cols:
                    print(f"🎯 Potential URL columns: {potential_url_cols}")
                    for col in potential_url_cols:
                        non_null = df[col].notna().sum()
                        print(f"   {col}: {non_null}/{len(df)} non-null values")
                
            except Exception as e:
                print(f"❌ Error reading sheet {sheet_name}: {e}")
        
    except Exception as e:
        print(f"❌ Error inspecting Excel file: {e}")

if __name__ == "__main__":
    inspect_excel()
