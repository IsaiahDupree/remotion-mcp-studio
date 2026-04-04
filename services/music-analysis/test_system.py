#!/usr/bin/env python3
"""Test script for the Music System"""

try:
    from main_system import MusicSystem
    
    print("🎵 Initializing Music System...")
    system = MusicSystem()
    print("✅ System initialized successfully!")
    
    print("\n📊 Getting system status...")
    status = system.get_system_status()
    
    print(f"📁 WordsOnText tracks: {status['music_libraries']['wordsOnText']['tracks']}")
    print(f"🎵 SoundCloud tracks: {status['music_libraries']['soundcloud']['tracks']}")
    print(f"📈 Total tracks available: {status['total_tracks']}")
    
    print(f"💾 Cache files status:")
    for cache_name, exists in status['cache_files'].items():
        print(f"   {cache_name}: {'✅' if exists else '❌'}")
    
    print(f"\n🔄 Trend data status: {status['trend_data']['status']}")
    
    print("\n🚀 Music System is ready for integration!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ System error: {e}")
    print("Check configuration and paths in config.py")
