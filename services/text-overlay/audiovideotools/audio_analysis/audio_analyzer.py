"""
Audio analyzer module for detecting and analyzing audio characteristics.

This module provides functions to:
1. Analyze audio volume metrics (RMS)
2. Detect background music in audio tracks
3. Calculate optimal background music volume levels
"""

import numpy as np
import scipy.fft
import logging
from typing import Dict, Any, Tuple, Optional, Union

# Set up logging
log = logging.getLogger('audio_analyzer')

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


def calculate_optimal_volume_db(
    audio_array: np.ndarray, 
    target_ratio: float = 0.15, 
    speech_emphasis: float = 0.7
) -> float:
    """
    Calculate optimal background music volume in dB based on audio characteristics.
    
    Args:
        audio_array: NumPy array containing audio samples
        target_ratio: Target ratio of background music volume to original audio volume
        speech_emphasis: Factor to make music even quieter to emphasize speech
        
    Returns:
        Optimal volume level in dB (negative value)
    """
    try:
        # Calculate original audio volume (RMS)
        original_volume = analyze_audio_volume(audio_array)
        
        log.info(f"Original audio volume metric (RMS): {original_volume:.6f}")
        
        # If original volume is very low, use a higher relative volume for music
        if original_volume < 0.01:
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
        
        return volume_db
        
    except Exception as e:
        log.error(f"Error calculating optimal volume: {e}")
        # Return a safe default value
        return -25.0
