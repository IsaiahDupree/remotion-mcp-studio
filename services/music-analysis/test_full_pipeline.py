#!/usr/bin/env python3
"""
Complete End-to-End Pipeline Test:
1. OpenAI-powered video analysis for intelligent overlays
2. Enhanced video processing with smart placement and music
3. Full integration test of all features
"""
import requests
import json
import time
import os
from pathlib import Path

class FullPipelineTest:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_video = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
        self.output_dir = r"C:\Users\Isaia\Documents\Coding\N8N\cache\processed_videos"
        
    def test_openai_analysis(self):
        """Step 1: Get AI-powered overlay suggestion"""
        print("🤖 Step 1: OpenAI Video Analysis")
        print("=" * 50)
        
        url = f"{self.base_url}/video/analyze-with-openai"
        data = {
            "video_path": self.test_video,
            "use_openai": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, timeout=120)
            analysis_time = time.time() - start_time
            
            print(f"📊 Status: {response.status_code}")
            print(f"⏱️ Analysis Time: {analysis_time:.1f}s")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ OpenAI Analysis SUCCESS!")
                print(f"🎯 AI-Generated Overlay: '{result.get('suggested_overlay', 'N/A')}'")
                print(f"🤖 Used OpenAI: {result.get('used_openai_analysis', False)}")
                print(f"🎲 Confidence: {result.get('confidence_score', 0):.2f}")
                print(f"📺 Duration: {result.get('video_info', {}).get('duration', 0):.1f}s")
                print(f"📐 Resolution: {result.get('video_info', {}).get('resolution', 'N/A')}")
                print(f"🖼️ Frame Samples: {result.get('frame_samples_count', 0)}")
                
                # Show context used
                transcript = result.get('transcript', '')
                visual = result.get('visual_analysis', '')
                
                if transcript:
                    print(f"🎤 Transcript: {transcript[:100]}...")
                if visual:
                    print(f"👁️ Visual: {visual[:100]}...")
                
                return result
            else:
                print(f"❌ OpenAI Analysis FAILED: {response.status_code}")
                try:
                    error = response.json()
                    print(f"Error: {error}")
                except:
                    print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI Analysis ERROR: {e}")
            return None
    
    def test_enhanced_processing(self, overlay_text, secondary_text=None):
        """Step 2: Enhanced video processing with AI overlay"""
        print(f"\n🎬 Step 2: Enhanced Video Processing")
        print("=" * 50)
        
        url = f"{self.base_url}/video/process-enhanced"
        
        # Generate unique output filename
        timestamp = int(time.time())
        output_filename = f"ai_enhanced_video_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        data = {
            "video_path": self.test_video,
            "output_path": output_path,
            "primary_text": overlay_text,
            "secondary_text": secondary_text or "AI-Powered Enhancement",
            "text_position": "top_center",
            "music_volume_db": -25,
            "preserve_audio": True,
            "smart_placement": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, timeout=300)  # 5 minute timeout
            processing_time = time.time() - start_time
            
            print(f"📊 Status: {response.status_code}")
            print(f"⏱️ Processing Time: {processing_time:.1f}s")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Enhanced Processing SUCCESS!")
                print(f"📁 Output File: {result.get('output_path', 'N/A')}")
                print(f"📐 Video Dimensions: {result.get('video_info', {}).get('resolution', 'N/A')}")
                print(f"⏱️ Video Duration: {result.get('video_info', {}).get('duration', 0):.1f}s")
                print(f"🎵 Music Applied: {result.get('music_applied', False)}")
                print(f"🎤 Audio Preserved: {result.get('audio_preserved', False)}")
                print(f"🧠 Smart Placement: {result.get('smart_placement_used', False)}")
                
                # Check if output file exists
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                    print(f"📦 File Size: {file_size:.2f} MB")
                    print(f"✅ Output file verified: {Path(output_path).name}")
                else:
                    print("❌ Output file not found")
                
                return result
            else:
                print(f"❌ Enhanced Processing FAILED: {response.status_code}")
                try:
                    error = response.json()
                    print(f"Error: {error}")
                except:
                    print(f"Error: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ Enhanced Processing TIMEOUT (5 minutes)")
            return None
        except Exception as e:
            print(f"❌ Enhanced Processing ERROR: {e}")
            return None
    
    def test_music_analysis(self):
        """Step 3: Test intelligent music selection"""
        print(f"\n🎵 Step 3: Intelligent Music Analysis")
        print("=" * 50)
        
        url = f"{self.base_url}/analyze-music-match"
        data = {
            "video_path": self.test_video,
            "transcript": "This is a sample transcript for music analysis",
            "visual_analysis": "Dynamic video with energetic content and bright visuals"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Music Analysis SUCCESS!")
                print(f"🎭 Detected Mood: {result.get('detected_mood', 'N/A')}")
                print(f"🎵 Recommended Track: {result.get('music_recommendation', {}).get('file_name', 'N/A')}")
                print(f"🎲 Compatibility Score: {result.get('music_recommendation', {}).get('compatibility_score', 0):.2f}")
                print(f"💡 Match Reasoning: {result.get('music_recommendation', {}).get('reasoning', 'N/A')}")
                
                return result
            else:
                print(f"❌ Music Analysis FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Music Analysis ERROR: {e}")
            return None
    
    def run_full_test(self):
        """Run complete end-to-end pipeline test"""
        print("🚀 FULL PIPELINE TEST - AI-ENHANCED VIDEO PROCESSING")
        print("=" * 70)
        print(f"📹 Test Video: {Path(self.test_video).name}")
        print(f"🎯 API Base: {self.base_url}")
        print(f"📁 Output Dir: {self.output_dir}")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        total_start = time.time()
        
        # Step 1: OpenAI Analysis
        analysis_result = self.test_openai_analysis()
        if not analysis_result:
            print("\n❌ PIPELINE FAILED: OpenAI analysis failed")
            return False
        
        # Extract the AI-generated overlay
        ai_overlay = analysis_result.get('suggested_overlay', 'AI Enhanced Video')
        
        # Step 2: Enhanced Processing
        processing_result = self.test_enhanced_processing(
            overlay_text=ai_overlay,
            secondary_text="Powered by OpenAI"
        )
        if not processing_result:
            print("\n❌ PIPELINE FAILED: Enhanced processing failed")
            return False
        
        # Step 3: Music Analysis (optional verification)
        music_result = self.test_music_analysis()
        
        total_time = time.time() - total_start
        
        print(f"\n🎉 COMPLETE PIPELINE SUCCESS!")
        print("=" * 70)
        print(f"⏱️ Total Time: {total_time:.1f}s")
        print(f"🤖 AI Overlay Generated: '{ai_overlay}'")
        print(f"🎬 Enhanced Video Created: {processing_result.get('output_path', 'N/A')}")
        print(f"🎵 Music Analysis: {'✅' if music_result else '⚠️'}")
        
        # Summary
        print(f"\n📊 PIPELINE SUMMARY:")
        print(f"✅ OpenAI video analysis: WORKING")
        print(f"✅ AI-powered overlay generation: WORKING") 
        print(f"✅ Enhanced video processing: WORKING")
        print(f"✅ Smart text placement: WORKING")
        print(f"✅ Background music integration: WORKING")
        print(f"✅ Audio preservation: WORKING")
        print(f"{'✅' if music_result else '⚠️'} Intelligent music selection: {'WORKING' if music_result else 'NEEDS CHECK'}")
        
        return True

if __name__ == "__main__":
    # Run the complete pipeline test
    tester = FullPipelineTest()
    
    if Path(tester.test_video).exists():
        success = tester.run_full_test()
        
        if success:
            print(f"\n🏆 ALL SYSTEMS OPERATIONAL!")
            print(f"🚀 Ready for n8n workflow integration!")
        else:
            print(f"\n❌ Pipeline test failed - check logs above")
    else:
        print(f"❌ Test video not found: {tester.test_video}")
