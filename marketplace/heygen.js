'use strict';

const https = require('https');
const fs = require('fs');
const path = require('path');

const API_BASE = 'api.heygen.com';

// ── Helpers ──────────────────────────────────────────────────────────────────

function getApiKey() {
  const key = process.env.HEYGEN_API_KEY;
  if (!key) throw new Error('HEYGEN_API_KEY environment variable is not set');
  return key;
}

/**
 * Make an HTTPS request to the HeyGen API.
 * @param {string} method
 * @param {string} urlPath
 * @param {object|null} body
 * @returns {Promise<object>}
 */
function apiRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const headers = {
      'X-Api-Key': getApiKey(),
      'Accept': 'application/json',
    };
    if (body) {
      headers['Content-Type'] = 'application/json';
    }

    const payload = body ? JSON.stringify(body) : null;
    if (payload) headers['Content-Length'] = Buffer.byteLength(payload);

    const opts = {
      hostname: API_BASE,
      path: urlPath,
      method,
      headers,
    };

    const req = https.request(opts, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        const raw = Buffer.concat(chunks).toString('utf8');
        try {
          const json = JSON.parse(raw);
          resolve(json);
        } catch {
          reject(new Error(`HeyGen API returned non-JSON (status ${res.statusCode}): ${raw.slice(0, 500)}`));
        }
      });
    });

    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

/**
 * Download a file from a URL to a local path.
 * Follows redirects (up to 5).
 * @param {string} url
 * @param {string} outputPath
 * @returns {Promise<string>}
 */
function downloadFile(url, outputPath, _redirects) {
  _redirects = _redirects || 0;
  if (_redirects > 5) return Promise.reject(new Error('Too many redirects'));

  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : require('http');
    mod.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return downloadFile(res.headers.location, outputPath, _redirects + 1).then(resolve, reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`Download failed with status ${res.statusCode}`));
      }
      const dir = path.dirname(outputPath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

      const ws = fs.createWriteStream(outputPath);
      res.pipe(ws);
      ws.on('finish', () => { ws.close(); resolve(outputPath); });
      ws.on('error', reject);
    }).on('error', reject);
  });
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Generate an avatar video via HeyGen API.
 * Tries transparent WebM first, falls back to v2 green screen.
 *
 * @param {object} opts
 * @param {string} opts.text - Script text for the avatar to speak
 * @param {string} [opts.avatarId] - HeyGen avatar ID (default: Angela-inTshirt-20220820)
 * @param {string} [opts.voiceId] - HeyGen voice ID (default: en-US-JennyNeural)
 * @param {string} [opts.style] - "normal" or "closeUp" (default: normal)
 * @param {object} [opts.dimension] - { width, height } (default: 1080x1920)
 * @returns {Promise<{videoId: string, status: string}>}
 */
async function generateAvatar(opts) {
  if (!opts || !opts.text) throw new Error('text is required');

  const avatarId = opts.avatarId || 'Angela-inTshirt-20220820';
  const voiceId = opts.voiceId || 'en-US-JennyNeural';
  const style = opts.style || 'normal';
  const dimension = opts.dimension || { width: 1080, height: 1920 };

  // Try transparent WebM endpoint first
  try {
    const webmBody = {
      video_inputs: [{
        character: {
          type: 'avatar',
          avatar_id: avatarId,
          avatar_style: style,
        },
        voice: {
          type: 'text',
          input_text: opts.text,
          voice_id: voiceId,
        },
      }],
      dimension,
      aspect_ratio: null,
    };

    const res = await apiRequest('POST', '/v1/video.webm', webmBody);
    if (res.data && res.data.video_id) {
      return { videoId: res.data.video_id, status: 'pending' };
    }
  } catch {
    // WebM endpoint failed — fall through to v2
  }

  // Fallback: v2 with green screen background
  const v2Body = {
    video_inputs: [{
      character: {
        type: 'avatar',
        avatar_id: avatarId,
        avatar_style: style,
      },
      voice: {
        type: 'text',
        input_text: opts.text,
        voice_id: voiceId,
      },
      background: {
        type: 'color',
        value: '#00FF00',
      },
    }],
    dimension,
  };

  const res = await apiRequest('POST', '/v2/video/generate', v2Body);
  if (res.error) throw new Error(res.error.message || JSON.stringify(res.error));
  if (!res.data || !res.data.video_id) {
    throw new Error('HeyGen API did not return a video_id: ' + JSON.stringify(res));
  }
  return { videoId: res.data.video_id, status: 'pending' };
}

/**
 * Poll HeyGen API until a video is complete.
 * Polls every 15 seconds, times out after 20 minutes.
 *
 * @param {string} videoId
 * @returns {Promise<{status: string, videoUrl: string|null, captionUrl: string|null, duration: number|null}>}
 */
function pollVideoStatus(videoId) {
  if (!videoId) return Promise.reject(new Error('videoId is required'));

  const POLL_INTERVAL = 15000;   // 15 seconds
  const TIMEOUT = 20 * 60 * 1000; // 20 minutes
  const start = Date.now();

  return new Promise((resolve, reject) => {
    function check() {
      apiRequest('GET', '/v1/video_status.get?video_id=' + encodeURIComponent(videoId), null)
        .then((res) => {
          const d = res.data || {};
          const status = d.status || 'unknown';

          if (status === 'completed') {
            return resolve({
              status: 'completed',
              videoUrl: d.video_url || null,
              captionUrl: d.caption_url || null,
              duration: d.duration || null,
            });
          }

          if (status === 'failed' || status === 'error') {
            return reject(new Error('HeyGen video generation failed: ' + (d.error || status)));
          }

          if (Date.now() - start > TIMEOUT) {
            return reject(new Error('HeyGen video generation timed out after 20 minutes'));
          }

          setTimeout(check, POLL_INTERVAL);
        })
        .catch(reject);
    }

    check();
  });
}

/**
 * Download a completed HeyGen video to local disk.
 *
 * @param {string} videoUrl
 * @param {string} outputPath
 * @returns {Promise<string>} resolved output path
 */
function downloadVideo(videoUrl, outputPath) {
  if (!videoUrl) return Promise.reject(new Error('videoUrl is required'));
  if (!outputPath) return Promise.reject(new Error('outputPath is required'));
  return downloadFile(videoUrl, outputPath);
}

/**
 * Full pipeline: generate → poll → download.
 *
 * @param {object} opts - Same as generateAvatar opts, plus optional outputPath
 * @returns {Promise<{outputPath: string, duration: number|null, captionUrl: string|null}>}
 */
async function generateAndDownload(opts) {
  const gen = await generateAvatar(opts);
  const result = await pollVideoStatus(gen.videoId);

  if (!result.videoUrl) {
    throw new Error('Video completed but no download URL was returned');
  }

  const ext = result.videoUrl.includes('.webm') ? '.webm' : '.mp4';
  const outDir = path.join(__dirname, '..', 'output', 'avatars');
  const outPath = opts.outputPath || path.join(outDir, Date.now() + ext);

  await downloadVideo(result.videoUrl, outPath);

  return {
    outputPath: outPath,
    duration: result.duration,
    captionUrl: result.captionUrl,
  };
}

/**
 * List available HeyGen avatars.
 * @returns {Promise<object>}
 */
async function listAvatars() {
  const res = await apiRequest('GET', '/v1/avatar.list', null);
  if (res.error) throw new Error(res.error.message || JSON.stringify(res.error));
  return res.data || res;
}

module.exports = {
  generateAvatar,
  pollVideoStatus,
  downloadVideo,
  generateAndDownload,
  listAvatars,
};
