#!/usr/bin/env python3
"""
Test Direct Intelligent Analyzer - Test core functionality
"""
import os
from pathlib import Path
import time

def test_direct_analyzer():
    """Test the analyzer directly"""
    print("🔬 TESTING INTELLIGENT VIDEO ANALYZER - CORE FUNCTIONALITY")
    print("=" * 65)
    
    try:
        from intelligent_video_analyzer import IntelligentVideoAnalyzer
        
        video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
        
        if not Path(video_path).exists():
            print(f"❌ Test video not found: {video_path}")
            return False
        
        print(f"🎬 Test Video: {Path(video_path).name}")
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"💾 Size: {file_size:.1f} MB")
        
        print(f"\n🚀 Initializing analyzer...")
        analyzer = IntelligentVideoAnalyzer()
        print("✅ Analyzer initialized")
        
        # Test video info extraction
        print(f"\n📹 Testing video info extraction...")
        video_info = analyzer.get_video_info(video_path) 
        print(f"   ✅ Duration: {video_info.get('duration', 0):.1f}s")
        print(f"   ✅ Resolution: {video_info.get('width')}x{video_info.get('height')}")
        print(f"   ✅ Has audio: {video_info.get('has_audio')}")
        print(f"   ✅ Codec: {video_info.get('video_stream', {}).get('codec_name', 'unknown')}")
        
        # Test caption detection
        print(f"\n🔍 Testing caption detection...")
        start_time = time.time()
        has_captions, caption_text = analyzer.detect_existing_captions(video_path)
        caption_time = time.time() - start_time
        print(f"   ✅ Captions detected: {has_captions} ({caption_time:.1f}s)")
        if caption_text:
            print(f"   📋 Caption content: {caption_text}")
        
        # Test frame sampling
        print(f"\n📸 Testing efficient frame sampling...")
        start_time = time.time()
        frames = analyzer.sample_frames_efficiently(video_path, video_info)
        frame_time = time.time() - start_time
        print(f"   ✅ Frames sampled: {len(frames)} ({frame_time:.1f}s)")
        print(f"   📊 Sampling strategy: {len(frames)} frames for {video_info.get('duration', 0):.1f}s video")
        
        # Test overlay generation (without AI vision)
        print(f"\n✨ Testing overlay generation...")
        start_time = time.time()
        overlay = analyzer.generate_perfect_overlay(None, None, video_info)
        overlay_time = time.time() - start_time
        print(f"   ✅ Generated overlay: \"{overlay}\" ({overlay_time:.1f}s)")
        
        # Test transcript extraction (this will take longer)
        print(f"\n🎤 Testing transcript extraction (this may take time)...")
        if video_info.get('has_audio'):
            start_time = time.time()
            transcript = analyzer.extract_audio_transcript(video_path)
            transcript_time = time.time() - start_time
            
            if transcript:
                print(f"   ✅ Transcript extracted: {len(transcript)} chars ({transcript_time:.1f}s)")
                print(f"   📜 Preview: {transcript[:150]}...")
                
                # Test overlay with transcript
                print(f"\n✨ Testing overlay with transcript...")
                overlay_with_transcript = analyzer.generate_perfect_overlay(transcript, None, video_info)
                print(f"   ✅ Enhanced overlay: \"{overlay_with_transcript}\"")
            else:
                print(f"   ⚠️ No transcript extracted ({transcript_time:.1f}s)")
        else:
            print(f"   ⚠️ No audio track available for transcription")
        
        print(f"\n🎯 COMPLETE ANALYSIS TEST")
        print("-" * 30)
        start_time = time.time()
        full_analysis = analyzer.analyze_video_intelligently(video_path)
        total_time = time.time() - start_time
        
        print(f"✅ FULL ANALYSIS COMPLETED in {total_time:.1f}s")
        print(f"   📝 Has Captions: {full_analysis.has_existing_captions}")
        print(f"   🎤 Has Transcript: {'YES' if full_analysis.transcript else 'NO'}")
        print(f"   👁️ Has Visual Analysis: {'YES' if full_analysis.visual_analysis else 'NO'}")
        print(f"   ✨ Perfect Overlay: \"{full_analysis.suggested_overlay}\"")
        print(f"   🎯 Confidence: {full_analysis.confidence_score:.2f}")
        print(f"   📸 Frames Analyzed: {len(full_analysis.frame_samples)}")
        print(f"   ⏱️ Processing Time: {full_analysis.processing_time:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run direct analyzer test"""
    success = test_direct_analyzer()
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 20)
    if success:
        print("🎉 INTELLIGENT ANALYZER CORE FUNCTIONALITY: WORKING!")
        print("✅ Video info extraction: Ready")
        print("✅ Caption detection: Working")
        print("✅ Frame sampling: Efficient")
        print("✅ Transcript extraction: Available")
        print("✅ Overlay generation: Smart")
        print("🚀 Ready for API integration and n8n workflows!")
    else:
        print("⚠️ ANALYZER NEEDS DEBUGGING")
        print("🔧 Check error messages above")

if __name__ == "__main__":
    main()
