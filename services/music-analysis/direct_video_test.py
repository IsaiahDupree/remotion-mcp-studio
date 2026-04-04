#!/usr/bin/env python3
"""
Direct Video Processing Test - No API Required
Test video processing functionality directly
"""
import sys
import os
from pathlib import Path
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_direct_video_processing():
    """Test video processing directly without API"""
    print("🎬 DIRECT VIDEO PROCESSING TEST")
    print("=" * 35)
    
    # Check if video file exists
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\direct_test.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print(f"✅ Video file found: {Path(video_path).name}")
    file_size = Path(video_path).stat().st_size / (1024 * 1024)
    print(f"   Size: {file_size:.1f} MB")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Import video processor
        print("\n⏳ Loading video processor...")
        from video_processor import VideoProcessor
        
        processor = VideoProcessor()
        print("✅ Video processor loaded successfully")
        print(f"   FFmpeg: {processor.ffmpeg_path}")
        
        # Test simple text overlay
        print("\n🎨 Adding text overlay...")
        start_time = time.time()
        
        result = processor.process_video_with_music_and_text(
            video_path=video_path,
            music_path=None,  # No music for this test
            text_lines=["Direct Processing Test"],
            output_path=output_path,
            text_position="bottom",
            preserve_audio=True
        )
        
        processing_time = time.time() - start_time
        
        if result.get('success'):
            print("✅ Text overlay processing successful!")
            print(f"   Output: {result['output_path']}")
            print(f"   Processing time: {processing_time:.1f}s")
            
            # Check output file
            if Path(result['output_path']).exists():
                output_size = Path(result['output_path']).stat().st_size / (1024 * 1024)
                print(f"   Output size: {output_size:.1f} MB")
                return True
            else:
                print("❌ Output file was not created")
                return False
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure video_processor.py is available")
        return False
    except Exception as e:
        print(f"❌ Processing error: {e}")
        logger.exception("Full error details:")
        return False

def test_music_processing():
    """Test video processing with background music"""
    print("\n🎵 TESTING MUSIC + VIDEO PROCESSING")
    print("=" * 40)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    music_dir = r"C:\Users\Isaia\Documents\Coding\N8N\shared\music_library"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\direct_music_test.mp4"
    
    # Find a music file
    music_files = list(Path(music_dir).glob("*.mp3"))
    if not music_files:
        print("⚠️ No music files found, skipping music test")
        return False
    
    music_path = str(music_files[0])
    print(f"✅ Using music: {Path(music_path).name}")
    
    try:
        from video_processor import VideoProcessor
        
        processor = VideoProcessor()
        
        print("⏳ Processing video with music and text...")
        start_time = time.time()
        
        result = processor.process_video_with_music_and_text(
            video_path=video_path,
            music_path=music_path,
            output_path=output_path,
            text_overlay="Music + Text Test",
            text_position="bottom_center",
            music_volume=-20
        )
        
        processing_time = time.time() - start_time
        
        if result.get('success'):
            print("✅ Music processing successful!")
            print(f"   Output: {result['output_path']}")
            print(f"   Processing time: {processing_time:.1f}s")
            
            if Path(result['output_path']).exists():
                output_size = Path(result['output_path']).stat().st_size / (1024 * 1024)
                print(f"   Output size: {output_size:.1f} MB")
                return True
            else:
                print("❌ Output file was not created")
                return False
        else:
            print(f"❌ Music processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Music processing error: {e}")
        return False

def main():
    """Run direct video processing tests"""
    print("🔬 DIRECT VIDEO PROCESSING TESTS")
    print("=" * 40)
    
    # Test 1: Simple text overlay
    text_success = test_direct_video_processing()
    
    # Test 2: Music + text processing  
    music_success = test_music_processing()
    
    print(f"\n📊 TEST RESULTS")
    print("=" * 15)
    print(f"Text Overlay: {'✅ PASS' if text_success else '❌ FAIL'}")
    print(f"Music + Text: {'✅ PASS' if music_success else '❌ FAIL'}")
    
    if text_success and music_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("🚀 Video processing is working - ready for API integration")
    elif text_success:
        print(f"\n⚠️ BASIC PROCESSING WORKS")
        print("🔧 Music processing needs attention")
    else:
        print(f"\n❌ CORE PROCESSING FAILED")
        print("🔧 Check video_processor.py and FFmpeg")

if __name__ == "__main__":
    main()
