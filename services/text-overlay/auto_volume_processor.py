#!/usr/bin/env python3
"""
Auto Volume Video Music Processor
--------------------------------
This script processes videos with background music,
automatically calculating the optimal volume level for
the background music based on analyzing the original video's audio.
"""

import os
import sys
import logging
import argparse
import numpy as np
import datetime
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import scipy.fft
from scipy import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("auto_volume_processor")

# Import required modules
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from utils.soundcloud_ytdlp import SoundCloudYtDlp


def analyze_audio_volume(audio_array: np.ndarray) -> float:
    """
    Analyze audio array to determine its volume characteristics.
    
    Args:
        audio_array: NumPy array containing audio samples
        
    Returns:
        Volume metric (RMS value)
    """
    # Calculate RMS (Root Mean Square) as volume metric
    # Square all samples, take mean, then square root
    if len(audio_array.shape) > 1:
        # Multi-channel audio (e.g. stereo) - average across channels
        rms_per_channel = [np.sqrt(np.mean(np.square(channel))) for channel in audio_array.T]
        rms = np.mean(rms_per_channel)
    else:
        # Mono audio
        rms = np.sqrt(np.mean(np.square(audio_array)))
        
    return float(rms)


def has_background_music(audio_array: np.ndarray, sample_rate: int) -> Tuple[bool, Dict[str, float]]:
    """
    Detect if audio already contains background music by analyzing audio features.
    
    Uses several heuristics to determine if music is present:
    1. Spectral flatness (music tends to have flatter spectrum than speech)
    2. Low frequency content (music usually has more bass than speech alone)
    3. Volume consistency (music tends to have more consistent volume over time)
    4. Spectral bandwidth (music often has wider frequency range)
    
    Args:
        audio_array: NumPy array containing audio samples
        sample_rate: Sample rate of the audio in Hz
    
    Returns:
        Tuple of (has_music_bool, metrics_dict)
    """
    metrics = {}
    
    # Convert to mono if stereo
    if len(audio_array.shape) > 1:
        audio_mono = np.mean(audio_array, axis=1)
    else:
        audio_mono = audio_array
    
    # Calculate metrics across multiple time windows
    window_size = min(int(sample_rate * 3), len(audio_mono) // 3)  # 3-second windows or smaller
    hop_size = window_size // 2
    
    spectral_flatness_values = []
    low_freq_ratios = []
    volume_variations = []
    
    # For each window
    for i in range(0, len(audio_mono) - window_size, hop_size):
        chunk = audio_mono[i:i+window_size]
        
        # 1. Calculate spectral flatness (music is "flatter" than speech)
        spec = np.abs(scipy.fft.rfft(chunk))
        spec = spec[1:] + 1e-10  # Avoid zeros and remove DC component
        spectral_flatness = np.exp(np.mean(np.log(spec))) / np.mean(spec)
        spectral_flatness_values.append(spectral_flatness)
        
        # 2. Calculate ratio of low frequency energy
        freq_resolution = sample_rate / window_size
        bass_range = int(300 / freq_resolution)  # 0-300Hz
        low_mid_range = int(2000 / freq_resolution)  # 0-2000Hz
        total_energy = np.sum(spec**2)
        if total_energy > 0:  # Avoid division by zero
            low_freq_ratio = np.sum(spec[:bass_range]**2) / total_energy
            low_mid_ratio = np.sum(spec[:low_mid_range]**2) / total_energy
            low_freq_ratios.append(low_freq_ratio)
            
        # 3. Calculate volume consistency
        # Split into sub-chunks and measure volume variation
        sub_chunks = np.array_split(chunk, 10)
        volumes = [np.sqrt(np.mean(np.square(sc))) for sc in sub_chunks]
        if np.mean(volumes) > 0:  # Avoid division by zero
            relative_variation = np.std(volumes) / np.mean(volumes)
            volume_variations.append(relative_variation)
    
    # Store all metrics for debugging and tuning
    metrics['spectral_flatness'] = np.mean(spectral_flatness_values) if spectral_flatness_values else 0
    metrics['low_freq_ratio'] = np.mean(low_freq_ratios) if low_freq_ratios else 0
    metrics['volume_variation'] = np.mean(volume_variations) if volume_variations else 1.0
    
    # Calculate additional metric: spectral contrast between bands
    # This helps identify music with pronounced bass/treble separation
    if len(spectral_flatness_values) > 0:
        # Calculate spectral centroid: weighted average of frequencies
        spec_full = np.abs(scipy.fft.rfft(audio_mono))
        freqs = np.fft.rfftfreq(len(audio_mono), 1/sample_rate)
        if np.sum(spec_full) > 0:  # Avoid division by zero
            centroid = np.sum(freqs * spec_full) / np.sum(spec_full)
            metrics['spectral_centroid'] = centroid
        else:
            metrics['spectral_centroid'] = 0
    else:
        metrics['spectral_centroid'] = 0
    
    # Calculate sustained volume ratio (music tends to have more sustained volume)
    if len(audio_mono) > sample_rate * 5:  # At least 5 seconds
        # Calculate percentage of time audio is above 25% of max volume
        audio_abs = np.abs(audio_mono)
        threshold = np.max(audio_abs) * 0.25
        sustained_ratio = np.sum(audio_abs > threshold) / len(audio_abs) 
        metrics['sustained_volume'] = sustained_ratio
    else:
        metrics['sustained_volume'] = 0
    
    # Music detection thresholds (refined based on empirical testing)
    # Music typically has higher spectral flatness, more low frequency content,
    # and more consistent volume (lower volume variation)
    
    # Logic for detecting background music we've added (specific pattern)
    likely_added_music = (metrics['spectral_flatness'] > 0.09 and 
                         metrics['low_freq_ratio'] > 0.35 and
                         metrics['volume_variation'] < 0.6)
    
    # General music detection
    general_music = (metrics['spectral_flatness'] > 0.04 and 
                   metrics['low_freq_ratio'] > 0.12 and 
                   metrics['volume_variation'] < 0.5)
    
    # High fidelity music usually has good spectral distribution and sustained volume
    high_quality_music = False
    if 'sustained_volume' in metrics and 'spectral_centroid' in metrics:
        high_quality_music = (metrics['spectral_centroid'] > 1000 and
                            metrics['sustained_volume'] > 0.3 and
                            metrics['spectral_flatness'] > 0.035)
    
    # Combine detection methods
    has_music = likely_added_music or general_music or high_quality_music
    
    # Override for very clear speech patterns
    if metrics['spectral_flatness'] < 0.02 or metrics['volume_variation'] > 0.85:
        has_music = False
        
    return has_music, metrics


def calculate_optimal_volume_db(video_path: str, target_ratio: float = 0.15, speech_emphasis: float = 0.7) -> float:
    """
    Calculate optimal background music volume in dB based on video's audio.
    
    Args:
        video_path: Path to the video file
        target_ratio: Target ratio of music volume to original audio volume (0-1)
            Lower values = quieter background music
    
    Returns:
        Recommended volume level in dB
    """
    log.info(f"Analyzing audio volume for: {os.path.basename(video_path)}")
    
    try:
        # Load video and extract audio
        video = VideoFileClip(video_path)
        
        if video.audio is None:
            log.warning("Video has no audio. Using default volume of -40 dB")
            return -40.0
        
        # Get audio as numpy array
        audio_array = video.audio.to_soundarray()
        
        # Calculate volume metric (RMS)
        original_volume = analyze_audio_volume(audio_array)
        log.info(f"Original audio volume metric (RMS): {original_volume:.6f}")
        
        # If original volume is very low, use a higher relative volume for music
        if original_volume < 0.01:
            # Original audio is very quiet, using lower reduction for music
            # But still keep it relatively quiet to ensure any speech is audible
            target_ratio = 0.3  # Less reduction for quiet videos
        elif original_volume > 0.3:
            log.info("Original audio is quite loud, using more reduction for music")
            target_ratio = 0.1  # More reduction for loud videos
            
        # Calculate desired music volume
        target_volume = original_volume * target_ratio
        
        # Apply speech emphasis factor to make music even quieter than calculated
        # This helps ensure speech/words are clearly audible
        target_volume *= speech_emphasis
        
        # Convert to dB: dB = 20 * log10(amplitude_ratio)
        # Since we want target_volume/1.0, the ratio is just target_ratio*speech_emphasis
        volume_db = 20 * np.log10(target_ratio * speech_emphasis)
        
        log.info(f"Calculated optimal volume: {volume_db:.2f} dB")
        
        # Limit to reasonable range, but use a lower upper bound (-20 dB instead of -15 dB)
        # to ensure the background music doesn't overpower speech
        volume_db = max(-50, min(-20, volume_db))
        
        # Close to free resources
        video.close()
        
        return volume_db
        
    except Exception as e:
        log.error(f"Error analyzing audio: {e}")
        log.warning("Using default volume of -40 dB")
        return -40.0


def process_video_with_auto_volume(
    video_path: str, 
    music_path: str,
    output_path: str,
    target_ratio: float = 0.15,
    speech_emphasis: float = 0.7,
    force_add_music: bool = False,
    skip_existing_music: bool = True,
    overwrite: bool = False
) -> bool:
    """
    Process a video by adding background music with automatically calculated volume.
    
    Args:
        video_path: Path to input video file
        music_path: Path to music file
        output_path: Path to save the processed video
        target_ratio: Target ratio of music volume to original audio (0-1)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        log.info(f"Processing video: {os.path.basename(video_path)}")
        
        # Check if output file already exists and handle accordingly
        if os.path.exists(output_path) and not overwrite:
            log.warning(f"Output file already exists: {output_path}")
            log.info(f"Generating new unique filename to avoid conflicts...")
            
            # Generate new unique filename with timestamp
            dirname = os.path.dirname(output_path)
            basename = os.path.basename(output_path)
            name, ext = os.path.splitext(basename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(dirname, f"{name}_{timestamp}{ext}")
            log.info(f"New output path: {output_path}")
            
        # Load video
        video = VideoFileClip(video_path)
        
        # Check if video already has background music if requested
        if skip_existing_music and video.audio is not None:
            log.info("Checking if video already has background music...")
            audio_array = video.audio.to_soundarray()
            sample_rate = video.audio.fps
            
            has_music, metrics = has_background_music(audio_array, sample_rate)
            
            if has_music and not force_add_music:
                log.info("Video appears to already have background music. Skipping.")
                log.info(f"Music detection metrics: {metrics}")
                return False
            elif has_music:
                log.info("Video appears to have background music, but force_add_music=True. Proceeding.")
                log.info(f"Music detection metrics: {metrics}")
            else:
                log.info("No background music detected in original video.")
                log.info(f"Music detection metrics: {metrics}")
        
        log.info(f"Adding music: {os.path.basename(music_path)}")        
        # Calculate optimal volume level with speech emphasis
        volume_db = calculate_optimal_volume_db(video_path, target_ratio, speech_emphasis)
        log.info(f"Using calculated volume level: {volume_db:.2f} dB")
        
        # Load music
        music = AudioFileClip(music_path)
        
        # Prepare the music: loop or trim as needed
        if music.duration < video.duration:
            # If music is shorter than video, loop it
            log.info(f"Looping music to match video duration ({video.duration:.2f}s)")
            music = music.loop(duration=video.duration)
        else:
            # If music is longer than video, trim it
            log.info(f"Trimming music to match video duration ({video.duration:.2f}s)")
            music = music.subclip(0, video.duration)
        
        # Set volume level (convert dB to amplitude ratio)
        # Formula: amplitude ratio = 10^(dB/20)
        volume_factor = 10 ** (volume_db / 20)
        log.info(f"Setting music volume to {volume_db:.2f} dB (factor: {volume_factor:.4f})")
        music = music.volumex(volume_factor)
        
        # Combine with original audio if present
        if video.audio is not None:
            log.info("Mixing music with original audio")
            final_audio = CompositeAudioClip([video.audio, music])
            video = video.set_audio(final_audio)
        else:
            log.info("No original audio present, using music only")
            video = video.set_audio(music)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Render the video
        log.info(f"Writing output video to: {output_path}")
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4
        )
        
        log.info(f"Successfully processed video: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        log.error(f"Error processing video: {e}")
        return False
    finally:
        # Close clips to free resources
        try:
            if 'video' in locals():
                video.close()
            if 'music' in locals():
                music.close()
        except Exception:
            pass


def process_videos_batch(
    video_dir: str,
    music_files: List[str],
    output_dir: str,
    target_ratio: float = 0.15,
    speech_emphasis: float = 0.7,
    force_add_music: bool = False,
    skip_existing_music: bool = True,
    overwrite: bool = False,
    limit: Optional[int] = None,
    specific_video: Optional[str] = None
) -> int:
    """
    Process a batch of videos with auto-volume background music.
    
    Args:
        video_dir: Directory containing input videos
        music_files: List of music files to use
        output_dir: Directory to save processed videos
        target_ratio: Target ratio for music volume calculation
        limit: Maximum number of videos to process
        specific_video: Optional filename to process only a specific video
        
    Returns:
        Number of successfully processed videos
    """
    if not music_files:
        log.error("No music files available")
        return 0
    
    log.info(f"Processing videos from: {video_dir}")
    log.info(f"Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
    video_files = []
    
    # If specific video is requested
    if specific_video:
        specific_path = os.path.join(video_dir, specific_video)
        if os.path.exists(specific_path):
            video_files = [specific_path]
            log.info(f"Processing specific video: {specific_video}")
        else:
            log.error(f"Specified video not found: {specific_video}")
            return 0
    else:
        # Find all video files
        for root, _, files in os.walk(video_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
    
    if not video_files:
        log.error(f"No video files found in {video_dir}")
        return 0
    
    # Sort videos by name
    video_files.sort()
    
    # Limit the number of videos to process if specified
    if limit and limit > 0:
        video_files = video_files[:limit]
    
    log.info(f"Found {len(video_files)} videos to process")
    log.info(f"Using {len(music_files)} music tracks")
    
    # Process each video with a music track
    success_count = 0
    for i, video_path in enumerate(video_files):
        # Select a music file (rotating through available music)
        music_path = music_files[i % len(music_files)]
        
        # Define output path
        video_name = os.path.basename(video_path)
        timestamp = int(time.time())
        basename, ext = os.path.splitext(video_name)
        output_path = os.path.join(
            output_dir,
            f"autovolume_{basename}_{timestamp}{ext}"
        )
        
        log.info(f"Processing video {i+1}/{len(video_files)}: {video_name}")
        
        # Process the video with auto-calculated volume and speech emphasis
        if process_video_with_auto_volume(video_path, music_path, output_path, target_ratio, speech_emphasis, 
                                         force_add_music, skip_existing_music, overwrite):
            success_count += 1
        else:
            log.info(f"Skipping video {video_name} (likely already has music or permission error)")
    
    if success_count == 0:
        if len(video_files) == 0:
            log.error("❌ Processing failed. No valid videos found to process.")
            return 0
        else:
            # All videos were skipped because they already have music - this is not an error
            skipped_count = len(video_files)
            log.info(f"ℹ️ All {skipped_count} videos were skipped (likely already have music).")
            return 0
    else:
        log.info(f"✅ Successfully processed {success_count} out of {len(video_files)} videos with auto-volume music.")
        return success_count


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process videos with SoundCloud music using automatic volume calculation"
    )
    parser.add_argument(
        "--video-dir",
        default="C:\\Users\\Isaia\\Documents\\Coding\\N8N\\shared\\videos",
        help="Directory containing input videos"
    )
    parser.add_argument(
        "--output-dir",
        default="C:\\Users\\Isaia\\Documents\\WordsOnText\\output_videos",
        help="Directory for output videos"
    )
    parser.add_argument(
        "--music-dir",
        default="C:\\Users\\Isaia\\Documents\\WordsOnText\\downloaded_songs",
        help="Directory with music files"
    )
    parser.add_argument(
        "--target-ratio",
        type=float,
        default=0.15,
        help="Target ratio of music to original audio volume (0-1)"
    )
    parser.add_argument(
        "--speech-emphasis",
        type=float,
        default=0.7,
        help="Factor to make music even quieter to emphasize speech (0-1)"
    )
    parser.add_argument(
        "--specific-video",
        help="Specific video filename to process (must be in video-dir)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of videos to process"
    )
    parser.add_argument(
        "--force-add-music",
        action="store_true",
        help="Force adding music even if video already has background music"
    )
    parser.add_argument(
        "--disable-music-check",
        action="store_true",
        help="Disable background music detection check"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    args = parser.parse_args()
    
    # Get existing music files
    music_dir = args.music_dir
    music_files = []
    
    if os.path.exists(music_dir):
        music_files = [
            os.path.join(music_dir, f) for f in os.listdir(music_dir)
            if f.lower().endswith(('.mp3', '.m4a', '.wav'))
        ]
        log.info(f"Found {len(music_files)} music files in {music_dir}")
    
    if not music_files:
        log.error("No music files found. Please download some tracks first.")
        log.info("You can use the utils/soundcloud_ytdlp.py module to download tracks.")
        return 1
    
    # Process videos with auto-volume music
    success_count = process_videos_batch(
        args.video_dir,
        music_files,
        args.output_dir,
        args.target_ratio,
        args.speech_emphasis,
        args.force_add_music,
        not args.disable_music_check,  # Skip existing music unless disabled
        args.overwrite,
        args.limit,
        args.specific_video
    )
    
    # Return appropriate exit code based on results
    if success_count == 0 and not os.path.exists(args.video_dir):
        # No video directory exists
        log.error(f"❌ Video directory not found: {args.video_dir}")
        sys.exit(1)
    else:
        # Success (even if all videos were skipped due to already having music)
        sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
