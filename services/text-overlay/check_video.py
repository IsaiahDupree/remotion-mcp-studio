"""
Quick script to check if a video has background music and analyze its content
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import librosa
import cv2

# Import our modules
from video_context_analyzer.audio_analysis import AudioAnalyzer
from video_context_analyzer.frame_analysis import FrameAnalyzer

def manual_check_for_background_music(audio_file):
    """
    Manual check for background music using audio features.
    This is a simplified version of the detection logic.
    """
    try:
        # Load audio
        print(f"Loading audio from {audio_file}...")
        y, sr = librosa.load(audio_file, sr=None)
        
        # Calculate some features
        print("Calculating audio features...")
        
        # Spectral flatness (high for noise/music, low for speech)
        spectral_flatness = np.mean(librosa.feature.spectral_flatness(y=y))
        
        # Zero crossing rate (high for music/noise)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=y))
        
        # RMS energy and its stability
        rms = librosa.feature.rms(y=y)[0]
        rms_std = np.std(rms)
        rms_mean = np.mean(rms)
        rms_var = rms_std / (rms_mean + 0.00001)  # Avoid division by zero
        
        # Simple heuristic thresholds
        has_music = False
        confidence = 0.0
        
        if spectral_flatness > 0.04 and rms_var < 0.7:
            has_music = True
            confidence = min(0.5 + spectral_flatness * 5, 1.0)
        
        print(f"Spectral flatness: {spectral_flatness:.6f}")
        print(f"Zero crossing rate: {zcr:.6f}")
        print(f"RMS variation: {rms_var:.6f}")
        print(f"Background music detected: {has_music} (confidence: {confidence:.2f})")
        
        return has_music, {
            "spectral_flatness": float(spectral_flatness),
            "zero_crossing_rate": float(zcr), 
            "rms_variation": float(rms_var),
            "confidence": float(confidence)
        }
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return False, {}

def check_for_text_overlay(video_path, frames=10):
    """
    Check if a video already has text overlays by sampling frames.
    Uses OCR-like features to detect text regions.
    """
    try:
        print(f"Checking for existing text overlays in {video_path}...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video: {video_path}")
            return False, {}
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps
        
        # Sample frames at regular intervals
        has_text_overlay = False
        frames_with_text = 0
        text_regions = []
        
        # Step size for sampling frames
        step = max(1, total_frames // frames)
        
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use edge detection and contour finding to identify potential text regions
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours to find text-like regions
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / (h + 0.01)  # Avoid division by zero
                
                # Text regions usually have specific aspect ratio and size
                if 2 < aspect_ratio < 15 and 20 < w < 300 and 10 < h < 100:
                    text_regions.append((x, y, w, h))
                    frames_with_text += 1
                    has_text_overlay = True
                    break  # Found text in this frame
        
        cap.release()
        
        # Calculate percentage of frames with text
        text_percentage = (frames_with_text / frames) * 100 if frames > 0 else 0
        print(f"Frames with text overlay: {frames_with_text} out of {frames} sampled frames ({text_percentage:.1f}%)")
        print(f"Text overlay detected: {has_text_overlay}")
        
        return has_text_overlay, {
            "frames_with_text": frames_with_text,
            "frames_sampled": frames,
            "text_percentage": float(text_percentage)
        }
    except Exception as e:
        print(f"Error analyzing frames: {e}")
        return False, {}

def analyze_video(video_path):
    """Analyze video for background music, text overlays and content"""
    print(f"\n=== Analyzing video: {video_path} ===")
    results = {
        "video_path": video_path,
        "filename": Path(video_path).name
    }
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        return None
    
    # Extract audio for manual analysis
    try:
        audio_file = os.path.join(os.path.dirname(video_path), 
                                 f"{Path(video_path).stem}_audio.wav")
        
        # Skip extracting audio if file exists already
        if not os.path.exists(audio_file):
            print(f"Extracting audio to {audio_file}...")
            os.system(f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_file}" -y')
            time.sleep(1)  # Wait for file to be created
        
        # Manually check for background music
        has_music, audio_features = manual_check_for_background_music(audio_file)
        results["manual_music_check"] = {
            "has_background_music": has_music,
            **audio_features
        }
    except Exception as e:
        print(f"Error extracting audio: {e}")
    
    # Check for existing text overlays
    has_text, text_features = check_for_text_overlay(video_path)
    results["text_overlay_check"] = {
        "has_text_overlay": has_text,
        **text_features
    }
    
    # Run audio analyzer
    try:
        audio_analyzer = AudioAnalyzer()
        print("\nRunning audio analysis module...")
        audio_result = audio_analyzer.analyze_video_audio(video_path)
        results["audio_analysis"] = audio_result
        
        has_music_from_module = audio_result.get("has_background_music", False)
        print(f"Module detected background music: {has_music_from_module}")
        
        # Check for transcript
        if "transcription" in audio_result and audio_result["transcription"]:
            transcript = audio_result["transcription"]
            print(f"Transcript excerpt: {transcript[:100]}...")
            results["has_transcript"] = True
        else:
            print("No transcript available")
            results["has_transcript"] = False
    except Exception as e:
        print(f"Error in audio analysis module: {e}")
    
    # Result summary
    need_music = not has_music
    need_text = not has_text
    
    print("\n=== Summary ===")
    print(f"Video needs background music: {need_music}")
    print(f"Video needs text overlay: {need_text}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Default video to test
        video_path = r"C:\Users\Isaia\Documents\WordsOnText\output_videos\autovolume_0024d0ff50d04b2eba719fec130a0b74.mp4"
    
    results = analyze_video(video_path)
    
    # Save results
    if results:
        results_file = os.path.join(os.path.dirname(video_path), 
                                   f"{Path(video_path).stem}_analysis.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {results_file}")
        
        if not results.get("manual_music_check", {}).get("has_background_music", False) and \
           not results.get("text_overlay_check", {}).get("has_text_overlay", False):
            print("\nThis video has no background music or text overlays.")
            print("It's a good candidate for enhancement!")
