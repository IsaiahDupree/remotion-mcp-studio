---
description: Start Flask Video Enhancement API after vacation
---

# Start Flask Video Enhancement API

Follow these steps to get the video processing API running:

## 1. Navigate to project directory
```bash
cd C:\Users\Isaia\Documents\WordsOnText
```

## 2. Verify environment setup
```bash
# Check if .env file exists with OpenAI API key
type .env
```

## 3. Install/verify dependencies
```bash
pip install flask requests python-dotenv openai moviepy pillow numpy opencv-python
```

// turbo
## 4. Kill any existing Python processes
```bash
taskkill /F /IM python.exe
```

// turbo
## 5. Start the Flask API
```bash
python flask_app.py
```

## 6. Verify system is running
Wait for these success messages in console:
- ✅ Enhanced video processor initialized
- ✅ Intelligent music matcher initialized  
- ✅ Local music selector initialized
- ✅ Music enhancer initialized
- ✅ Text styler initialized
- 🚀 SmartVideoProcessor initialized successfully
- * Running on http://127.0.0.1:5003

## 7. Test health endpoint
```bash
curl http://localhost:5003/health
```

## Success!
Your Flask API is now ready for N8N integration at `http://localhost:5003`

## N8N Quick Test
Use this HTTP Request node configuration:
- Method: GET
- URL: `http://localhost:5003/analyze/music-match/your_video.mp4`
- Headers: `Content-Type: application/json`
