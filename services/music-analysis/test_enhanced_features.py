#!/usr/bin/env python3
"""
Test Enhanced Video Processing Features
- Smart text placement (avoiding faces)
- Proper audio mixing (-20 to -30dB)
- OpenAI-powered video analysis
- Directory path compatibility
"""
import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:5001"

def test_enhanced_processing():
    """Test enhanced video processing with all new features"""
    print("🎬 TESTING ENHANCED VIDEO PROCESSING")
    print("=" * 50)
    
    # Test video from shared directory
    video_path = 'C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4'
    
    test_cases = [
        {
            'name': 'Smart Positioning + Preserve Audio',
            'data': {
                'video_path': video_path,
                'music_path': 'auto',
                'text_lines': ['Smart Text Placement', 'Preserves Original Audio'],
                'output_name': 'test_smart_positioning.mp4',
                'music_volume_db': -25.0,
                'preserve_audio': True,
                'smart_positioning': True
            }
        },
        {
            'name': 'Background Only Audio',
            'data': {
                'video_path': video_path,
                'music_path': 'auto',
                'text_lines': ['Background Music Only', 'No Original Audio'],
                'output_name': 'test_bg_only.mp4',
                'music_volume_db': -22.0,
                'preserve_audio': False,
                'smart_positioning': True
            }
        },
        {
            'name': 'Quiet Background (-30dB)',
            'data': {
                'video_path': video_path,
                'music_path': 'auto',
                'text_lines': ['Very Quiet Music', 'Perfect for Voice Content'],
                'output_name': 'test_quiet_bg.mp4',
                'music_volume_db': -30.0,
                'preserve_audio': True,
                'smart_positioning': True
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"   Volume: {test_case['data']['music_volume_db']}dB")
        print(f"   Preserve audio: {test_case['data']['preserve_audio']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/video/process-enhanced",
                json=test_case['data'],
                timeout=120
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS in {elapsed:.1f}s")
                print(f"   📁 Output: {result['output_name']}")
                print(f"   📊 Size: {result['file_size_mb']} MB")
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                print(f"   🔍 Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")

def test_music_video_matching():
    """Test intelligent music-video matching"""
    print("\n🎵 TESTING MUSIC-VIDEO MATCHING")
    print("=" * 50)
    
    video_path = 'C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4'
    
    test_data = {
        'video_path': video_path,
        'transcript': 'Energetic upbeat content with positive vibes',
        'visual_analysis': 'Bright colorful scenes with dynamic movement'
    }
    
    try:
        print("🔍 Analyzing video for music match...")
        response = requests.post(
            f"{API_BASE}/analyze-music-match",
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MUSIC MATCHING SUCCESS!")
            print(f"🎯 Detected mood: {result.get('detected_mood')}")
            
            if result.get('music_recommendation'):
                rec = result['music_recommendation']
                print(f"🎵 Recommended: {rec.get('file_name', 'N/A')}")
                print(f"📊 Compatibility: {rec.get('compatibility_score', 'N/A')}")
                print(f"💡 Reasoning: {rec.get('match_reasoning', 'N/A')[:80]}...")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"🔍 Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def test_system_status():
    """Test comprehensive system status"""
    print("\n📊 TESTING SYSTEM STATUS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/system/status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ SYSTEM HEALTHY")
            
            # Music Database Status
            music_db = status['music_database']
            print(f"\n🎵 MUSIC DATABASE:")
            print(f"   📀 Total tracks: {music_db['total_tracks']}")
            print(f"   💾 Size: {music_db['total_size_gb']} GB")
            print(f"   ⏱️ Duration: {music_db['total_duration_hours']} hours")
            print(f"   🎯 Moods: {', '.join(music_db['moods'].keys())}")
            print(f"   🎼 Genres: {', '.join(music_db['genres'].keys())}")
            
            # Video Processor Status
            video_proc = status['video_processor']
            print(f"\n🎬 VIDEO PROCESSOR:")
            print(f"   🔧 FFmpeg available: {video_proc['ffmpeg_available']}")
            print(f"   📁 Temp dir: {video_proc['temp_dir']}")
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def test_directory_paths():
    """Test directory path compatibility"""
    print("\n📁 TESTING DIRECTORY PATHS")
    print("=" * 50)
    
    paths_to_test = [
        'C:/Users/Isaia/Documents/Coding/N8N/shared/videos',
        'C:/Users/Isaia/Documents/Coding/N8N/soundcloud_music',
        'C:/Users/Isaia/Documents/Coding/N8N/cache/processed_videos'
    ]
    
    for path in paths_to_test:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_dir():
                file_count = len(list(path_obj.iterdir()))
                print(f"✅ {path}: {file_count} items")
            else:
                print(f"✅ {path}: File exists")
        else:
            print(f"❌ {path}: Not found")

def main():
    """Run all enhanced feature tests"""
    print("🚀 ENHANCED FLASK API FEATURE TESTING")
    print("=" * 60)
    print("Testing all new features:")
    print("• Smart text placement (face detection)")
    print("• Proper audio mixing (-20 to -30dB)")
    print("• Enhanced video processing pipeline")
    print("• Music-video matching intelligence")
    print("• Directory path compatibility")
    print("=" * 60)
    
    # Test system status first
    test_system_status()
    
    # Test directory paths
    test_directory_paths()
    
    # Test music-video matching
    test_music_video_matching()
    
    # Test enhanced processing features
    test_enhanced_processing()
    
    print("\n🎯 TESTING COMPLETE!")
    print("Check the processed_videos directory for output files.")

if __name__ == "__main__":
    main()
