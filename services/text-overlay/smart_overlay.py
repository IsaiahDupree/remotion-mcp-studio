#!/usr/bin/env python3
"""
Smart Text-on-Video Overlay Tool
--------------------------------
Automatically places context-aware text on videos by analyzing transcript,
visual content, and user prompts.
"""

import argparse
import base64
import csv
import datetime
import glob
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

from PIL import Image

import cv2
import numpy as np
import torch
import yaml
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from openai import OpenAI
from pydantic import BaseModel, Field
from rich.console import Console
from rich.logging import RichHandler
from slugify import slugify
from ultralytics import YOLO

# Set up rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
log = logging.getLogger("smart_overlay")

# Font presets
FONT_PRESETS = {
    "TechMeStuff": {
        "font": "./fonts/Inter-Bold.ttf",
        "color": "white",
        "stroke_width": 2,
        "stroke_color": "black",
    },
    "Minimalist": {
        "font": "./fonts/Roboto-Light.ttf",
        "color": "white",
        "stroke_width": 1,
        "stroke_color": "black",
    },
    "Dramatic": {
        "font": "./fonts/Montserrat-ExtraBold.ttf",
        "color": "white",
        "stroke_width": 3,
        "stroke_color": "black",
    },
    "Professional": {
        "font": "./fonts/OpenSans-SemiBold.ttf",
        "color": "white",
        "stroke_width": 2,
        "stroke_color": "black",
    },
}

# Configuration model
class Config(BaseModel):
    video: Dict[str, Any] = Field(default_factory=dict)
    overlay: Dict[str, Any] = Field(default_factory=dict)
    models: Dict[str, str] = Field(default_factory=dict)
    weights: Dict[str, float] = Field(default_factory=dict)
    sampling: Dict[str, int] = Field(default_factory=dict)
    thresholds: Dict[str, float] = Field(default_factory=dict)

# Global variables
config = None
client = None
yolo_model = None
clip_model = None
clip_preprocess = None
webhook_notifier = None
gpu_config = None


def load_config(config_path: str) -> Config:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return Config(**config_dict)
    except Exception as e:
        log.error(f"Failed to load config: {e}")
        sys.exit(1)


def setup_openai_client(api_key: str) -> OpenAI:
    """Initialize the OpenAI client."""
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        log.error(f"Failed to initialize OpenAI client: {e}")
        sys.exit(1)


def setup_models():
    """Load and initialize all required models."""
    global yolo_model, clip_model, clip_preprocess, gpu_config
    
    # Setup GPU acceleration if available
    try:
        from utils.gpu_utils import setup_gpu_acceleration
        gpu_config = setup_gpu_acceleration(config.dict() if hasattr(config, 'dict') else None)
        device = gpu_config["device"]
    except ImportError:
        log.warning("GPU utilities not found, using CPU only")
        device = "cpu"
        gpu_config = {"use_gpu": False, "device": "cpu"}
    
    # Load YOLO model for object detection
    try:
        log.info(f"Loading YOLO model: {config.models['yolo_model']} on {device}")
        yolo_model = YOLO(config.models['yolo_model'])
        if gpu_config["use_gpu"]:
            # Configure YOLO to use GPU
            yolo_model.to(device)
    except Exception as e:
        log.error(f"Failed to load YOLO model: {e}")
        sys.exit(1)
    
    # Load CLIP model for visual embeddings
    try:
        log.info(f"Loading CLIP model: {config.models['clip_model']} on {device}")
        import clip
        clip_model, clip_preprocess = clip.load(config.models['clip_model'], device=device)
        
        # Use half precision if configured
        if gpu_config.get("half_precision", False) and device != "cpu":
            clip_model = clip_model.half()
            log.info("Using half precision for CLIP model")
    except Exception as e:
        log.error(f"Failed to load CLIP model: {e}")
        sys.exit(1)


def get_transcript(video_path: str) -> List[Dict[str, Any]]:
    """Extract transcript from video using Whisper API."""
    log.info(f"Extracting transcript from {video_path}")
    try:
        # Use OpenAI Whisper API for transcription
        with open(video_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json"
            )
        
        # Extract segments with timestamps
        segments = transcript.segments
        log.info(f"Extracted {len(segments)} transcript segments")
        return segments
    except Exception as e:
        log.error(f"Failed to extract transcript: {e}")
        return []


