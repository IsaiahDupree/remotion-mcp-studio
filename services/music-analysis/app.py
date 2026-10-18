import os
import json
import uuid
import subprocess
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/video-generator'
OUTPUT_FOLDER = '/tmp/video-generator/output'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'png', 'jpg', 'jpeg'}

# Create required directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def combine_audio_files(audio_files, output_file):
    """Combine multiple audio files into a single file"""
    # Create a file with a list of audio files to concatenate
    concat_list_path = f"{UPLOAD_FOLDER}/concat_list_{uuid.uuid4()}.txt"
    with open(concat_list_path, 'w') as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")
    
    # Use FFmpeg to concatenate the audio files
    subprocess.run([
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c', 'copy',
        output_file
    ], check=True)
    
    # Clean up the temporary list file
    os.remove(concat_list_path)
    
    return output_file

def create_video_from_audio_and_image(audio_file, image_file, output_file):
    """Create a video file using an audio file and a static image"""
    subprocess.run([
        'ffmpeg',
        '-loop', '1',
        '-i', image_file,
        '-i', audio_file,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_file
    ], check=True)
    
    return output_file

@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        # Get the JSON data
        content = request.json
        
        # Parse the content
        if not isinstance(content, list):
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        # Extract audio paths and image path
        audio_paths = []
        image_path = None
        
        for item in content:
            if 'audioPaths' in item:
                audio_paths.extend(item['audioPaths'])
            if 'imagePath' in item:
                image_path = item['imagePath']
        
        if not audio_paths:
            return jsonify({'error': 'No audio paths provided'}), 400
        
        if not image_path:
            return jsonify({'error': 'No image path provided'}), 400
        
        # Generate unique filenames for output files
        unique_id = uuid.uuid4()
        combined_audio_path = f"{UPLOAD_FOLDER}/combined_{unique_id}.mp3"
        output_video_path = f"{OUTPUT_FOLDER}/video_{unique_id}.mp4"
        
        # Combine audio files
        combine_audio_files(audio_paths, combined_audio_path)
        
        # Create video from audio and image
        create_video_from_audio_and_image(combined_audio_path, image_path, output_video_path)
        
        # Clean up the temporary combined audio file
        os.remove(combined_audio_path)
        
        return jsonify({
            'success': True,
            'videoPath': output_video_path
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze-music-match', methods=['POST'])
def analyze_music_match():
    """Intelligent music matching using WordsOnText music analysis system"""
    try:
        content = request.json
        
        # Extract video analysis data from n8n workflow
        video_path = content.get('video_path', '')
        video_analysis = content.get('video_analysis', {})
        transcript = content.get('transcript', '')
        visual_analysis = content.get('visual_analysis', '')
        
        # Define music library path (will be mounted from WordsOnText)
        music_library_path = '/srv/music_library'
        
        # Simulate music analysis logic based on video content
        # In full implementation, this would use MusicVideoMatcher class
        
        # Analyze video mood and content type
        mood_keywords = {
            'energetic': ['action', 'fast', 'dynamic', 'exciting'],
            'calm': ['peaceful', 'slow', 'relaxing', 'quiet'],
            'upbeat': ['happy', 'positive', 'cheerful', 'lively'],
            'dramatic': ['intense', 'serious', 'emotional', 'powerful']
        }
        
        detected_mood = 'neutral'
        content_text = f"{transcript} {visual_analysis}".lower()
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                detected_mood = mood
                break
        
        # Genre mapping based on mood
        genre_mapping = {
            'energetic': 'electronic',
            'calm': 'ambient', 
            'upbeat': 'house',
            'dramatic': 'corporate',
            'neutral': 'general'
        }
        
        recommended_genre = genre_mapping.get(detected_mood, 'general')
        
        # Mock music selection (in real implementation, would query music_index.json)
        selected_music = {
            'file_path': f'/srv/music_library/{recommended_genre}/selected_track.aac',
            'name': f'AI Selected {recommended_genre.title()} Track',
            'genre': recommended_genre,
            'mood': detected_mood,
            'energy_level': 'medium' if detected_mood == 'calm' else 'high',
            'size_mb': 3.5
        }
        
        result = {
            'success': True,
            'video_analysis': {
                'detected_mood': detected_mood,
                'content_type': 'video',
                'transcript_length': len(transcript),
                'has_visual_analysis': bool(visual_analysis)
            },
            'music_recommendation': selected_music,
            'compatibility': {
                'score': 0.87,
                'reasoning': f'Selected {recommended_genre} music matches {detected_mood} mood detected in video',
                'mood_match': 'high',
                'energy_match': 'high',
                'theme_match': 'medium'
            },
            'timestamp': str(uuid.uuid4())
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': {
                'received_data': content if 'content' in locals() else 'No data received'
            }
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
