# N8N Workflow Setup Guide - Video Enhancement API

## 📁 Available Workflows

I've created **2 N8N workflows** for you:

### 1. **Complete Workflow** (`n8n_video_enhancement_workflow.json`)
- **Full-featured** with error handling, compatibility checks, and notifications
- **15 nodes** including health checks, data extraction, and conditional logic
- **Comprehensive logging** and status reporting
- **Slack notifications** (optional - disabled by default)

### 2. **Simple Workflow** (`n8n_simple_workflow.json`)
- **Quick test** workflow with 5 nodes
- **Minimal setup** for fast testing
- **Direct processing** without complex logic
- **Perfect for debugging** and initial testing

---

## 🚀 Import Instructions

### Step 1: Access N8N
1. Open your N8N instance (usually `http://localhost:5678`)
2. Click **"Workflows"** in the left sidebar
3. Click **"Import from File"** button

### Step 2: Import Workflow
1. **For Full Workflow:** Select `n8n_video_enhancement_workflow.json`
2. **For Simple Test:** Select `n8n_simple_workflow.json`
3. Click **"Import"**
4. The workflow will appear in your workflows list

---

## ⚙️ Configuration Steps

### 1. **Update Video Filename**
In the **"Set Configuration"** node, update:
```json
{
  "video_filename": "YOUR_VIDEO_FILE.mp4"
}
```

### 2. **Verify API Base URL**
Ensure the Flask API base URL is correct:
```json
{
  "flask_api_base": "http://localhost:5003"
}
```

### 3. **Optional: Configure Notifications**
To enable Slack notifications:
1. **Enable** the disabled Slack nodes
2. **Add Slack credentials** in N8N settings
3. **Set channel/webhook** for notifications

---

## 🎯 How to Use

### **Complete Workflow**

1. **Start Workflow:** Click the **"🎬 Start Video Processing"** trigger
2. **Automatic Processing:**
   - ✅ API health check
   - 🎵 Music compatibility analysis
   - 📊 Data extraction and validation
   - ✅ Compatibility score check (≥0.6)
   - 🎬 Video processing (if compatible)
   - ⬇️ Download enhanced video
   - 📋 Final summary report

3. **View Results:** Check the final node outputs for:
   - Processing summary
   - Download URLs
   - Performance metrics
   - Error messages (if any)

### **Simple Workflow**

1. **Start:** Click **"▶️ Start"** trigger
2. **Direct Processing:** 
   - 🎵 Analyze music match
   - 🎬 Process video immediately
   - ⬇️ Download result
3. **Check Output:** Final node contains the enhanced video file

---

## 📊 Workflow Node Details

### **Complete Workflow Nodes:**

| Node | Purpose | Output |
|------|---------|--------|
| 🎬 Start Video Processing | Manual trigger | Starts the workflow |
| ⚙️ Set Configuration | Define parameters | Video filename, API settings |
| 🔍 API Health Check | Verify Flask API | System status |
| 🎵 Analyze Music Match | Get music recommendations | Best match data |
| 📊 Extract Music Data | Parse analysis results | Music compatibility scores |
| ✅ Check Compatibility | Validate score threshold | Pass/fail decision |
| 🎬 Process Video | Enhance video with music | Processing results |
| 📤 Extract Results | Parse processing output | Download URLs |
| ⬇️ Download Enhanced Video | Get final video file | Enhanced video |
| 📋 Final Summary | Generate report | Complete processing summary |
| ⚠️ Compatibility Too Low | Handle low scores | Error information |
| 🏁 Final Status Check | Determine success/failure | Route to notifications |
| ✅ Success Notification | Send success alert | Slack message |
| ❌ Error Notification | Send error alert | Slack message |

### **Simple Workflow Nodes:**

| Node | Purpose | Output |
|------|---------|--------|
| ▶️ Start | Manual trigger | Starts workflow |
| ⚙️ Config | Set video filename | Configuration data |
| 🎵 Analyze | Get music match | Music analysis |
| 🎬 Process | Enhance video | Processing results |
| ⬇️ Download | Get final video | Enhanced video file |

---

## 🔧 Customization Options

### **Volume Levels**
Change music volume in the **"🎬 Process Video"** node:
```json
{
  "config": {
    "music_volume": 0.003162,  // -25dB (recommended)
    "music_volume": 0.01,      // -20dB (more noticeable)
    "music_volume": 0.001      // -30dB (very subtle)
  }
}
```

### **Text Styles**
Modify text overlay style:
```json
{
  "config": {
    "text_style": "modern",      // Modern style
    "text_style": "classic",     // Classic style
    "text_style": "minimal"      // Minimal style
  }
}
```

### **Compatibility Threshold**
Adjust minimum compatibility score:
```json
{
  "config": {
    "min_compatibility_score": 0.6   // Default (60%)
    "min_compatibility_score": 0.4   // More lenient (40%)
    "min_compatibility_score": 0.8   // Stricter (80%)
  }
}
```

---

## 🐛 Troubleshooting

### **Common Issues:**

1. **"Connection Refused" Error**
   - **Solution:** Ensure Flask API is running on `http://localhost:5003`
   - **Check:** Run `curl http://localhost:5003/health`

2. **"Video Not Found" Error**
   - **Solution:** Verify video file exists in shared directory
   - **Check:** File path and spelling

3. **"Compatibility Too Low" Error**
   - **Solution:** Lower `min_compatibility_score` or add more music tracks
   - **Check:** Analysis results for best available match

4. **Processing Timeout**
   - **Solution:** Increase timeout in HTTP Request nodes
   - **Check:** Video file size and processing complexity

### **Debug Steps:**

1. **Test Individual Nodes:** Run each node separately
2. **Check Node Outputs:** Inspect JSON data at each step
3. **Verify API Responses:** Check Flask console logs
4. **Monitor Processing:** Watch processing time and memory usage

---

## 📈 Performance Tips

### **For Large Videos:**
- Process during off-peak hours
- Ensure sufficient disk space
- Monitor system resources
- Consider batch processing for multiple videos

### **For Better Music Matching:**
- Add more music tracks to your library
- Provide videos with clear audio/visual themes
- Use descriptive video filenames
- Regularly update music compatibility cache

---

## 🔗 Integration Examples

### **Webhook Trigger**
Replace manual trigger with webhook for automation:
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "enhance-video",
    "options": {}
  },
  "type": "n8n-nodes-base.webhook"
}
```

### **File System Watch**
Monitor directory for new videos:
```json
{
  "parameters": {
    "path": "C:\\Users\\Isaia\\Documents\\Coding\\N8N\\shared\\videos",
    "watchFor": "files"
  },
  "type": "n8n-nodes-base.fileSystem"
}
```

### **Scheduled Processing**
Run at specific times:
```json
{
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "0 2 * * *"
        }
      ]
    }
  },
  "type": "n8n-nodes-base.cron"
}
```

---

## 📝 Testing Checklist

Before running in production:

- [ ] Flask API is running and healthy
- [ ] Video file exists in shared directory
- [ ] OpenAI API key is configured
- [ ] Music library is loaded (6+ tracks)
- [ ] N8N has sufficient permissions
- [ ] Network connectivity is stable
- [ ] Disk space is available for output

---

## 🎉 Success Metrics

After successful processing, you should see:
- ✅ **Video enhanced** with AI-selected music
- 🎵 **Music added** at specified volume level
- 📝 **Text overlay** applied with modern styling
- ⏱️ **Processing time** logged (typically 15-30 seconds)
- 📁 **Output file** available for download
- 💯 **Compatibility score** meeting threshold requirements

---

*Ready to enhance your videos with AI-powered music matching! 🚀*