def get_transcript_context(transcript: List[Dict[str, Any]]) -> str:
    """Extract the middle 50% of the transcript for context."""
    if not transcript:
        return ""
    
    # Calculate start and end indices for middle 50%
    total_segments = len(transcript)
    start_idx = total_segments // 4
    end_idx = start_idx + (total_segments // 2)
    
    # Extract and join the text from the middle segments
    middle_segments = transcript[start_idx:end_idx]
    context_text = " ".join([segment.get('text', '') for segment in middle_segments])
    
    log.info(f"Extracted {len(middle_segments)} segments for transcript context")
    return context_text


def sample_frames(video_path: str, duration: float) -> List[np.ndarray]:
    """Sample frames from the video at specified intervals."""
    log.info(f"Sampling frames from {video_path}")
    frames = []
    
    # Determine sampling rate based on video duration
    sample_interval = config.sampling['short_interval_sec'] if duration < 900 else config.sampling['long_interval_sec']
    
    try:
        # Open video file
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame indices to sample
        frame_interval = int(fps * sample_interval)
        sample_indices = range(0, total_frames, frame_interval)
        
        for frame_idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
        
        cap.release()
        log.info(f"Sampled {len(frames)} frames at {sample_interval}s intervals")
        return frames
    except Exception as e:
        log.error(f"Failed to sample frames: {e}")
        return []


def get_frame_captions(frames: List[np.ndarray], top_n: int = 5) -> List[str]:
    """Generate captions for the sampled frames using CLIP and GPT."""
    log.info(f"Generating captions for {len(frames)} frames")
    captions = []
    
    try:
        # Prepare frames for CLIP
        processed_images = torch.stack([clip_preprocess(Image.fromarray(frame)) for frame in frames])
        
        # Get image features
        with torch.no_grad():
            image_features = clip_model.encode_image(processed_images)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        
        # For each frame, get a caption using GPT-4o
        for i, frame in enumerate(frames[:top_n]):  # Limit to top_n frames
            # Convert numpy array to base64 for API
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            base64_image = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
            
            # Get caption from GPT-4o
            response = client.chat.completions.create(
                model=config.models['gpt_model'],
                messages=[
                    {"role": "system", "content": "You are a visual description assistant. Describe the key elements in this image in a single concise sentence."},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": base64_image}}]}
                ],
                max_tokens=100
            )
            
            caption = response.choices[0].message.content.strip()
            captions.append(caption)
            
            log.info(f"Frame {i+1}/{top_n} caption: {caption}")
    
    except Exception as e:
        log.error(f"Failed to generate frame captions: {e}")
    
    return captions


def generate_overlay_text(prompt: str, transcript_context: str, frame_captions: List[str]) -> str:
    """Generate the final overlay text using GPT-4o."""
    log.info("Generating overlay text")
    
    try:
        # Prepare the prompt for GPT-4o
        system_prompt = (
            "You are an expert content creator specializing in video captions. "
            "Craft one concise, punchy text (≤ 90 chars) that unites the three inputs below. "
            "The text should be attention-grabbing and relevant to the video content. "
            "Do not use quotes or hashtags in your response. Just return the text."
        )
        
        user_prompt = f"""PROMPT (40% weight): {prompt}

TRANSCRIPT CONTEXT (30% weight): {transcript_context}

VISUAL CONTEXT (30% weight): {'; '.join(frame_captions)}

Create a single line of compelling text that combines these elements."""
        
        # Call GPT-4o
        response = client.chat.completions.create(
            model=config.models['gpt_model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        overlay_text = response.choices[0].message.content.strip()
        
        # Ensure text is not too long
        if len(overlay_text) > 90:
            overlay_text = overlay_text[:87] + "..."
            
        log.info(f"Generated overlay text: {overlay_text}")
        return overlay_text
    
    except Exception as e:
        log.error(f"Failed to generate overlay text: {e}")
        return prompt  # Fallback to the original prompt


def detect_faces_and_objects(frame: np.ndarray) -> np.ndarray:
    """Detect faces and UI elements in the frame to create a mask of areas to avoid."""
    log.info("Detecting faces and UI elements")
    
    try:
        # Create a mask (0 = avoid, 1 = available)
        mask = np.ones(frame.shape[:2], dtype=np.float32)
        
        # Face detection using mediapipe
        import mediapipe as mp
        mp_face_detection = mp.solutions.face_detection
        
        with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(frame_rgb)
            
            if results.detections:
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    h, w = frame.shape[:2]
                    x, y = int(bbox.xmin * w), int(bbox.ymin * h)
                    width, height = int(bbox.width * w), int(bbox.height * h)
                    
                    # Add padding around face
                    padding = int(min(width, height) * 0.2)
                    x_start = max(0, x - padding)
                    y_start = max(0, y - padding)
                    x_end = min(w, x + width + padding)
                    y_end = min(h, y + height + padding)
                    
                    # Mark face region as 0 (avoid)
                    mask[y_start:y_end, x_start:x_end] = 0
        
        # Object detection using YOLO
        # Focus on UI elements like buttons, icons, text boxes
        results = yolo_model(frame)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get class and confidence
                cls_id = int(box.cls.item())
                conf = box.conf.item()
                
                # Filter for UI elements (screens, buttons, etc.)
                # Class IDs depend on the YOLO model used
                ui_classes = [62, 63, 66, 67, 73]  # tv, laptop, keyboard, cell phone, book
                
                if cls_id in ui_classes and conf > 0.5:
                    # Get bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    # Mark UI region as 0 (avoid)
                    mask[y1:y2, x1:x2] = 0
        
        return mask
    
    except Exception as e:
        log.error(f"Failed to detect faces and objects: {e}")
        return np.ones(frame.shape[:2], dtype=np.float32)  # Return all ones if detection fails


def create_saliency_mask(frame: np.ndarray) -> np.ndarray:
    """Create a saliency mask to identify visually important regions."""
    log.info("Creating saliency mask")
    
    try:
        # Use OpenCV's saliency detection
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
        success, saliency_map = saliency.computeSaliency(frame)
        
        if success:
            # Normalize to 0-1 range
            saliency_map = (saliency_map * 255).astype(np.uint8)
            # Invert saliency map (0 = salient, 1 = not salient)
            saliency_mask = 1 - (saliency_map / 255.0)
            return saliency_mask
        else:
            log.warning("Saliency detection failed, using fallback")
            return np.ones(frame.shape[:2], dtype=np.float32)  # Fallback
    
    except Exception as e:
        log.error(f"Failed to create saliency mask: {e}")
        return np.ones(frame.shape[:2], dtype=np.float32)  # Fallback


def create_safe_zones_mask(frame: np.ndarray) -> np.ndarray:
    """Create a mask for safe zones based on rules (edges, caption area)."""
    log.info("Creating safe zones mask")
    
    try:
        h, w = frame.shape[:2]
        mask = np.ones((h, w), dtype=np.float32)
        
        # Avoid edges (32px margin)
        edge_margin = 32
        mask[:edge_margin, :] = 0  # Top margin
        mask[-edge_margin:, :] = 0  # Bottom margin
        mask[:, :edge_margin] = 0  # Left margin
        mask[:, -edge_margin:] = 0  # Right margin
        
        # Avoid caption area (bottom 15%)
        caption_height = int(h * config.video['safe_caption_height_pct'] / 100)
        mask[-caption_height:, :] = 0
        
        return mask
    
    except Exception as e:
        log.error(f"Failed to create safe zones mask: {e}")
        return np.ones(frame.shape[:2], dtype=np.float32)  # Fallback


def find_text_placement(frame: np.ndarray, text: str, font_size: int) -> Tuple[int, int]:
    """Find the optimal placement for text overlay using heat-map algorithm."""
    log.info("Finding optimal text placement")
    
    try:
        # Create masks
        face_object_mask = detect_faces_and_objects(frame)
        saliency_mask = create_saliency_mask(frame)
        safe_zones_mask = create_safe_zones_mask(frame)
        
        # Combine masks with weights
        combined_mask = (
            face_object_mask * 0.4 +
            saliency_mask * 0.4 +
            safe_zones_mask * 0.2
        )
        
        # Normalize to 0-1
        combined_mask = combined_mask / combined_mask.max()
        
        # Estimate text dimensions
        # This is a rough estimate, actual dimensions depend on the font
        chars_per_line = len(text)
        text_width = int(chars_per_line * font_size * 0.6)  # Approximate width
        text_height = int(font_size * 1.5)  # Approximate height
        
        h, w = frame.shape[:2]
        
        # Find regions large enough for text
        valid_regions = []
        
        # Use sliding window approach
        for y in range(0, h - text_height, 10):  # Step by 10 pixels for efficiency
            for x in range(0, w - text_width, 10):
                region = combined_mask[y:y+text_height, x:x+text_width]
                if region.mean() > 0.7:  # If region is mostly available
                    # Calculate distance from vertical center (prefer center placement)
                    center_dist = abs((y + text_height/2) - h/2) / (h/2)  # Normalized 0-1
                    score = region.mean() * (1 - center_dist * 0.5)  # Weigh by center proximity
                    valid_regions.append((x, y, score))
        
        if valid_regions:
            # Sort by score (highest first)
            valid_regions.sort(key=lambda r: r[2], reverse=True)
            best_x, best_y, _ = valid_regions[0]
            log.info(f"Found optimal text placement at ({best_x}, {best_y})")
            return best_x, best_y
        else:
            # Fallback to top-center if no good region found
            log.warning("No optimal placement found, using fallback position")
            return (w - text_width) // 2, edge_margin + 10
    
    except Exception as e:
        log.error(f"Failed to find text placement: {e}")
        # Fallback to top-center
        return (frame.shape[1] // 2) - 200, 50


def render_video_with_text(video_path: str, output_path: str, overlay_text: str, 
                          font_preset: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Render the video with text overlay at the optimal position."""
    log.info(f"Rendering video with text overlay: {overlay_text}")
    
    try:
        # Load video
        video = VideoFileClip(video_path)
        
        # Sample a frame for placement calculation
        frame_time = video.duration / 2  # Middle of video
        frame = video.get_frame(frame_time)
        
        # Determine font size based on video resolution
        video_width = video.w
        min_font_size = config.video['min_font_size']
        max_font_size = config.video['max_font_size']
        
        # Scale font size with video width
        font_size = min(max(int(video_width / 30), min_font_size), max_font_size)
        
        # Find optimal text placement
        x, y = find_text_placement(frame, overlay_text, font_size)
        
        # Create text clip
        text_clip = TextClip(
            overlay_text,
            fontsize=font_size,
            font=font_preset['font'],
            color=font_preset['color'],
            stroke_color=font_preset['stroke_color'],
            stroke_width=font_preset['stroke_width'],
            method='caption'
        )
        
        # Set position and add fade-in
        text_clip = text_clip.set_position((x, y))
        text_clip = text_clip.set_start(0)
        text_clip = text_clip.set_duration(video.duration)
        text_clip = text_clip.crossfadein(config.video['fade_in_sec'])
        
        # Composite video with text
        final_clip = CompositeVideoClip([video, text_clip])
        
        # Get optimal ffmpeg args based on GPU configuration
        ffmpeg_args = {}
        if gpu_config and gpu_config.get("use_gpu", False):
            try:
                from utils.gpu_utils import get_optimal_ffmpeg_args
                ffmpeg_args = get_optimal_ffmpeg_args(gpu_config)
                log.info(f"Using optimized encoding settings: {ffmpeg_args}")
            except ImportError:
                log.warning("GPU utilities not found, using default encoding settings")
                ffmpeg_args = {"codec": "libx264", "audio_codec": "aac"}
        else:
            ffmpeg_args = {"codec": "libx264", "audio_codec": "aac"}
        
        # Write to file with optimized settings
        final_clip.write_videofile(
            output_path,
            codec=ffmpeg_args.get("codec", "libx264"),
            audio_codec=ffmpeg_args.get("audio_codec", "aac"),
            preset=ffmpeg_args.get("preset", "medium"),
            threads=ffmpeg_args.get("threads", None),
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            **(ffmpeg_args.get("extra_args", {}))
        )
        
        # Close clips
        text_clip.close()
        video.close()
        final_clip.close()
        
        # Return metadata
        metadata = {
            "overlay_text": overlay_text,
            "position_x": x,
            "position_y": y,
            "font_style": font_preset['font'],
            "start_sec": 0,
            "duration": video.duration
        }
        
        log.info(f"Successfully rendered video to {output_path}")
        return True, metadata
    
    except Exception as e:
        log.error(f"Failed to render video: {e}")
        return False, {}


def process_video(video_path: str, output_dir: str, prompt: str, font_preset: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single video with the smart overlay pipeline."""
    log.info(f"Processing video: {video_path}")
    
    try:
        # Get video duration
        video = VideoFileClip(video_path)
        duration = video.duration
        video.close()
        
        # Step 1: Get transcript
        transcript = get_transcript(video_path)
        
        # Step 2: Get transcript context
        transcript_context = get_transcript_context(transcript)
        
        # Step 3: Sample frames
        frames = sample_frames(video_path, duration)
        
        # Step 4: Get frame captions
        frame_captions = get_frame_captions(frames)
        
        # Step 5: Generate overlay text
        overlay_text = generate_overlay_text(prompt, transcript_context, frame_captions)
        
        # Create output filename
        video_basename = os.path.basename(video_path)
        video_name, video_ext = os.path.splitext(video_basename)
        prompt_slug = slugify(prompt)[:30]  # Limit slug length
        output_filename = f"{prompt_slug}_{video_name}{video_ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Step 6: Render video with text
        success, metadata = render_video_with_text(video_path, output_path, overlay_text, font_preset)
        
        if success:
            # Add additional metadata
            metadata.update({
                "original_name": video_basename,
                "new_name": output_filename,
                "prompt": prompt
            })
            return metadata
        else:
            log.error(f"Failed to process video: {video_path}")
            return {}
    
    except Exception as e:
        log.error(f"Error processing video {video_path}: {e}")
        return {}


def process_batch(input_dir: str, output_base_dir: str, prompt: str, font_preset: Dict[str, Any], 
                 batch_prompts: Optional[str] = None, webhook_url: Optional[str] = None,
                 single_video: Optional[str] = None) -> None:
    """Process a batch of videos with smart overlay."""
    # Create timestamp for the run
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_dir = os.path.join(output_base_dir, f"{timestamp}_run")
    edited_dir = os.path.join(run_dir, "edited")
    
    # Create output directories
    os.makedirs(edited_dir, exist_ok=True)
    
    # Initialize webhook notifier if URL is provided
    global webhook_notifier
    if webhook_url:
        try:
            from utils.webhook import WebhookNotifier
            webhook_notifier = WebhookNotifier(webhook_url)
            log.info(f"Webhook notifications enabled: {webhook_url}")
        except ImportError:
            log.warning("Webhook module not found, notifications disabled")
    
    # Set up logging to file
    log_file = os.path.join(run_dir, "run.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    log.addHandler(file_handler)
    
    log.info(f"Starting batch processing with prompt: {prompt}")
    
    # Get list of videos in input directory
    video_files = []
    
    # If a single video is specified, only process that one
    if single_video:
        video_path = os.path.join(input_dir, single_video)
        if os.path.exists(video_path):
            video_files = [video_path]
        else:
            log.error(f"Specified video not found: {video_path}")
            return
    else:
        # Otherwise, get all videos in the directory
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            video_files.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))
    
    if not video_files:
        log.error(f"No video files found in {input_dir}")
        return
    
    log.info(f"Found {len(video_files)} videos to process")
    
    # Create mapping file
    mapping_file = os.path.join(run_dir, "mapping.csv")
    with open(mapping_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "original_name", "new_name", "overlay_text", "start_sec", 
            "duration", "position_x", "position_y", "font_style", "prompt"
        ])
    
    # Process each video
    if batch_prompts:
        # Load prompts from file
        with open(batch_prompts, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        
        # Pair videos with prompts (cycle through prompts if needed)
        from itertools import cycle
        video_prompt_pairs = list(zip(video_files, cycle(prompts[:len(video_files)]) if len(prompts) < len(video_files) else prompts))
        
        for video_path, video_prompt in video_prompt_pairs:
            metadata = process_video(video_path, edited_dir, video_prompt, font_preset)
            if metadata:
                # Add timestamp to metadata
                metadata["timestamp"] = datetime.datetime.now().isoformat()
                
                # Send webhook notification if enabled
                if webhook_notifier:
                    webhook_notifier.notify_video_processed(metadata)
                # Append to mapping file
                with open(mapping_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        metadata.get("original_name", ""),
                        metadata.get("new_name", ""),
                        metadata.get("overlay_text", ""),
                        metadata.get("start_sec", 0),
                        metadata.get("duration", 0),
                        metadata.get("position_x", 0),
                        metadata.get("position_y", 0),
                        metadata.get("font_style", ""),
                        metadata.get("prompt", "")
                    ])
    else:
        # Use the same prompt for all videos
        for video_path in video_files:
            metadata = process_video(video_path, edited_dir, prompt, font_preset)
            if metadata:
                # Add timestamp to metadata
                metadata["timestamp"] = datetime.datetime.now().isoformat()
                
                # Send webhook notification if enabled
                if webhook_notifier:
                    webhook_notifier.notify_video_processed(metadata)
                # Append to mapping file
                with open(mapping_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        metadata.get("original_name", ""),
                        metadata.get("new_name", ""),
                        metadata.get("overlay_text", ""),
                        metadata.get("start_sec", 0),
                        metadata.get("duration", 0),
                        metadata.get("position_x", 0),
                        metadata.get("position_y", 0),
                        metadata.get("font_style", ""),
                        metadata.get("prompt", "")
                    ])
    
    # Send batch complete webhook notification if enabled
    if webhook_notifier:
        batch_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_videos": len(video_files),
            "successful_videos": sum(1 for v in video_files if os.path.exists(os.path.join(edited_dir, f"{slugify(prompt)[:30]}_{os.path.basename(v)}"))),
            "failed_videos": sum(1 for v in video_files if not os.path.exists(os.path.join(edited_dir, f"{slugify(prompt)[:30]}_{os.path.basename(v)}"))),
            "output_directory": run_dir,
            "mapping_file": mapping_file,
            "prompt": prompt
        }
        webhook_notifier.notify_batch_complete(batch_info)
    
    log.info(f"Batch processing complete. Results saved to {run_dir}")


def main():
    """Main entry point for the smart overlay tool."""
    parser = argparse.ArgumentParser(description="Smart Text-on-Video Overlay Tool")
    parser.add_argument("--input_dir", required=True, help="Directory containing input videos")
    parser.add_argument("--prompt", required=True, help="Text prompt to guide overlay generation")
    parser.add_argument("--output_dir", default="./outputs", help="Base directory for outputs")
    parser.add_argument("--config", default="./config.yaml", help="Path to configuration file")
    parser.add_argument("--font_path", help="Custom font path (overrides preset)")
    parser.add_argument("--preset", default="TechMeStuff", choices=list(FONT_PRESETS.keys()), 
                        help="Font preset to use")
    parser.add_argument("--batch_prompts", help="Path to file with prompts for batch processing")
    parser.add_argument("--openai_key", required=True, help="OpenAI API key")
    parser.add_argument("--webhook_url", help="URL to send webhook notifications to")
    parser.add_argument("--cpu_only", action="store_true", help="Force CPU-only mode even if GPU is available")
    parser.add_argument("--half_precision", action="store_true", help="Use half precision (FP16) for models if GPU is available")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load configuration
    global config, client
    config = load_config(args.config)
    
    # Initialize OpenAI client
    client = setup_openai_client(args.openai_key)
    
    # Load models
    setup_models()
    
    # Get font preset
    font_preset = FONT_PRESETS[args.preset].copy()
    if args.font_path:
        font_preset["font"] = args.font_path
    
    # Create fonts directory if it doesn't exist
    fonts_dir = os.path.dirname(font_preset["font"])
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir, exist_ok=True)
        log.warning(f"Created fonts directory: {fonts_dir}. You'll need to add font files.")
    
    # Process videos
    process_batch(
        args.input_dir,
        args.output_dir,
        args.prompt,
        font_preset,
        args.batch_prompts,
        args.webhook_url,
        None  # No single video specified from command line
    )


if __name__ == "__main__":
    main()

