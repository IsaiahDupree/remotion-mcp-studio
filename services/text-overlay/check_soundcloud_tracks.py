#!/usr/bin/env python3
"""
Check SoundCloud Tracks Excel File
==================================
Examine the structure and content of the SoundCloud tracks file
"""

import pandas as pd
import os

def check_soundcloud_excel():
    """Check the SoundCloud Excel file structure"""
    
    excel_path = "SoundCloud_Tracks.xlsx"
    
    print("🎵 SoundCloud Tracks Analysis")
    print("=" * 50)
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return False
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        print(f"📊 Total tracks: {len(df)}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\n📝 First 5 tracks:")
        print("-" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df.head().to_string(index=False))
        
        # Check for track URLs
        url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()]
        print(f"\n🔗 URL columns found: {url_columns}")
        
        if url_columns:
            url_col = url_columns[0]
            valid_urls = df[url_col].dropna()
            print(f"✅ Valid URLs: {len(valid_urls)}")
            
            # Show sample URLs
            print(f"\n🎵 Sample tracks:")
            for i, url in enumerate(valid_urls.head(10)):
                if pd.notna(url) and str(url).startswith('http'):
                    track_name = df.iloc[i].get('Title', df.iloc[i].get('Track', f'Track {i+1}'))
                    print(f"   {i+1}. {track_name}")
                    print(f"      URL: {str(url)[:60]}...")
        
        # Check for popularity/ranking columns
        ranking_cols = [col for col in df.columns if any(word in col.lower() for word in ['rank', 'popular', 'play', 'like', 'view'])]
        print(f"\n📈 Ranking columns: {ranking_cols}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

if __name__ == "__main__":
    check_soundcloud_excel()
