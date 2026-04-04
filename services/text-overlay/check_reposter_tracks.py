#!/usr/bin/env python3
"""
Check SoundCloud to X Reposter Excel File
=========================================
Examine the structure and content of the reposter tracks file
"""

import pandas as pd
import os

def check_reposter_excel():
    """Check the SoundCloud to X Reposter Excel file structure"""
    
    excel_path = "SoundCloud to X Reposter.xlsx"
    
    print("🎵 SoundCloud to X Reposter Tracks Analysis")
    print("=" * 60)
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return False
    
    try:
        # Read the Excel file - check if it has multiple sheets
        excel_file = pd.ExcelFile(excel_path)
        sheets = excel_file.sheet_names
        print(f"📋 Available sheets: {sheets}")
        
        # Read the first sheet (or main sheet)
        df = pd.read_excel(excel_path, sheet_name=sheets[0])
        
        print(f"\n📊 Sheet: {sheets[0]}")
        print(f"📊 Total rows: {len(df)}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\n📝 First 10 rows:")
        print("-" * 100)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 60)
        print(df.head(10).to_string(index=True))
        
        # Check for URL columns
        url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'soundcloud' in col.lower()]
        print(f"\n🔗 Potential URL columns: {url_columns}")
        
        # Look for any column that might contain URLs
        for col in df.columns:
            sample_values = df[col].dropna().head(3)
            for val in sample_values:
                if isinstance(val, str) and ('soundcloud.com' in val.lower() or 'http' in val.lower()):
                    print(f"🎵 Found URLs in column '{col}':")
                    valid_urls = df[col].dropna()
                    print(f"   ✅ Total entries: {len(valid_urls)}")
                    
                    # Show sample URLs
                    for i, url in enumerate(valid_urls.head(10)):
                        if pd.notna(url) and 'http' in str(url).lower():
                            print(f"   {i+1}. {str(url)[:80]}...")
                    break
        
        # Check for title/name columns
        title_columns = [col for col in df.columns if any(word in col.lower() for word in ['title', 'name', 'track', 'song'])]
        print(f"\n🎵 Title columns: {title_columns}")
        
        # Check for artist columns
        artist_columns = [col for col in df.columns if any(word in col.lower() for word in ['artist', 'creator', 'author', 'user'])]
        print(f"🎤 Artist columns: {artist_columns}")
        
        # Show data types
        print(f"\n📊 Column data types:")
        for col in df.columns:
            print(f"   {col}: {df[col].dtype}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_reposter_excel()
