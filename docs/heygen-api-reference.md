# HeyGen API Reference — Complete Documentation

Saved: 2026-04-04
Source: https://docs.heygen.com/reference

---

## Authentication

All endpoints require: `x-api-key: <your-api-key>` header

---

## 1. Video Generation

### POST /v2/video/generate — Create Studio Video
**URL:** `https://api.heygen.com/v2/video/generate`

**Request Body:**
```json
{
  "video_inputs": [          // REQUIRED, 1-50 scenes
    {
      "character": {          // REQUIRED
        "type": "avatar",     // "avatar" | "talking_photo"
        "avatar_id": "string",
        "avatar_style": "normal",  // "normal" | "closeUp" | "circle"
        "scale": 1.0,         // 0.0-5.0
        "offset": { "x": 0.0, "y": 0.0 },
        "matting": false,      // remove background
        "use_avatar_iv_model": false,
        "prompt": "string",    // Avatar IV motion instructions
        "circle_background_color": "#FFFFFF"
      },
      "voice": {              // REQUIRED — one of:
        // Text type:
        "type": "text",
        "voice_id": "string",
        "input_text": "string",  // max 5000 chars
        "speed": 1.0,          // 0.5-1.5
        "pitch": 0,            // -50 to 50
        "emotion": "Friendly",  // "Excited"|"Friendly"|"Serious"|"Soothing"|"Broadcaster"
        "locale": "en-US",
        "elevenlabs_settings": {
          "model": "eleven_v3",
          "similarity_boost": 0.5,
          "stability": 1.0,
          "style": 0.0
        }

        // Audio type:
        // "type": "audio",
        // "audio_url": "string" OR "audio_asset_id": "string"

        // Silence type:
        // "type": "silence",
        // "duration": "5"  // 1.0-100.0 seconds
      },
      "background": {         // OPTIONAL
        "type": "color",       // "color" | "image" | "video"
        "value": "#FFFFFF",    // hex color (color type)
        "url": "string",       // image/video URL
        "image_asset_id": "string",
        "video_asset_id": "string",
        "play_style": "loop",  // "freeze"|"loop"|"fit_to_scene" (video)
        "fit": "cover"         // "crop"|"cover"|"contain"|"none" (video)
      }
    }
  ],
  "dimension": { "width": 1920, "height": 1080 },  // 128-4096 px
  "caption": false,
  "title": "string",
  "callback_url": "string",
  "callback_id": "string",
  "folder_id": "string"
}
```

**Response (200):**
```json
{ "error": null, "data": { "video_id": "string" } }
```

---

### POST /v1/video.webm — Create Transparent WebM Video
**URL:** `https://api.heygen.com/v1/video.webm`

**Request Body:**
```json
{
  "avatar_pose_id": "string",    // REQUIRED — avatar ID
  "avatar_style": "normal",      // "normal" | "closeUp"
  "input_text": "string",        // Text to speak (OR use input_audio)
  "voice_id": "string",          // Required with input_text
  "input_audio": "string",       // Audio URL (alternative to text)
  "dimension": { "width": 1280, "height": 720 }
}
```

**Response (200):**
```json
{ "code": 100, "data": { "video_id": "string" }, "message": "string" }
```

**Limitations:**
- Only supports HeyGen studio avatars (NOT all custom avatars)
- Error 400175 = "Avatar does not support WebM"
- Default 1280x720

---

## 2. Video Status & Management

### GET /v1/video_status.get — Check Video Status
**URL:** `https://api.heygen.com/v1/video_status.get?video_id=<id>`

**Status Values:**
- `pending` — in queue
- `waiting` — pre-processing
- `processing` — rendering
- `completed` — done
- `failed` — error

**Response (200):**
```json
{
  "data": {
    "id": "string",
    "status": "completed",
    "video_url": "string",         // expires in 7 days
    "thumbnail_url": "string",
    "video_url_caption": "string",  // captioned version
    "caption_url": "string",        // .ass format
    "gif_url": "string",
    "duration": 30.5,
    "created_at": 1234567890,
    "error": null,
    "callback_id": "string"
  }
}
```

