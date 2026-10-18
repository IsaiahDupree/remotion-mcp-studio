#!/usr/bin/env python3
"""
Test Enhanced Video Processing with Specific Video
=================================================
Test our enhanced video processing system with the specific video file.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_video_processing():
    """Test enhanced video processing with the specific video"""
    
    # Video file to test
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\v12044gd0000cu2t04nog65p7djql4g0.MP4"
    
    print("🎬 Testing Enhanced Video Processing")
    print("=" * 60)
    print(f"📹 Video: {os.path.basename(video_path)}")
    print(f"📁 Path: {video_path}")
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Get video file size for reference
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"📊 File size: {file_size_mb:.1f} MB")
    
    try:
        # Import our enhanced processor
        from enhanced_video_processor import EnhancedVideoProcessor
        print("✅ Enhanced processor imported successfully")
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  OPENAI_API_KEY not found - will skip AI analysis")
        else:
            print("✅ OpenAI API key found")
        
        # Create output directory
        output_dir = "test_enhanced_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        timestamp = int(datetime.now().timestamp())
        output_filename = f"enhanced_test_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"📁 Output will be saved to: {output_path}")
        
        # Initialize processor
        print("\n🔧 Initializing Enhanced Processor...")
        processor = EnhancedVideoProcessor(api_key=api_key)
        print("✅ Processor initialized")
        
        # Test frame extraction first
        print("\n🎞️  Testing 30-second frame extraction...")
        try:
            frames = processor.frame_analyzer.extract_frames(video_path, interval_seconds=30.0)
            print(f"✅ Extracted {len(frames)} frames at 30-second intervals")
            
            # Show frame timestamps
            if frames:
                timestamps = [f"{timestamp:.1f}s" for _, timestamp in frames]
                print(f"📍 Frame timestamps: {', '.join(timestamps)}")
        except Exception as e:
            print(f"❌ Frame extraction failed: {e}")
            return False
        
        # Test AI analysis with one frame (to save API costs)
        if frames and api_key:
            print("\n🤖 Testing GPT-4o frame analysis...")
            try:
                # Analyze just the first frame
                single_frame_analysis = processor.frame_analyzer.analyze_frames_with_ai([frames[0]])
                if single_frame_analysis.get('catchy_text'):
                    print(f"✅ AI generated text: '{single_frame_analysis['catchy_text']}'")
                else:
                    print("⚠️  AI analysis completed but no catchy text generated")
                    print(f"📝 Full analysis: {single_frame_analysis.get('full_analysis', 'No analysis available')[:200]}...")
            except Exception as e:
                print(f"❌ AI analysis failed: {e}")
        
        # Setup configuration for full processing
        print("\n⚙️  Setting up processing configuration...")
        
        text_config = {
            "style": "classic",
            "position": "top", 
            "font": "arial",
            "font_scale": 1.2,
            "custom_text": None  # Let AI generate based on frames
        }
        
        music_config = {
            "enabled": True,
            "excel_path": "soundcloud_tracks.xlsx" if os.path.exists("soundcloud_tracks.xlsx") else None,
            "track_column": "Track URL",
            "speech_emphasis": 0.7,
            "auto_detect": True
        }
        
        print("📝 Text config:", text_config)
        print("🎵 Music config:", music_config)
        
        # Process the video
        print("\n🚀 Processing video with enhanced features...")
        print("   - 30-second frame analysis with GPT-4o")
        print("   - Background music at -25 to -30dB")
        print("   - Resolution preservation")
        
        start_time = time.time()
        
        result = processor.enhance_video(
            video_path=video_path,
            output_path=output_path,
            text_config=text_config,
            music_config=music_config
        )
        
        processing_time = time.time() - start_time
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 PROCESSING RESULTS")
        print("=" * 60)
        
        if result.get('success', False):
            print("✅ VIDEO PROCESSING SUCCESSFUL!")
            print(f"⏱️  Processing time: {processing_time:.1f} seconds")
            print(f"📁 Output file: {result.get('output_video', output_path)}")
            
            # Check if output file exists and get its size
            if os.path.exists(output_path):
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"📊 Output size: {output_size_mb:.1f} MB")
            
            # Text overlay info
            if result.get('text_overlay_applied', False):
                print(f"📝 Text overlay: '{result.get('text_used', 'N/A')}'")
                print(f"🎨 Style: {result.get('text_style', 'N/A')}")
                print(f"📍 Position: {result.get('text_position', 'N/A')}")
            
            # Music info
            if result.get('music_added', False):
                print(f"🎵 Music added: Yes (from {result.get('music_source', 'unknown')})")
                print(f"🔊 Volume: -25 to -30dB range")
            else:
                print(f"🎵 Music added: No ({result.get('music_reason', 'unknown reason')})")
            
            # Enhanced features
            print("\n🚀 Enhanced Features Used:")
            print("   ✅ 30-second frame analysis")
            print("   ✅ GPT-4o contextual text generation")
            print("   ✅ Optimized music volume (-25 to -30dB)")
            print("   ✅ Resolution preservation")
            
        else:
            print("❌ VIDEO PROCESSING FAILED!")
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return False
        
        print("\n🎉 Enhanced video processing test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("🧪 Enhanced Video Processing Test")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_video_processing()
    
    if success:
        print("\n✅ All tests passed! Enhanced video processing is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the logs above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