---

## 3. Avatars

### GET /v2/avatars — List All Avatars
**URL:** `https://api.heygen.com/v2/avatars`

**Response:**
```json
{
  "data": {
    "avatars": [{
      "avatar_id": "string",
      "avatar_name": "string",
      "gender": "string",
      "preview_image_url": "string",
      "preview_video_url": "string",
      "premium": false,
      "type": "string",
      "tags": ["string"],
      "default_voice_id": "string"
    }],
    "talking_photos": [{
      "talking_photo_id": "string",
      "talking_photo_name": "string",
      "preview_image_url": "string"
    }]
  }
}
```

---

## 4. Voices

### GET /v2/voices — List All Voices
**URL:** `https://api.heygen.com/v2/voices`

**Response:**
```json
{
  "data": {
    "voices": [{
      "voice_id": "string",
      "name": "string",
      "language": "string",
      "gender": "male|female|unknown",
      "preview_audio": "string",
      "support_pause": true,
      "emotion_support": true,
      "support_interactive_avatar": true,
      "support_locale": true
    }]
  }
}
```

---

## 5. Templates

### GET /v2/template/{template_id} — Get Template Details
**URL:** `https://api.heygen.com/v2/template/{template_id}`

**Response:**
```json
{
  "data": {
    "variables": {
      "var_name": {
        "name": "string",
        "type": "text|image|video|character|voice",
        "properties": {
          "content": "string",     // text type
          "url": "string",          // image/video type
          "asset_id": "string",
          "fit": "string",
          "character_id": "string", // character type
          "voice_id": "string"      // voice type
        }
      }
    }
  }
}
```

### POST /v2/template/{template_id}/generate — Generate from Template
**URL:** `https://api.heygen.com/v2/template/{template_id}/generate`

**Request Body:**
```json
{
  "variables": {},           // REQUIRED — JSON of variable overrides
  "caption": false,
  "title": "string",
  "dimension": { "width": 1920, "height": 1080 },
  "callback_url": "string",
  "folder_id": "string",
  "brand_voice_id": "string",
  "enable_sharing": false,
  "include_gif": false,
  "keep_text_vertically_centered": false
}
```

---

## 6. Asset Upload

### POST /v1/asset — Upload Asset
**URL:** `https://upload.heygen.com/v1/asset`

**Headers:**
- `X-API-KEY: <key>`
- `Content-Type`: `image/png` | `image/jpeg` | `video/mp4` | `video/webm` | `audio/mpeg`

**Body:** Raw binary file data

**Response:**
```json
{
  "code": 100,
  "data": {
    "id": "string",
    "file_type": "audio|video|image",
    "url": "string",
    "created_ts": 1234567890,
    "image_key": "string|null",
    "folder_id": "string",
    "meta": {}
  }
}
```

---

## 7. Streaming Avatar (DEPRECATED — sunsets March 31, 2026)
**Migrating to:** LiveAvatar (docs.liveavatar.com)
- Uses WebRTC for low-latency interactive avatars
- npm: `@heygen/streaming-avatar`
- Not useful for Remotion (pre-rendered video is better)

---

## Limits Summary

| Limit | Value |
|-------|-------|
| Max text input | 5,000 characters |
| Max audio input | 600 seconds (10 min) |
| Max scenes per video | 50 |
| Video dimensions | 128-4096 px |
| Output frame rate | 25 fps |
| Video upload max | 100 MB, <2K resolution |
| Image upload max | 50 MB, <2K resolution |
| Audio upload max | 50 MB |
| Video URL expiry | 7 days (re-poll to regenerate) |

## Pricing

| Resource | Cost/sec |
|----------|----------|
| Public Avatar Engine IV | $0.10 |
| Digital Twin Engine IV | $0.10 |
| Public Avatar Engine III | $0.0167 |
| Photo Avatar Engine III | $0.0167 |
| TTS Starfish | $0.000333 |
| Prompt to Video | $0.0333 |
| Photo avatar/generate | $1/call |
| Photo avatar/train | $4/call |
