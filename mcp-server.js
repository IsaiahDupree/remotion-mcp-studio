#!/usr/bin/env node
/**
 * Remotion MCP Studio — Unified Video Generation MCP Server v2.0
 *
 * Merged from: ai-video-platform, remotion-tiktok-pipeline, content-ai-pipeline, custom-video-tools
 *
 * Tools (24 total):
 *   ── Remotion Core ──
 *   remotion_list_formats        — available formats + schemas (12 formats)
 *   remotion_generate_brief      — build ContentBrief from topic/title inputs
 *   remotion_validate_brief      — validate brief before submitting
 *   remotion_render              — submit async render job (local)
 *   remotion_render_modal        — render on Modal cloud (GPU)
 *   remotion_render_still        — render single frame (PNG/JPEG)
 *   remotion_render_thumbnail_cloud — YouTube thumbnail via Modal
 *   remotion_job_status          — check job status by ID
 *   remotion_list_jobs           — list recent render jobs
 *   remotion_list_outputs        — list rendered MP4 files
 *   remotion_list_compositions   — browse 50+ compositions
 *   remotion_list_scenes         — browse 30+ scene templates
 *   remotion_list_animations     — browse 12+ animation presets
 *   remotion_generate_voiceover  — voice clone via Modal
 *   remotion_send_telegram       — send renders to Telegram
 *
 *   ── TikTok Pipeline ──
 *   tiktok_render                — TikTok-optimized render with themes
 *   tiktok_list_briefs           — list TikTok brief templates
 *
 *   ── AI Content Pipeline ──
 *   pipeline_research            — research topics via Perplexity
 *   pipeline_generate_script     — generate scripts via Claude
 *   pipeline_generate_voiceover  — TTS via ElevenLabs
 *   pipeline_full_run            — full pipeline: research → script → render
 *
 *   ── Python Services ──
 *   services_status              — check Docker service status
 *   services_start               — start Docker services
 *   services_music_match         — AI music matching for videos
 *   services_text_overlay        — smart text overlay with AI
 *
 *   ── Template Marketplace ──
 *   marketplace_browse           — browse templates by category
 *   marketplace_search           — search templates by keyword
 *   marketplace_details          — get full template details
 *   marketplace_publish          — publish a template for sale
 *   marketplace_buy              — purchase/download a template
 *   marketplace_my_templates     — list seller's published templates
 *   marketplace_my_purchases     — list buyer's purchased templates
 *   marketplace_review           — submit a review for a template
 *   marketplace_categories       — list all marketplace categories
 */

'use strict';

const { spawn, execSync, spawnSync } = require('child_process');
const fs = require('fs');
const https = require('https');
const http = require('http');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');

const marketplace = require('./marketplace/server');
const heygen = require('./marketplace/heygen');
const REMOTION_DIR = path.resolve(__dirname);
const OUTPUT_DIR = path.join(REMOTION_DIR, 'output');
const BRIEFS_DIR = path.join(REMOTION_DIR, 'data', 'briefs', 'mcp');
const JOBS_FILE = path.join(OUTPUT_DIR, '.mcp-jobs.json');
const STILLS_DIR = path.join(OUTPUT_DIR, 'stills');

// Telegram config from environment (load from actp-worker .env if not set)
function _loadEnv() {
  try {
    const envFile = require('fs').readFileSync(
      path.join(path.dirname(REMOTION_DIR), 'actp-worker', '.env'),
      'utf8'
    );
    for (const line of envFile.split('\n')) {
      const m = line.match(/^([A-Z0-9_]+)=(.+)$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
    }
  } catch {}
}
_loadEnv();

// ── Job Registry ─────────────────────────────────────────────────────────────

/** @type {Map<string, object>} */
const jobs = new Map();

function loadJobs() {
  try {
    if (fs.existsSync(JOBS_FILE)) {
      const data = JSON.parse(fs.readFileSync(JOBS_FILE, 'utf8'));
      for (const job of data) {
        jobs.set(job.id, job);
      }
    }
  } catch {}
}

function saveJobs() {
  try {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    const recent = Array.from(jobs.values())
      .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))
      .slice(0, 50);
    fs.writeFileSync(JOBS_FILE, JSON.stringify(recent, null, 2));
  } catch {}
}

function makeJobId() {
  return `job_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
}

loadJobs();

// ── Brief Templates ───────────────────────────────────────────────────────────

const FORMATS = {
  explainer_v1: {
    name: 'Explainer',
    description: 'Educational walkthrough: intro → 3-5 topic slides → outro. Best for "5 hacks", "how AI works", "what is X" content.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['intro', 'topic', 'outro'],
  },
  listicle_v1: {
    name: 'Listicle',
    description: 'Numbered list format: intro → numbered items → outro. Best for ranked lists, "top 10", "3 reasons" content.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['intro', 'list_item', 'outro'],
  },
  comparison_v1: {
    name: 'Comparison',
    description: 'Side-by-side comparison: intro → comparison slide → outro. Best for "X vs Y", before/after content.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['intro', 'comparison', 'outro'],
  },
  shorts_v1: {
    name: 'Shorts',
    description: 'Ultra-short 15s format: hook → key point → CTA. Best for viral hooks, quick tips.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['hook', 'content', 'cta'],
  },
  // ── TikTok Pipeline Formats (from remotion-tiktok-pipeline) ──
  tiktok_v1: {
    name: 'TikTok (Pipeline)',
    description: 'TikTok-optimized vertical video with hook slam, body points, phone frame, and outro. Best for app promos, viral tips.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['hook', 'body', 'phone_frame', 'outro'],
    renderer: 'tiktok-pipeline',
  },
  tiktok_myth_v1: {
    name: 'TikTok Myth/Reality',
    description: 'Myth vs Reality format for TikTok. Hook → myth busting → reveal → CTA.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['hook', 'myth', 'reality', 'outro'],
    renderer: 'tiktok-pipeline',
  },
  tiktok_problem_solution_v1: {
    name: 'TikTok Problem/Solution',
    description: 'Problem → agitate → solution format for TikTok. Great for product demos.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['problem', 'agitate', 'solution', 'cta'],
    renderer: 'tiktok-pipeline',
  },
  // ── Content Pipeline Formats (from content-ai-pipeline) ──
  content_pipeline_v1: {
    name: 'Content Pipeline',
    description: 'AI-generated content video: background video + captions + name bar + summary strap. Research → Script → Voiceover → Video.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['background', 'captions', 'name_bar', 'summary_strap'],
    renderer: 'content-pipeline',
  },
  // ── Platform-Specific from ai-video-platform ──
  youtube_explainer_v2: {
    name: 'YouTube Explainer',
    description: 'Long-form explainer for YouTube. Intro → chapters → enhanced topics → outro.',
    aspectRatio: '16:9',
    resolution: { width: 1920, height: 1080 },
    sections: ['intro', 'chapter', 'topic', 'outro'],
  },
  instagram_reel_v1: {
    name: 'Instagram Reel',
    description: 'Instagram Reel format. Hook → content → CTA with IG-native caption styles.',
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    sections: ['hook', 'content', 'cta'],
  },
  linkedin_v1: {
    name: 'LinkedIn Video',
    description: 'Professional LinkedIn video. Framework → insights → stats → CTA.',
    aspectRatio: '1:1',
    resolution: { width: 1080, height: 1080 },
    sections: ['hook', 'framework', 'insight', 'cta'],
  },
};

const THEMES = {
  dark: {
    primary_color: '#ffffff',
    secondary_color: '#a1a1aa',
    accent_color: '#3b82f6',
    background_type: 'gradient',
    background_value: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%)',
  },
  light: {
    primary_color: '#0a0a0a',
    secondary_color: '#52525b',
    accent_color: '#2563eb',
    background_type: 'gradient',
    background_value: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
  },
  neon: {
    primary_color: '#ffffff',
    secondary_color: '#d4d4d8',
    accent_color: '#a855f7',
    background_type: 'gradient',
    background_value: 'linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%)',
  },
  // ── TikTok Pipeline Themes ──
  tiktok: {
    primary_color: '#ffffff',
    secondary_color: '#a1a1aa',
    accent_color: '#fe2c55',
    background_type: 'gradient',
    background_value: 'linear-gradient(135deg, #000000 0%, #0a0a0a 100%)',
  },
  everreach: {
    primary_color: '#ffffff',
    secondary_color: '#c4b5fd',
    accent_color: '#7c3aed',
    background_type: 'gradient',
    background_value: 'linear-gradient(135deg, #1a0533 0%, #2d1b69 50%, #1a0533 100%)',
  },
  minimal: {
    primary_color: '#0a0a0a',
    secondary_color: '#52525b',
    accent_color: '#18181b',
    background_type: 'solid',
    background_value: '#fafafa',
  },
};

/**
 * Generate a ContentBrief from simple inputs.
 * @param {object} input
 * @returns {object} ContentBrief
 */
function generateBrief(input) {
  const {
    title,
    subtitle,
    hookText,
    format = 'explainer_v1',
    theme = 'dark',
    topics = [],
    listItems = [],
    ctaText = 'Follow for more',
    ctaHandle = '',
    accentColor,
    durationPerTopic = 8,
  } = input;

  if (!title) throw new Error('title is required');
  if (!FORMATS[format]) throw new Error(`Unknown format: ${format}. Valid: ${Object.keys(FORMATS).join(', ')}`);

  const themeConfig = THEMES[theme] || THEMES.dark;
  if (accentColor) themeConfig.accent_color = accentColor;

  const id = `brief_${Date.now()}_${crypto.randomBytes(3).toString('hex')}`;
  const sections = [];
  let currentTime = 0;

  if (format === 'explainer_v1') {
    // Intro
    sections.push({
      id: 'intro_001',
      type: 'intro',
      duration_sec: 5,
      start_time_sec: currentTime,
      content: { type: 'intro', title, subtitle, hook_text: hookText },
    });
    currentTime += 5;

    // Topics
    const topicList = topics.length > 0 ? topics : ['Key Point'];
    for (let i = 0; i < topicList.length; i++) {
      const item = typeof topicList[i] === 'string'
        ? { heading: topicList[i], body_text: '' }
        : topicList[i];
      sections.push({
        id: `topic_${String(i + 1).padStart(3, '0')}`,
        type: 'topic',
        duration_sec: durationPerTopic,
        start_time_sec: currentTime,
        content: {
          type: 'topic',
          heading: item.heading || item,
          body_text: item.body_text || '',
          bullet_points: item.bullet_points || [],
          icon: item.icon,
          animation_style: item.animation_style || 'slide',
        },
      });
      currentTime += durationPerTopic;
    }

    // Outro
    sections.push({
      id: 'outro_001',
      type: 'outro',
      duration_sec: 5,
      start_time_sec: currentTime,
      content: {
        type: 'outro',
        title: 'Follow for More',
        call_to_action: ctaText,
        social_handles: ctaHandle ? [{ platform: 'TikTok', handle: ctaHandle }] : [],
      },
    });
    currentTime += 5;

  } else if (format === 'listicle_v1') {
    sections.push({
      id: 'intro_001',
      type: 'intro',
      duration_sec: 5,
      start_time_sec: currentTime,
      content: { type: 'intro', title, subtitle, hook_text: hookText },
    });
    currentTime += 5;

    const items = listItems.length > 0 ? listItems : topics;
    for (let i = 0; i < items.length; i++) {
      const item = typeof items[i] === 'string' ? { title: items[i], description: '' } : items[i];
      sections.push({
        id: `item_${String(i + 1).padStart(3, '0')}`,
        type: 'list_item',
        duration_sec: durationPerTopic,
        start_time_sec: currentTime,
        content: {
          type: 'list_item',
          number: i + 1,
          title: item.title || item,
          description: item.description || '',
        },
      });
      currentTime += durationPerTopic;
    }

    sections.push({
      id: 'outro_001',
      type: 'outro',
      duration_sec: 5,
      start_time_sec: currentTime,
      content: {
        type: 'outro',
        title: 'Found this helpful?',
        call_to_action: ctaText,
        social_handles: ctaHandle ? [{ platform: 'TikTok', handle: ctaHandle }] : [],
      },
    });
    currentTime += 5;

  } else if (format === 'shorts_v1') {
    sections.push({
      id: 'hook_001',
      type: 'hook',
      duration_sec: 3,
      start_time_sec: 0,
      content: { type: 'hook', text: hookText || title, subtext: subtitle },
    });
    sections.push({
      id: 'content_001',
      type: 'content',
      duration_sec: 9,
      start_time_sec: 3,
      content: {
        type: 'topic',
        heading: title,
        body_text: topics[0] || '',
        animation_style: 'fade',
      },
    });
    sections.push({
      id: 'cta_001',
      type: 'cta',
      duration_sec: 3,
      start_time_sec: 12,
      content: { type: 'cta', title: ctaText, action_text: 'Follow', url: ctaHandle },
    });
    currentTime = 15;

  } else if (format === 'comparison_v1') {
    const left = input.leftItem || { label: 'Option A', points: [] };
    const right = input.rightItem || { label: 'Option B', points: [] };
    sections.push({
      id: 'intro_001',
      type: 'intro',
      duration_sec: 5,
      start_time_sec: 0,
      content: { type: 'intro', title, subtitle, hook_text: hookText },
    });
    sections.push({
      id: 'comparison_001',
      type: 'comparison',
      duration_sec: 15,
      start_time_sec: 5,
      content: { type: 'comparison', title, left_item: left, right_item: right },
    });
    sections.push({
      id: 'outro_001',
      type: 'outro',
      duration_sec: 5,
      start_time_sec: 20,
      content: {
        type: 'outro',
        title: 'Which do you prefer?',
        call_to_action: ctaText,
      },
    });
    currentTime = 25;
  }

  return {
    id,
    format,
    version: '1.0',
    created_at: new Date().toISOString(),
    settings: {
      resolution: FORMATS[format].resolution,
      fps: 30,
      duration_sec: currentTime,
      aspect_ratio: '9:16',
    },
    style: {
      theme,
      font_heading: 'Inter',
      font_body: 'Inter',
      ...themeConfig,
    },
    sections,
    audio: {
      volume_music: 0.3,
      volume_voice: 1.0,
    },
  };
}

/**
 * Validate a ContentBrief (basic validation matching schema.json rules).
 * @param {object} brief
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateBrief(brief) {
  const errors = [];
  if (!brief.id) errors.push('Missing required field: id');
  if (!brief.format) errors.push('Missing required field: format');
  else if (!FORMATS[brief.format]) errors.push(`Unknown format: ${brief.format}`);
  if (!brief.settings) errors.push('Missing required field: settings');
  else {
    if (!brief.settings.resolution) errors.push('Missing settings.resolution');
    if (!brief.settings.fps) errors.push('Missing settings.fps');
    if (!brief.settings.duration_sec) errors.push('Missing settings.duration_sec');
    if (!brief.settings.aspect_ratio) errors.push('Missing settings.aspect_ratio');
  }
  if (!brief.style) errors.push('Missing required field: style');
  if (!Array.isArray(brief.sections) || brief.sections.length === 0) errors.push('sections must be a non-empty array');
  return { valid: errors.length === 0, errors };
}

// ── Render ────────────────────────────────────────────────────────────────────

/**
 * Submit a render job. Saves brief JSON to disk then spawns the render CLI.
 * @param {object} brief
 * @param {object} options
 * @returns {string} jobId
 */
function submitRender(brief, options = {}) {
  const { quality = 'production', outputPath } = options;

  // Ensure directories
  fs.mkdirSync(BRIEFS_DIR, { recursive: true });
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const jobId = makeJobId();
  const briefPath = path.join(BRIEFS_DIR, `${jobId}.json`);
  const outPath = outputPath || path.join(OUTPUT_DIR, `${jobId}.mp4`);

  fs.writeFileSync(briefPath, JSON.stringify(brief, null, 2));

  const job = {
    id: jobId,
    briefId: brief.id,
    briefPath,
    outputPath: outPath,
    status: 'queued',
    progress: 0,
    startedAt: new Date().toISOString(),
    completedAt: null,
    error: null,
    quality,
    format: brief.format,
    title: brief.sections[0]?.content?.title || brief.id,
  };

  jobs.set(jobId, job);
  saveJobs();

  // Spawn render process
  const proc = spawn(
    'npx',
    ['tsx', 'scripts/render.ts', briefPath, outPath, '--quality', quality],
    {
      cwd: REMOTION_DIR,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
      env: { ...process.env, PATH: process.env.PATH || '/usr/local/bin:/usr/bin:/bin' },
    }
  );

  job.status = 'rendering';
  job.pid = proc.pid;
  saveJobs();

  let lastStdout = '';
  let lastStderr = '';
  proc.stdout.on('data', (chunk) => {
    lastStdout += chunk.toString();
    // Parse progress from output
    const match = lastStdout.match(/Rendering:\s+(\d+)%/);
    if (match) {
      job.progress = parseInt(match[1], 10);
      saveJobs();
    }
  });

  proc.stderr.on('data', (chunk) => {
    lastStderr += chunk.toString();
  });

  proc.on('close', (code) => {
    job.completedAt = new Date().toISOString();
    if (code === 0 && fs.existsSync(outPath)) {
      job.status = 'complete';
      job.progress = 100;
      const stat = fs.statSync(outPath);
      job.fileSizeBytes = stat.size;
    } else {
      const errDetail = lastStderr.slice(-1000) || lastStdout.slice(-500) || `exit code ${code}`;
      job.status = 'failed';
      job.error = `exit ${code}: ${errDetail}`;
    }
    delete job.pid;
    saveJobs();
  });

  proc.on('error', (err) => {
    job.status = 'failed';
    job.error = err.message;
    job.completedAt = new Date().toISOString();
    saveJobs();
  });

  return jobId;
}

// ── Still Render ─────────────────────────────────────────────────────────────

/**
 * Render a single frame from a ContentBrief as PNG.
 * Returns job object; rendering is async (check job status).
 * @param {object} brief
 * @param {object} opts
 * @returns {string} jobId
 */
function submitStillRender(brief, opts = {}) {
  const { frame = 0, format = 'png', outputPath } = opts;

  fs.mkdirSync(BRIEFS_DIR, { recursive: true });
  fs.mkdirSync(STILLS_DIR, { recursive: true });

  const jobId = makeJobId();
  const briefPath = path.join(BRIEFS_DIR, `${jobId}.json`);
  const ext = format === 'jpeg' ? 'jpg' : format;
  const outPath = outputPath || path.join(STILLS_DIR, `${jobId}.${ext}`);

  fs.writeFileSync(briefPath, JSON.stringify(brief, null, 2));

  const job = {
    id: jobId,
    type: 'still',
    briefId: brief.id,
    briefPath,
    outputPath: outPath,
    status: 'queued',
    progress: 0,
    frame,
    format,
    startedAt: new Date().toISOString(),
    completedAt: null,
    error: null,
    title: brief.sections[0]?.content?.title || brief.id,
  };

  jobs.set(jobId, job);
  saveJobs();

  const proc = spawn(
    'npx',
    ['tsx', 'scripts/render-brief-still.ts', briefPath, outPath, String(frame)],
    { cwd: REMOTION_DIR, stdio: ['ignore', 'pipe', 'pipe'], detached: false }
  );

  job.status = 'rendering';
  job.pid = proc.pid;
  saveJobs();

  let lastOutput = '';
  proc.stdout.on('data', (c) => { lastOutput += c.toString(); });
  proc.stderr.on('data', () => {});

  proc.on('close', (code) => {
    job.completedAt = new Date().toISOString();
    if (code === 0 && fs.existsSync(outPath)) {
      job.status = 'complete';
      job.progress = 100;
      job.fileSizeBytes = fs.statSync(outPath).size;
    } else {
      job.status = 'failed';
      job.error = lastOutput.slice(-500) || `exit code ${code}`;
    }
    delete job.pid;
    saveJobs();
  });

  proc.on('error', (err) => {
    job.status = 'failed';
    job.error = err.message;
    job.completedAt = new Date().toISOString();
    saveJobs();
  });

  return jobId;
}

// ── Voice Clone (Modal) ───────────────────────────────────────────────────────

/**
 * Generate voiceover using Modal voice clone API (not ElevenLabs).
 * @param {object} opts
 * @param {string} opts.text - Script text to synthesize
 * @param {string} [opts.referenceAudio] - Path to reference WAV file
 * @param {string} [opts.speakerName] - Speaker ID for caching
 * @param {string} opts.outputPath - Where to save the .wav
 * @returns {Promise<string>} outputPath on success
 */
async function generateVoiceover(opts) {
  const modalUrl = process.env.MODAL_VOICE_CLONE_URL;
  if (!modalUrl) {
    throw new Error('MODAL_VOICE_CLONE_URL not set. Deploy ai-video-platform/scripts/modal_voice_clone.py first.');
  }

  const refPath = opts.referenceAudio ||
    path.join(REMOTION_DIR, 'public', 'assets', 'voices', 'isaiah.wav');

  if (!fs.existsSync(refPath)) {
    throw new Error(`Reference audio not found: ${refPath}`);
  }

  const audioBuffer = fs.readFileSync(refPath);
  const referenceAudioBase64 = audioBuffer.toString('base64');

  const body = JSON.stringify({
    text: opts.text,
    reference_audio_base64: referenceAudioBase64,
    speaker_name: opts.speakerName || 'isaiah',
    speed: opts.speed || 1.0,
    temperature: opts.temperature || 0.7,
  });

  const parsedUrl = new URL(modalUrl);
  const isHttps = parsedUrl.protocol === 'https:';
  const reqModule = isHttps ? https : http;

  return new Promise((resolve, reject) => {
    const controller = { aborted: false };
    const timeoutId = setTimeout(() => {
      controller.aborted = true;
      reject(new Error('Voice clone request timed out after 120s'));
    }, 120000);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = reqModule.request(options, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        clearTimeout(timeoutId);
        if (controller.aborted) return;
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            return reject(new Error(`Voice clone API error: ${parsed.error}`));
          }
          if (!parsed.audio) {
            return reject(new Error(`Voice clone API returned no audio. Response: ${data.slice(0, 200)}`));
          }
          const audioOut = Buffer.from(parsed.audio, 'base64');
          fs.mkdirSync(path.dirname(opts.outputPath), { recursive: true });
          fs.writeFileSync(opts.outputPath, audioOut);
          resolve(opts.outputPath);
        } catch (e) {
          reject(new Error(`Failed to parse voice clone response: ${e.message}`));
        }
      });
    });

    req.on('error', (e) => {
      clearTimeout(timeoutId);
      reject(new Error(`Voice clone request failed: ${e.message}`));
    });
    req.write(body);
    req.end();
  });
}

// ── Telegram ──────────────────────────────────────────────────────────────────

/**
 * Send a file or text message to Telegram via Bot API.
 * @param {object} opts
 * @param {string} [opts.imagePath] - Local file path to send as photo
 * @param {string} [opts.videoPath] - Local file path to send as video (MP4)
 * @param {string} [opts.caption] - Caption text
 * @param {string} [opts.text] - Plain text message (if no imagePath/videoPath)
 * @param {string} [opts.chatId] - Override chat ID
 * @returns {Promise<object>}
 */
function sendTelegram(opts) {
  return new Promise((resolve, reject) => {
    const token = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = opts.chatId || process.env.TELEGRAM_CHAT_ID;

    if (!token) return reject(new Error('TELEGRAM_BOT_TOKEN not set'));
    if (!chatId) return reject(new Error('TELEGRAM_CHAT_ID not set'));

    if (opts.videoPath) {
      // sendVideo via multipart/form-data
      if (!fs.existsSync(opts.videoPath)) {
        return reject(new Error(`Video not found: ${opts.videoPath}`));
      }

      const fileBuffer = fs.readFileSync(opts.videoPath);
      const filename = path.basename(opts.videoPath);
      const boundary = `----FormBoundary${crypto.randomBytes(8).toString('hex')}`;

      const parts = [];
      parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n${chatId}\r\n`));
      if (opts.caption) {
        parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n${opts.caption}\r\n`));
      }
      parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="video"; filename="${filename}"\r\nContent-Type: video/mp4\r\n\r\n`));
      parts.push(fileBuffer);
      parts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

      const body = Buffer.concat(parts);

      const options = {
        hostname: 'api.telegram.org',
        port: 443,
        path: `/bot${token}/sendVideo`,
        method: 'POST',
        headers: {
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
          'Content-Length': body.length,
        },
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (c) => { data += c; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.ok) resolve({ ok: true, message_id: parsed.result?.message_id });
            else reject(new Error(`Telegram API error: ${parsed.description}`));
          } catch {
            reject(new Error(`Invalid Telegram response: ${data.slice(0, 200)}`));
          }
        });
      });
      req.on('error', reject);
      req.write(body);
      req.end();

    } else if (opts.imagePath) {
      // sendPhoto via multipart/form-data
      if (!fs.existsSync(opts.imagePath)) {
        return reject(new Error(`Image not found: ${opts.imagePath}`));
      }

      const fileBuffer = fs.readFileSync(opts.imagePath);
      const filename = path.basename(opts.imagePath);
      const boundary = `----FormBoundary${crypto.randomBytes(8).toString('hex')}`;

      const parts = [];
      // chat_id field
      parts.push(
        Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n${chatId}\r\n`)
      );
      // caption field
      if (opts.caption) {
        parts.push(
          Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n${opts.caption}\r\n`)
        );
      }
      // photo file
      parts.push(
        Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="photo"; filename="${filename}"\r\nContent-Type: image/png\r\n\r\n`)
      );
      parts.push(fileBuffer);
      parts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

      const body = Buffer.concat(parts);

      const options = {
        hostname: 'api.telegram.org',
        port: 443,
        path: `/bot${token}/sendPhoto`,
        method: 'POST',
        headers: {
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
          'Content-Length': body.length,
        },
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (c) => { data += c; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.ok) resolve({ ok: true, message_id: parsed.result?.message_id });
            else reject(new Error(`Telegram API error: ${parsed.description}`));
          } catch {
            reject(new Error(`Invalid Telegram response: ${data.slice(0, 200)}`));
          }
        });
      });
      req.on('error', reject);
      req.write(body);
      req.end();

    } else {
      // sendMessage
      const body = JSON.stringify({ chat_id: chatId, text: opts.text || '(no message)' });
      const options = {
        hostname: 'api.telegram.org',
        port: 443,
        path: `/bot${token}/sendMessage`,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      };
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (c) => { data += c; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.ok) resolve({ ok: true, message_id: parsed.result?.message_id });
            else reject(new Error(`Telegram API error: ${parsed.description}`));
          } catch {
            reject(new Error(`Invalid Telegram response: ${data.slice(0, 200)}`));
          }
        });
      });
      req.on('error', reject);
      req.write(body);
      req.end();
    }
  });
}

// ── Tool Handlers ─────────────────────────────────────────────────────────────

function listFormats() {
  return Object.entries(FORMATS).map(([id, f]) => ({
    id,
    name: f.name,
    description: f.description,
    aspectRatio: f.aspectRatio,
    resolution: f.resolution,
    sectionTypes: f.sections,
  }));
}

function listOutputFiles() {
  if (!fs.existsSync(OUTPUT_DIR)) return [];
  return fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.endsWith('.mp4'))
    .map(f => {
      const fp = path.join(OUTPUT_DIR, f);
      const stat = fs.statSync(fp);
      return {
        filename: f,
        path: fp,
        sizeBytes: stat.size,
        sizeMB: Math.round(stat.size / 1024 / 1024 * 10) / 10,
        modifiedAt: stat.mtime.toISOString(),
      };
    })
    .sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt));
}

function listRecentJobs(limit = 20) {
  return Array.from(jobs.values())
    .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))
    .slice(0, limit)
    .map(j => ({
      id: j.id,
      status: j.status,
      progress: j.progress,
      format: j.format,
      title: j.title,
      outputPath: j.outputPath,
      fileSizeBytes: j.fileSizeBytes,
      startedAt: j.startedAt,
      completedAt: j.completedAt,
      error: j.error,
    }));
}

// ── MCP Protocol ──────────────────────────────────────────────────────────────

const TOOL_DEFS = [
  {
    name: 'remotion_list_formats',
    description: 'List all available Remotion video formats with descriptions, section types, and resolution. Use this to pick the right format before generating a brief.',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'remotion_generate_brief',
    description: 'Generate a ContentBrief JSON from simple inputs (title, topics, format). Returns a ready-to-use brief that can be passed to remotion_render.',
    inputSchema: {
      type: 'object',
      required: ['title'],
      properties: {
        title: { type: 'string', description: 'Video title / main hook' },
        subtitle: { type: 'string', description: 'Optional subtitle text' },
        hookText: { type: 'string', description: 'Hook text shown in intro (problem statement)' },
        format: {
          type: 'string',
          enum: ['explainer_v1', 'listicle_v1', 'comparison_v1', 'shorts_v1'],
          description: 'Video format. Default: explainer_v1',
        },
        theme: {
          type: 'string',
          enum: ['dark', 'light', 'neon'],
          description: 'Visual theme. Default: dark',
        },
        topics: {
          type: 'array',
          description: 'Topic slides for explainer format. Each item: string or {heading, body_text, bullet_points, icon}',
          items: {},
        },
        listItems: {
          type: 'array',
          description: 'Numbered items for listicle format. Each item: string or {title, description}',
          items: {},
        },
        ctaText: { type: 'string', description: 'Call-to-action text in outro. Default: "Follow for more"' },
        ctaHandle: { type: 'string', description: 'Social handle shown in outro (e.g. @isaiahdupree)' },
        accentColor: { type: 'string', description: 'Hex accent color override (e.g. #ff6b00)' },
        durationPerTopic: { type: 'number', description: 'Seconds per topic/list item. Default: 8' },
        leftItem: {
          type: 'object',
          description: 'Left side for comparison format: {label, points: []}',
        },
        rightItem: {
          type: 'object',
          description: 'Right side for comparison format: {label, points: []}',
        },
      },
    },
  },
  {
    name: 'remotion_validate_brief',
    description: 'Validate a ContentBrief JSON before rendering. Returns {valid, errors}.',
    inputSchema: {
      type: 'object',
      required: ['brief'],
      properties: {
        brief: { type: 'object', description: 'ContentBrief JSON to validate' },
      },
    },
  },
  {
    name: 'remotion_render',
    description: 'Submit a video render job. Accepts a ContentBrief JSON. Returns job_id for status polling. Render runs in background (typically 2-5 min).',
    inputSchema: {
      type: 'object',
      required: ['brief'],
      properties: {
        brief: { type: 'object', description: 'ContentBrief JSON (use remotion_generate_brief to create one)' },
        quality: {
          type: 'string',
          enum: ['preview', 'production'],
          description: 'Render quality. preview is faster (lower CRF). Default: production',
        },
        outputPath: { type: 'string', description: 'Optional absolute output path (default: output/<job_id>.mp4)' },
      },
    },
  },
  {
    name: 'remotion_job_status',
    description: 'Check the status of a Remotion render job by job_id.',
    inputSchema: {
      type: 'object',
      required: ['jobId'],
      properties: {
        jobId: { type: 'string', description: 'Job ID returned by remotion_render' },
      },
    },
  },
  {
    name: 'remotion_list_jobs',
    description: 'List recent render jobs with their status, progress, output paths, and file sizes.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Max jobs to return (default: 20)' },
      },
    },
  },
  {
    name: 'remotion_list_outputs',
    description: 'List rendered MP4 files in the output directory.',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'remotion_render_still',
    description: 'Render a single still frame (PNG/JPEG) from a ContentBrief. Much faster than full video render. Use for ad images, preview frames, or Telegram previews. Returns job_id — poll with remotion_job_status.',
    inputSchema: {
      type: 'object',
      required: ['brief'],
      properties: {
        brief: { type: 'object', description: 'ContentBrief JSON (use remotion_generate_brief to create one)' },
        frame: { type: 'number', description: 'Frame number to render (default: 0 = first frame)' },
        format: {
          type: 'string',
          enum: ['png', 'jpeg'],
          description: 'Image format. Default: png',
        },
        outputPath: { type: 'string', description: 'Optional absolute output path (default: output/stills/<job_id>.png)' },
      },
    },
  },
  {
    name: 'remotion_render_thumbnail_cloud',
    description: 'Render a YouTube thumbnail (1280×720 PNG) on Modal cloud using YouTubeThumbnailBrief. Uploads to Supabase Storage and returns a public URL. No local Chrome needed. Faster than local render. Use this instead of remotion_render_still for YouTube thumbnails.',
    inputSchema: {
      type: 'object',
      required: ['brief'],
      properties: {
        brief: {
          type: 'object',
          description: 'YouTubeThumbnailBrief: {title, subtitle?, highlight?, highlight_label?, podcast_name?, episode_label?, speaker_name?, speaker_title?, cta_handle?, accent?, style?}',
        },
        output_filename: { type: 'string', description: 'Optional output filename (auto-generated if omitted)' },
      },
    },
  },
  {
    name: 'remotion_render_modal',
    description: 'Render a Remotion composition on Modal (cloud GPU/CPU) and upload result to Supabase Storage. Returns a public URL immediately after upload. Faster than local render for long videos, no local Chrome required. Uses modal_remotion_render.py endpoint.',
    inputSchema: {
      type: 'object',
      required: ['composition'],
      properties: {
        composition: { type: 'string', description: 'Remotion composition ID (e.g. "UGCComposition", "EverReachReel")' },
        input_props: { type: 'object', description: 'Props to pass to the composition (same as inputProps in local render)' },
        quality: { type: 'string', enum: ['preview', 'production'], description: 'Render quality (default: production)' },
        output_filename: { type: 'string', description: 'Output MP4 filename (auto-generated if omitted)' },
      },
    },
  },
  {
    name: 'remotion_generate_voiceover',
    description: 'Generate a voiceover audio file using the Modal voice clone API (not ElevenLabs). Clones Isaiah\'s voice by default. Requires MODAL_VOICE_CLONE_URL env var. Returns the path to the generated WAV file.',
    inputSchema: {
      type: 'object',
      required: ['text'],
      properties: {
        text: { type: 'string', description: 'Script text to synthesize into speech' },
        referenceAudio: { type: 'string', description: 'Absolute path to reference WAV file (default: public/assets/voices/isaiah.wav)' },
        speakerName: { type: 'string', description: 'Speaker ID for caching (default: isaiah)' },
        outputPath: { type: 'string', description: 'Where to save the .wav (default: output/voiceovers/<timestamp>.wav)' },
        speed: { type: 'number', description: 'Speech speed multiplier 0.5-2.0 (default: 1.0)' },
        temperature: { type: 'number', description: 'Sampling temperature 0.1-1.0 (default: 0.7)' },
      },
    },
  },
  {
    name: 'remotion_send_telegram',
    description: 'Send a video, image, or text message to Telegram for review. Supports MP4 videos from render jobs. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars (auto-loaded from actp-worker .env).',
    inputSchema: {
      type: 'object',
      properties: {
        videoPath: { type: 'string', description: 'Absolute path to MP4 video file to send as video' },
        imagePath: { type: 'string', description: 'Absolute path to image file (PNG/JPEG) to send as photo' },
        jobId: { type: 'string', description: 'Job ID from remotion_render or remotion_render_still — auto-detects MP4 vs image' },
        caption: { type: 'string', description: 'Caption text to show under the media' },
        text: { type: 'string', description: 'Plain text message (used when no media path/jobId provided)' },
        chatId: { type: 'string', description: 'Override chat ID (default: TELEGRAM_CHAT_ID env var)' },
      },
    },
  },
  // ── TikTok Pipeline Tools ──────────────────────────────────────────────────
  {
    name: 'tiktok_render',
    description: 'Render a TikTok video using the TikTok pipeline (from remotion-tiktok-pipeline). Accepts a TikTok brief JSON with hook, body points, phone frame, and outro sections. Supports 5 themes: dark, tiktok, everreach, neon, minimal.',
    inputSchema: {
      type: 'object',
      required: ['brief'],
      properties: {
        brief: { type: 'object', description: 'TikTok ContentBrief JSON with hook_text, body_points, theme, etc.' },
        quality: { type: 'string', enum: ['preview', 'production'], description: 'Render quality (default: production)' },
        outputPath: { type: 'string', description: 'Optional output path' },
      },
    },
  },
  {
    name: 'tiktok_list_briefs',
    description: 'List available TikTok brief templates in data/briefs/tiktok/. These can be used as starting points for tiktok_render.',
    inputSchema: { type: 'object', properties: {} },
  },
  // ── AI Content Pipeline Tools ──────────────────────────────────────────────
  {
    name: 'pipeline_research',
    description: 'Research a topic using Perplexity API. Returns facts, statistics, quotes with sources. Results are cached for 24h. Requires PERPLEXITY_API_KEY env var.',
    inputSchema: {
      type: 'object',
      required: ['topic'],
      properties: {
        topic: { type: 'string', description: 'Topic to research (e.g. "AI video generation trends 2026")' },
        platform: { type: 'string', enum: ['youtube', 'tiktok', 'instagram', 'linkedin'], description: 'Target platform for research focus' },
      },
    },
  },
  {
    name: 'pipeline_generate_script',
    description: 'Generate a video script using Claude AI from a topic and optional research. Returns hook, body points, CTA, and word-level timing. Requires ANTHROPIC_API_KEY env var.',
    inputSchema: {
      type: 'object',
      required: ['topic'],
      properties: {
        topic: { type: 'string', description: 'Topic for the video script' },
        platform: { type: 'string', enum: ['youtube', 'tiktok', 'instagram', 'linkedin'], description: 'Target platform' },
        tone: { type: 'string', description: 'Tone of voice (e.g. casual, professional, energetic)' },
        targetLength: { type: 'number', description: 'Target duration in seconds (default: 60)' },
        researchId: { type: 'string', description: 'Research ID from pipeline_research to incorporate stats/quotes' },
      },
    },
  },
  {
    name: 'pipeline_generate_voiceover',
    description: 'Generate voiceover using ElevenLabs TTS. Supports long scripts with auto-splitting. Requires ELEVENLABS_API_KEY env var.',
    inputSchema: {
      type: 'object',
      required: ['text'],
      properties: {
        text: { type: 'string', description: 'Script text to synthesize' },
        voiceId: { type: 'string', description: 'ElevenLabs voice ID (default: Adam)' },
        speed: { type: 'number', description: 'Speech speed 0.25-4.0 (default: 1.0)' },
        outputPath: { type: 'string', description: 'Output file path' },
      },
    },
  },
  {
    name: 'pipeline_full_run',
    description: 'Run the full content pipeline: Research → Script → Voiceover → Render → (optional) Publish. Orchestrates all steps automatically. Returns a pipeline run ID for status polling.',
    inputSchema: {
      type: 'object',
      required: ['topic'],
      properties: {
        topic: { type: 'string', description: 'Topic for the video' },
        platforms: {
          type: 'array',
          items: { type: 'string', enum: ['youtube', 'tiktok', 'instagram', 'linkedin'] },
          description: 'Target platforms (default: ["tiktok"])',
        },
        tone: { type: 'string', description: 'Tone of voice' },
        duration: { type: 'number', description: 'Target duration in seconds' },
        publish: { type: 'boolean', description: 'Whether to publish after rendering (default: false)' },
      },
    },
  },
  // ── Python Services Tools ──────────────────────────────────────────────────
  {
    name: 'services_status',
    description: 'Check the status of Python microservices (music analysis, text overlay, video generator, Google Drive). Shows which Docker services are running.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'services_start',
    description: 'Start the Python microservices via Docker Compose. Services: music-analysis (port 5001), text-overlay, video-generator, google-drive (port 5000).',
    inputSchema: {
      type: 'object',
      properties: {
        services: {
          type: 'array',
          items: { type: 'string', enum: ['music-analysis', 'text-overlay', 'video-generator', 'google-drive'] },
          description: 'Specific services to start (default: all)',
        },
      },
    },
  },
  {
    name: 'services_music_match',
    description: 'Find the best background music for a video using AI music matching. Analyzes video mood, energy, and genre to recommend tracks from the music library.',
    inputSchema: {
      type: 'object',
      required: ['videoPath'],
      properties: {
        videoPath: { type: 'string', description: 'Path to the video file to match music for' },
        mood: { type: 'string', description: 'Optional mood hint (happy, sad, energetic, calm)' },
        genre: { type: 'string', description: 'Optional genre preference' },
      },
    },
  },
  {
    name: 'services_text_overlay',
    description: 'Add smart text overlay to a video. Uses AI to generate text and find optimal placement avoiding faces/UI elements. Uses Whisper for transcription and YOLO for detection.',
    inputSchema: {
      type: 'object',
      required: ['videoPath'],
      properties: {
        videoPath: { type: 'string', description: 'Path to the input video' },
        text: { type: 'string', description: 'Text to overlay (auto-generated if not provided)' },
        style: { type: 'string', enum: ['TechMeStuff', 'Minimalist', 'Dramatic', 'Professional'], description: 'Font style preset' },
        outputPath: { type: 'string', description: 'Output file path' },
      },
    },
  },
  // ── Composition Browser ────────────────────────────────────────────────────
  {
    name: 'remotion_list_compositions',
    description: 'List all available Remotion compositions across all merged projects (ai-video-platform, tiktok-pipeline, content-pipeline). Shows composition IDs you can use with remotion_render_modal.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'remotion_list_scenes',
    description: 'List all available scene templates (30+ scenes like HookScene, CTAScene, CompareScene, etc.) that can be composed into videos.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'remotion_list_animations',
    description: 'List all available animation presets (bounce, fadeIn, glitch, kinetic, typewriter, etc.) for use in compositions.',
    inputSchema: { type: 'object', properties: {} },
  },
  // ── Template Marketplace Tools ─────────────────────────────────────────────
  {
    name: 'marketplace_browse',
    description: 'Browse the Remotion template marketplace. Filter by category and sort by popularity, newest, rating, or price. Returns template listings with names, prices, ratings, and download counts.',
    inputSchema: {
      type: 'object',
      properties: {
        category: {
          type: 'string',
          enum: ['social-video', 'youtube', 'ads', 'presentations', 'podcast', 'ecommerce', 'automation', 'effects', 'brand-kits'],
          description: 'Filter by category',
        },
        sort: { type: 'string', enum: ['popular', 'newest', 'rating', 'price-low', 'price-high'], description: 'Sort order (default: popular)' },
        limit: { type: 'number', description: 'Max results (default: 20)' },
      },
    },
  },
  {
    name: 'marketplace_search',
    description: 'Search the template marketplace by keyword. Searches template names, descriptions, tags, and authors.',
    inputSchema: {
      type: 'object',
      required: ['query'],
      properties: {
        query: { type: 'string', description: 'Search query (e.g. "tiktok countdown", "UGC ads", "podcast clip")' },
      },
    },
  },
  {
    name: 'marketplace_details',
    description: 'Get full details for a specific template including description, pricing, reviews, technical requirements, and preview URLs.',
    inputSchema: {
      type: 'object',
      required: ['templateId'],
      properties: {
        templateId: { type: 'string', description: 'Template ID to look up' },
      },
    },
  },
  {
    name: 'marketplace_publish',
    description: 'Publish a Remotion template or automation to the marketplace for others to buy. Free templates are published immediately; paid templates require review. Include name, description, category, price, and technical details.',
    inputSchema: {
      type: 'object',
      required: ['name', 'description', 'category'],
      properties: {
        name: { type: 'string', description: 'Template name' },
        description: { type: 'string', description: 'Short description (max 200 chars)' },
        longDescription: { type: 'string', description: 'Full description with markdown' },
        category: { type: 'string', enum: ['social-video', 'youtube', 'ads', 'presentations', 'podcast', 'ecommerce', 'automation', 'effects', 'brand-kits'] },
        tags: { type: 'array', items: { type: 'string' }, description: 'Searchable tags' },
        price: { type: 'number', description: 'Price in cents (0 = free). e.g. 999 = $9.99' },
        license: { type: 'string', enum: ['free', 'personal', 'commercial', 'extended', 'open-source'], description: 'License type' },
        author: { type: 'string', description: 'Your display name' },
        compositions: { type: 'array', items: { type: 'string' }, description: 'Remotion composition IDs included' },
        mcpTools: { type: 'array', items: { type: 'string' }, description: 'MCP tool names included (for automations)' },
        dependencies: { type: 'array', items: { type: 'string' }, description: 'npm dependencies required' },
      },
    },
  },
  {
    name: 'marketplace_buy',
    description: 'Purchase or download a template from the marketplace. Free templates are added instantly. Paid templates initiate a Stripe checkout flow.',
    inputSchema: {
      type: 'object',
      required: ['templateId'],
      properties: {
        templateId: { type: 'string', description: 'Template ID to purchase' },
        buyerId: { type: 'string', description: 'Your user ID (default: "default")' },
      },
    },
  },
  {
    name: 'marketplace_my_templates',
    description: 'List your published templates with sales stats, revenue, ratings, and download counts.',
    inputSchema: {
      type: 'object',
      properties: {
        sellerId: { type: 'string', description: 'Your seller ID (default: "default")' },
      },
    },
  },
  {
    name: 'marketplace_my_purchases',
    description: 'List templates you have purchased or downloaded from the marketplace.',
    inputSchema: {
      type: 'object',
      properties: {
        buyerId: { type: 'string', description: 'Your user ID (default: "default")' },
      },
    },
  },
  {
    name: 'marketplace_review',
    description: 'Submit a review for a purchased template. Rate 1-5 stars with an optional title and description.',
    inputSchema: {
      type: 'object',
      required: ['templateId', 'rating'],
      properties: {
        templateId: { type: 'string', description: 'Template ID to review' },
        rating: { type: 'number', description: 'Rating 1-5 stars' },
        title: { type: 'string', description: 'Review title' },
        body: { type: 'string', description: 'Review text' },
        userName: { type: 'string', description: 'Your display name' },
      },
    },
  },
  {
    name: 'marketplace_categories',
    description: 'List all marketplace categories with descriptions. Use these when publishing or browsing templates.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'heygen_generate_avatar',
    description: 'Generate an AI avatar video via HeyGen API. The avatar speaks the given text. Returns a videoId that can be polled with heygen_video_status. Requires HEYGEN_API_KEY env var.',
    inputSchema: {
      type: 'object',
      required: ['text'],
      properties: {
        text: { type: 'string', description: 'Script text for the avatar to speak' },
        avatarId: { type: 'string', description: 'HeyGen avatar ID (default: Angela-inTshirt-20220820). Use heygen_list_avatars to see options.' },
        voiceId: { type: 'string', description: 'HeyGen voice ID (default: en-US-JennyNeural)' },
        style: { type: 'string', enum: ['normal', 'closeUp'], description: 'Avatar framing style (default: normal)' },
        width: { type: 'number', description: 'Video width in px (default: 1080)' },
        height: { type: 'number', description: 'Video height in px (default: 1920)' },
      },
    },
  },
  {
    name: 'heygen_list_avatars',
    description: 'List all available HeyGen avatars with their IDs and preview images. Requires HEYGEN_API_KEY env var.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'heygen_video_status',
    description: 'Check the status of a HeyGen avatar video generation. Returns status, video URL (when complete), caption URL, and duration.',
    inputSchema: {
      type: 'object',
      required: ['videoId'],
      properties: {
        videoId: { type: 'string', description: 'The video ID returned by heygen_generate_avatar' },
      },
    },
  },
];

async function handleTool(name, args) {
  switch (name) {
    case 'remotion_list_formats':
      return { content: [{ type: 'text', text: JSON.stringify(listFormats(), null, 2) }] };

    case 'remotion_generate_brief': {
      try {
        const brief = generateBrief(args);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({ success: true, brief }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ success: false, error: err.message }) }],
          isError: true,
        };
      }
    }

    case 'remotion_validate_brief': {
      const result = validateBrief(args.brief || {});
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }

    case 'remotion_render_modal': {
      const { composition, input_props = {}, quality = 'production', output_filename } = args;
      if (!composition) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'composition is required' }) }], isError: true };
      }

      // Get Modal endpoint URL from env or derive from known pattern
      const modalUrl = process.env.MODAL_REMOTION_RENDER_URL ||
        'https://isaiahdupree33--remotion-render-endpoint.modal.run';

      let response, result;
      try {
        response = await fetch(modalUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ composition, input_props, quality, output_filename }),
          signal: AbortSignal.timeout(3600_000), // 1 hour
        });
        result = await response.json();
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: `Modal request failed: ${err.message}` }) }],
          isError: true,
        };
      }

      if (!response.ok || result.error) {
        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
          isError: true,
        };
      }

      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }

    case 'remotion_render_thumbnail_cloud': {
      const { brief, output_filename } = args;
      if (!brief) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'brief is required' }) }], isError: true };
      }

      const thumbnailUrl = process.env.MODAL_REMOTION_THUMBNAIL_URL ||
        'https://isaiahdupree33--remotion-thumbnail.modal.run';

      let response, result;
      try {
        response = await fetch(thumbnailUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brief, output_filename }),
          signal: AbortSignal.timeout(300_000),
        });
        result = await response.json();
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }

      if (!response.ok || result.error) {
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }], isError: true };
      }

      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }

    case 'remotion_render': {
      const { brief, quality, outputPath } = args;
      if (!brief) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: 'brief is required' }) }],
          isError: true,
        };
      }
      const validation = validateBrief(brief);
      if (!validation.valid) {
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({ error: 'Invalid brief', errors: validation.errors }),
          }],
          isError: true,
        };
      }
      try {
        const jobId = submitRender(brief, { quality, outputPath });
        const job = jobs.get(jobId);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              jobId,
              status: job.status,
              outputPath: job.outputPath,
              message: 'Render started. Use remotion_job_status to check progress.',
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
          isError: true,
        };
      }
    }

    case 'remotion_job_status': {
      const job = jobs.get(args.jobId);
      if (!job) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: `Job not found: ${args.jobId}` }) }],
          isError: true,
        };
      }
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            id: job.id,
            status: job.status,
            progress: job.progress,
            format: job.format,
            title: job.title,
            outputPath: job.outputPath,
            fileSizeBytes: job.fileSizeBytes,
            fileSizeMB: job.fileSizeBytes ? Math.round(job.fileSizeBytes / 1024 / 1024 * 10) / 10 : null,
            startedAt: job.startedAt,
            completedAt: job.completedAt,
            error: job.error,
          }, null, 2),
        }],
      };
    }

    case 'remotion_list_jobs': {
      const jobList = listRecentJobs(args.limit || 20);
      return { content: [{ type: 'text', text: JSON.stringify(jobList, null, 2) }] };
    }

    case 'remotion_list_outputs': {
      const files = listOutputFiles();
      return { content: [{ type: 'text', text: JSON.stringify(files, null, 2) }] };
    }

    case 'remotion_render_still': {
      const { brief, frame, format, outputPath } = args;
      if (!brief) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: 'brief is required' }) }],
          isError: true,
        };
      }
      const validation = validateBrief(brief);
      if (!validation.valid) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: 'Invalid brief', errors: validation.errors }) }],
          isError: true,
        };
      }
      try {
        const jobId = submitStillRender(brief, { frame, format, outputPath });
        const job = jobs.get(jobId);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              jobId,
              status: job.status,
              outputPath: job.outputPath,
              message: 'Still render started. Use remotion_job_status to check progress, then remotion_send_telegram to preview.',
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
          isError: true,
        };
      }
    }

    case 'remotion_generate_voiceover': {
      const { text: voText, referenceAudio, speakerName, outputPath: voOutPath, speed, temperature } = args;
      if (!voText) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: 'text is required' }) }],
          isError: true,
        };
      }
      const defaultOut = path.join(OUTPUT_DIR, 'voiceovers', `vo_${Date.now()}.wav`);
      try {
        const savedPath = await generateVoiceover({
          text: voText,
          referenceAudio,
          speakerName,
          outputPath: voOutPath || defaultOut,
          speed,
          temperature,
        });
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              outputPath: savedPath,
              message: 'Voiceover generated via Modal voice clone API. Add the path to your brief audio.voiceover_path field.',
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
          isError: true,
        };
      }
    }

    case 'remotion_send_telegram': {
      const { videoPath, imagePath, jobId: sendJobId, caption, text, chatId } = args;

      // Resolve media path from job if jobId provided
      let resolvedVideoPath = videoPath;
      let resolvedImagePath = imagePath;
      if (!resolvedVideoPath && !resolvedImagePath && sendJobId) {
        const job = jobs.get(sendJobId);
        if (!job) {
          return {
            content: [{ type: 'text', text: JSON.stringify({ error: `Job not found: ${sendJobId}` }) }],
            isError: true,
          };
        }
        if (job.status !== 'complete') {
          return {
            content: [{ type: 'text', text: JSON.stringify({ error: `Job not ready: status=${job.status}`, progress: job.progress }) }],
            isError: true,
          };
        }
        // Auto-detect: MP4 → video, everything else → image
        if (job.outputPath && job.outputPath.endsWith('.mp4')) {
          resolvedVideoPath = job.outputPath;
        } else {
          resolvedImagePath = job.outputPath;
        }
      }

      try {
        const result = await sendTelegram({ videoPath: resolvedVideoPath, imagePath: resolvedImagePath, caption, text, chatId });
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              message_id: result.message_id,
              sent: resolvedVideoPath || resolvedImagePath || '(text message)',
              type: resolvedVideoPath ? 'video' : resolvedImagePath ? 'photo' : 'text',
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
          isError: true,
        };
      }
    }

    // ── TikTok Pipeline Handlers ──────────────────────────────────────────────
    case 'tiktok_render': {
      const { brief, quality = 'production', outputPath } = args;
      if (!brief) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'brief is required' }) }], isError: true };
      }
      const jobId = makeJobId();
      const briefPath = path.join(BRIEFS_DIR, `${jobId}.json`);
      const outPath = outputPath || path.join(OUTPUT_DIR, `${jobId}.mp4`);
      fs.mkdirSync(BRIEFS_DIR, { recursive: true });
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
      fs.writeFileSync(briefPath, JSON.stringify(brief, null, 2));

      const job = {
        id: jobId, type: 'tiktok', briefPath, outputPath: outPath,
        status: 'rendering', progress: 0, startedAt: new Date().toISOString(),
        completedAt: null, error: null, quality, format: brief.format || 'tiktok_v1',
        title: brief.hook_text || brief.id || jobId,
      };
      jobs.set(jobId, job);
      saveJobs();

      const proc = spawn('npx', ['tsx', 'scripts/render-tiktok.ts', briefPath, outPath, '--quality', quality], {
        cwd: REMOTION_DIR, stdio: ['ignore', 'pipe', 'pipe'], detached: false,
      });
      proc.stdout.on('data', (c) => {
        const m = c.toString().match(/Rendering:\s+(\d+)%/);
        if (m) { job.progress = parseInt(m[1], 10); saveJobs(); }
      });
      proc.on('close', (code) => {
        job.completedAt = new Date().toISOString();
        if (code === 0 && fs.existsSync(outPath)) {
          job.status = 'complete'; job.progress = 100;
          job.fileSizeBytes = fs.statSync(outPath).size;
        } else { job.status = 'failed'; job.error = `exit code ${code}`; }
        delete job.pid; saveJobs();
      });
      proc.on('error', (err) => { job.status = 'failed'; job.error = err.message; saveJobs(); });

      return { content: [{ type: 'text', text: JSON.stringify({ success: true, jobId, status: 'rendering', outputPath: outPath, message: 'TikTok render started. Use remotion_job_status to check progress.' }, null, 2) }] };
    }

    case 'tiktok_list_briefs': {
      const briefsDir = path.join(REMOTION_DIR, 'data', 'briefs', 'tiktok');
      if (!fs.existsSync(briefsDir)) return { content: [{ type: 'text', text: '[]' }] };
      const briefs = fs.readdirSync(briefsDir).filter(f => f.endsWith('.json')).map(f => {
        try {
          const data = JSON.parse(fs.readFileSync(path.join(briefsDir, f), 'utf8'));
          return { filename: f, id: data.id, hook: data.hook_text || data.sections?.[0]?.content?.hook_text, format: data.format };
        } catch { return { filename: f, error: 'parse error' }; }
      });
      return { content: [{ type: 'text', text: JSON.stringify(briefs, null, 2) }] };
    }

    // ── AI Content Pipeline Handlers ──────────────────────────────────────────
    case 'pipeline_research': {
      const { topic, platform = 'tiktok' } = args;
      if (!topic) return { content: [{ type: 'text', text: JSON.stringify({ error: 'topic is required' }) }], isError: true };
      if (!process.env.PERPLEXITY_API_KEY) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'PERPLEXITY_API_KEY not set. Add it to .env' }) }], isError: true };
      }
      try {
        const body = JSON.stringify({
          model: 'sonar-medium-online',
          messages: [
            { role: 'system', content: `You are a research assistant for ${platform} video content. Extract key facts, statistics, and quotable insights.` },
            { role: 'user', content: `Research this topic thoroughly for a ${platform} video: "${topic}". Return: 1) 5 key facts, 2) 3 statistics with sources, 3) 2 expert quotes.` }
          ],
        });
        const response = await fetch('https://api.perplexity.ai/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}` },
          body,
          signal: AbortSignal.timeout(30000),
        });
        const result = await response.json();
        const researchId = `research_${Date.now()}`;
        const researchPath = path.join(OUTPUT_DIR, 'research', `${researchId}.json`);
        fs.mkdirSync(path.dirname(researchPath), { recursive: true });
        fs.writeFileSync(researchPath, JSON.stringify({ id: researchId, topic, platform, result, createdAt: new Date().toISOString() }, null, 2));
        return { content: [{ type: 'text', text: JSON.stringify({ success: true, researchId, topic, content: result.choices?.[0]?.message?.content || 'No content returned' }, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'pipeline_generate_script': {
      const { topic, platform = 'tiktok', tone = 'engaging', targetLength = 60, researchId } = args;
      if (!topic) return { content: [{ type: 'text', text: JSON.stringify({ error: 'topic is required' }) }], isError: true };
      const apiKey = process.env.ANTHROPIC_API_KEY;
      if (!apiKey) return { content: [{ type: 'text', text: JSON.stringify({ error: 'ANTHROPIC_API_KEY not set' }) }], isError: true };

      let researchContext = '';
      if (researchId) {
        const rPath = path.join(OUTPUT_DIR, 'research', `${researchId}.json`);
        if (fs.existsSync(rPath)) {
          const rData = JSON.parse(fs.readFileSync(rPath, 'utf8'));
          researchContext = `\n\nResearch findings:\n${rData.result?.choices?.[0]?.message?.content || ''}`;
        }
      }

      try {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
          body: JSON.stringify({
            model: 'claude-sonnet-4-20250514',
            max_tokens: 2000,
            messages: [{
              role: 'user',
              content: `Write a ${platform} video script about "${topic}". Tone: ${tone}. Target: ${targetLength}s (~${Math.round(targetLength * 2.5)} words).${researchContext}

Return JSON with: { "hook": "opening hook text", "body_points": ["point 1", "point 2", "point 3"], "cta": "call to action", "full_script": "complete narration script", "estimated_duration_sec": number }`
            }],
          }),
          signal: AbortSignal.timeout(60000),
        });
        const result = await response.json();
        const scriptText = result.content?.[0]?.text || '';
        const scriptId = `script_${Date.now()}`;
        const scriptPath = path.join(OUTPUT_DIR, 'scripts', `${scriptId}.json`);
        fs.mkdirSync(path.dirname(scriptPath), { recursive: true });
        fs.writeFileSync(scriptPath, JSON.stringify({ id: scriptId, topic, platform, tone, raw: scriptText, createdAt: new Date().toISOString() }, null, 2));

        return { content: [{ type: 'text', text: JSON.stringify({ success: true, scriptId, topic, script: scriptText }, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'pipeline_generate_voiceover': {
      const { text: voText, voiceId, speed = 1.0, outputPath: voOut } = args;
      if (!voText) return { content: [{ type: 'text', text: JSON.stringify({ error: 'text is required' }) }], isError: true };
      const elevenKey = process.env.ELEVENLABS_API_KEY;
      if (!elevenKey) return { content: [{ type: 'text', text: JSON.stringify({ error: 'ELEVENLABS_API_KEY not set' }) }], isError: true };

      const voice = voiceId || 'pNInz6obpgDQGcFmaJgB'; // Adam
      const outPath = voOut || path.join(OUTPUT_DIR, 'voiceovers', `vo_${Date.now()}.mp3`);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });

      try {
        const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'xi-api-key': elevenKey },
          body: JSON.stringify({
            text: voText,
            model_id: 'eleven_monolingual_v1',
            voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.0, use_speaker_boost: true },
          }),
          signal: AbortSignal.timeout(120000),
        });

        if (!response.ok) {
          const errText = await response.text();
          return { content: [{ type: 'text', text: JSON.stringify({ error: `ElevenLabs error: ${response.status} ${errText}` }) }], isError: true };
        }

        const audioBuffer = Buffer.from(await response.arrayBuffer());
        fs.writeFileSync(outPath, audioBuffer);
        return { content: [{ type: 'text', text: JSON.stringify({ success: true, outputPath: outPath, sizeBytes: audioBuffer.length, message: 'Voiceover generated via ElevenLabs.' }, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'pipeline_full_run': {
      const { topic, platforms = ['tiktok'], tone = 'engaging', duration = 60, publish = false } = args;
      if (!topic) return { content: [{ type: 'text', text: JSON.stringify({ error: 'topic is required' }) }], isError: true };

      const pipelineId = `pipeline_${Date.now()}_${crypto.randomBytes(3).toString('hex')}`;
      const pipelinePath = path.join(OUTPUT_DIR, 'pipelines', `${pipelineId}.json`);
      fs.mkdirSync(path.dirname(pipelinePath), { recursive: true });

      const pipeline = {
        id: pipelineId, topic, platforms, tone, duration, publish,
        status: 'started', steps: [], startedAt: new Date().toISOString(),
      };
      fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));

      // Run pipeline steps asynchronously
      (async () => {
        try {
          // Step 1: Research
          pipeline.status = 'researching';
          pipeline.steps.push({ step: 'research', status: 'running', startedAt: new Date().toISOString() });
          fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));

          const researchResult = await handleTool('pipeline_research', { topic, platform: platforms[0] });
          pipeline.steps[0].status = 'complete';
          pipeline.steps[0].result = JSON.parse(researchResult.content[0].text);

          // Step 2: Script
          pipeline.status = 'scripting';
          pipeline.steps.push({ step: 'script', status: 'running', startedAt: new Date().toISOString() });
          fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));

          const scriptResult = await handleTool('pipeline_generate_script', {
            topic, platform: platforms[0], tone, targetLength: duration,
            researchId: pipeline.steps[0].result?.researchId,
          });
          pipeline.steps[1].status = 'complete';
          pipeline.steps[1].result = JSON.parse(scriptResult.content[0].text);

          // Step 3: Generate brief and render
          pipeline.status = 'rendering';
          pipeline.steps.push({ step: 'render', status: 'running', startedAt: new Date().toISOString() });
          fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));

          const brief = generateBrief({
            title: topic,
            hookText: pipeline.steps[1].result?.script?.hook || topic,
            format: 'explainer_v1',
            theme: 'dark',
            topics: pipeline.steps[1].result?.script?.body_points || [topic],
          });
          const renderJobId = submitRender(brief, { quality: 'production' });
          pipeline.steps[2].jobId = renderJobId;
          pipeline.steps[2].status = 'rendering';

          pipeline.status = 'complete';
          pipeline.completedAt = new Date().toISOString();
          fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));
        } catch (err) {
          pipeline.status = 'failed';
          pipeline.error = err.message;
          pipeline.completedAt = new Date().toISOString();
          fs.writeFileSync(pipelinePath, JSON.stringify(pipeline, null, 2));
        }
      })();

      return { content: [{ type: 'text', text: JSON.stringify({
        success: true, pipelineId, status: 'started', topic, platforms,
        message: 'Pipeline started. Steps: Research → Script → Render. Use remotion_job_status to check render progress.',
        statusFile: pipelinePath,
      }, null, 2) }] };
    }

    // ── Python Services Handlers ──────────────────────────────────────────────
    case 'services_status': {
      const servicesDir = path.join(REMOTION_DIR, 'services');
      const services = ['music-analysis', 'text-overlay', 'video-generator', 'google-drive'];
      const status = {};

      for (const svc of services) {
        const svcDir = path.join(servicesDir, svc);
        status[svc] = {
          installed: fs.existsSync(svcDir),
          hasDockerfile: fs.existsSync(path.join(svcDir, 'Dockerfile')),
          hasRequirements: fs.existsSync(path.join(svcDir, 'requirements.txt')),
        };
      }
      status.dockerCompose = fs.existsSync(path.join(servicesDir, 'docker-compose.yml'));

      // Check if Docker is running
      try {
        const dockerCheck = spawnSync('docker', ['info'], { timeout: 5000, stdio: 'pipe' });
        status.dockerRunning = dockerCheck.status === 0;
      } catch { status.dockerRunning = false; }

      // Check running containers
      if (status.dockerRunning) {
        try {
          const ps = spawnSync('docker', ['compose', '-f', path.join(servicesDir, 'docker-compose.yml'), 'ps', '--format', 'json'], { timeout: 10000, stdio: 'pipe' });
          if (ps.stdout) status.runningContainers = ps.stdout.toString().trim();
        } catch {}
      }

      return { content: [{ type: 'text', text: JSON.stringify(status, null, 2) }] };
    }

    case 'services_start': {
      const servicesDir = path.join(REMOTION_DIR, 'services');
      const composePath = path.join(servicesDir, 'docker-compose.yml');
      if (!fs.existsSync(composePath)) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'docker-compose.yml not found in services/' }) }], isError: true };
      }

      const svcArgs = args.services ? args.services : [];
      const cmdArgs = ['compose', '-f', composePath, 'up', '-d', ...svcArgs];

      try {
        const result = spawnSync('docker', cmdArgs, { timeout: 120000, stdio: 'pipe', cwd: servicesDir });
        return { content: [{ type: 'text', text: JSON.stringify({
          success: result.status === 0,
          stdout: result.stdout?.toString().slice(-500),
          stderr: result.stderr?.toString().slice(-500),
        }, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'services_music_match': {
      const { videoPath, mood, genre } = args;
      if (!videoPath) return { content: [{ type: 'text', text: JSON.stringify({ error: 'videoPath is required' }) }], isError: true };

      try {
        const body = JSON.stringify({ video_path: videoPath, mood, genre });
        const response = await fetch('http://localhost:5001/analyze-music-match', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
          signal: AbortSignal.timeout(60000),
        });
        const result = await response.json();
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: `Music service error (is it running? Use services_start): ${err.message}` }) }], isError: true };
      }
    }

    case 'services_text_overlay': {
      const { videoPath, text: overlayText, style = 'Minimalist', outputPath: overlayOut } = args;
      if (!videoPath) return { content: [{ type: 'text', text: JSON.stringify({ error: 'videoPath is required' }) }], isError: true };

      try {
        const body = JSON.stringify({ video_path: videoPath, text: overlayText, style, output_path: overlayOut });
        const response = await fetch('http://localhost:5000/process/video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
          signal: AbortSignal.timeout(300000),
        });
        const result = await response.json();
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: `Text overlay service error (is it running? Use services_start): ${err.message}` }) }], isError: true };
      }
    }

    // ── Template Marketplace Handlers ─────────────────────────────────────────
    case 'marketplace_browse': {
      const result = marketplace.browseListings({
        category: args.category || null,
        sort: args.sort || 'popular',
        limit: args.limit || 20,
        offset: args.offset || 0,
      });
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }

    case 'marketplace_search': {
      if (!args.query) return { content: [{ type: 'text', text: JSON.stringify({ error: 'query is required' }) }], isError: true };
      const result = marketplace.searchListings(args.query);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }

    case 'marketplace_details': {
      if (!args.templateId) return { content: [{ type: 'text', text: JSON.stringify({ error: 'templateId is required' }) }], isError: true };
      const listing = marketplace.getListingById(args.templateId);
      if (!listing) return { content: [{ type: 'text', text: JSON.stringify({ error: 'Template not found' }) }], isError: true };
      return { content: [{ type: 'text', text: JSON.stringify({
        ...listing.manifest,
        status: listing.status,
        reviews: listing.reviews?.slice(0, 10) || [],
        previewUrl: listing.previewUrl,
        thumbnailUrl: listing.thumbnailUrl,
        earnings: listing.manifest.authorId === (args.sellerId || 'default') ? listing.earnings : undefined,
      }, null, 2) }] };
    }

    case 'marketplace_publish': {
      const manifest = {
        name: args.name,
        description: args.description,
        longDescription: args.longDescription,
        category: args.category,
        tags: args.tags || [],
        author: args.author || 'Isaiah Dupree',
        license: args.license || (args.price > 0 ? 'commercial' : 'free'),
        pricing: { price: args.price || 0, currency: 'usd' },
        technical: {
          compositions: args.compositions || [],
          mcpTools: args.mcpTools || [],
          dependencies: args.dependencies || [],
          remotionVersion: '>=4.0.0',
          entryPoint: 'src/index.tsx',
        },
      };
      const result = marketplace.publishTemplate(manifest, args.sellerId || 'default');
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }], isError: !result.success };
    }

    case 'marketplace_buy': {
      if (!args.templateId) return { content: [{ type: 'text', text: JSON.stringify({ error: 'templateId is required' }) }], isError: true };
      const result = marketplace.initiatePurchase(args.templateId, args.buyerId || 'default');
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }], isError: !result.success };
    }

    case 'marketplace_my_templates': {
      const templates = marketplace.getSellerTemplates(args.sellerId || 'default');
      return { content: [{ type: 'text', text: JSON.stringify({ templates }, null, 2) }] };
    }

    case 'marketplace_my_purchases': {
      const purchases = marketplace.getUserPurchases(args.buyerId || 'default');
      return { content: [{ type: 'text', text: JSON.stringify({ purchases }, null, 2) }] };
    }

    case 'marketplace_review': {
      if (!args.templateId || !args.rating) return { content: [{ type: 'text', text: JSON.stringify({ error: 'templateId and rating are required' }) }], isError: true };
      const result = marketplace.addReview(args.templateId, args.userId || 'default', args.userName || 'Anonymous', args.rating, args.title || '', args.body || '');
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }], isError: !result.success };
    }

    case 'marketplace_categories': {
      return { content: [{ type: 'text', text: JSON.stringify(marketplace.CATEGORIES, null, 2) }] };
    }

    // ── Composition/Scene/Animation Browser ───────────────────────────────────
    case 'remotion_list_compositions': {
      const compositions = [];
      // Scan compositions directory
      const compsDir = path.join(REMOTION_DIR, 'src', 'compositions');
      if (fs.existsSync(compsDir)) {
        const scanDir = (dir, prefix = '') => {
          for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
            if (entry.isDirectory()) {
              scanDir(path.join(dir, entry.name), prefix ? `${prefix}/${entry.name}` : entry.name);
            } else if (entry.name.endsWith('.tsx') && !entry.name.startsWith('index')) {
              compositions.push({
                file: prefix ? `${prefix}/${entry.name}` : entry.name,
                name: entry.name.replace('.tsx', ''),
                source: prefix || 'main',
              });
            }
          }
        };
        scanDir(compsDir);
      }
      return { content: [{ type: 'text', text: JSON.stringify({ total: compositions.length, compositions }, null, 2) }] };
    }

    case 'remotion_list_scenes': {
      const scenesDir = path.join(REMOTION_DIR, 'src', 'scenes');
      const scenes = [];
      if (fs.existsSync(scenesDir)) {
        for (const f of fs.readdirSync(scenesDir)) {
          if (f.endsWith('.tsx') && f !== 'index.ts') {
            scenes.push({ name: f.replace('.tsx', ''), file: f });
          }
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify({ total: scenes.length, scenes }, null, 2) }] };
    }

    case 'remotion_list_animations': {
      const animDir = path.join(REMOTION_DIR, 'src', 'animations');
      const anims = [];
      if (fs.existsSync(animDir)) {
        for (const f of fs.readdirSync(animDir)) {
          if (f.endsWith('.ts') && f !== 'index.ts') {
            anims.push({ name: f.replace('.ts', ''), file: f });
          }
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify({ total: anims.length, animations: anims }, null, 2) }] };
    }

    case 'heygen_generate_avatar': {
      if (!args.text) return { content: [{ type: 'text', text: JSON.stringify({ error: 'text is required' }) }], isError: true };
      try {
        const dimension = (args.width && args.height) ? { width: args.width, height: args.height } : undefined;
        const result = await heygen.generateAvatar({
          text: args.text,
          avatarId: args.avatarId,
          voiceId: args.voiceId,
          style: args.style,
          dimension,
        });
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'heygen_list_avatars': {
      try {
        const result = await heygen.listAvatars();
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    case 'heygen_video_status': {
      if (!args.videoId) return { content: [{ type: 'text', text: JSON.stringify({ error: 'videoId is required' }) }], isError: true };
      try {
        const result = await heygen.pollVideoStatus(args.videoId);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }], isError: true };
      }
    }

    default:
      return {
        content: [{ type: 'text', text: JSON.stringify({ error: `Unknown tool: ${name}` }) }],
        isError: true,
      };
  }
}

// ── Stdio Transport ───────────────────────────────────────────────────────────

const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on('line', (line) => {
  line = line.trim();
  if (!line) return;

  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    return;
  }

  const { id, method, params } = msg;

  function reply(result) {
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\n');
  }

  function replyError(code, message, data) {
    process.stdout.write(JSON.stringify({
      jsonrpc: '2.0',
      id,
      error: { code, message, ...(data ? { data } : {}) },
    }) + '\n');
  }

  switch (method) {
    case 'initialize':
      reply({
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'remotion-mcp-studio', version: '2.0.0' },
      });
      break;

    case 'tools/list':
      reply({ tools: TOOL_DEFS });
      break;

    case 'tools/call': {
      const { name, arguments: args } = params;
      handleTool(name, args || {})
        .then((result) => reply(result))
        .catch((err) => replyError(-32603, 'Internal error', err.message));
      break;
    }

    case 'notifications/initialized':
    case 'ping':
      if (id !== undefined) reply({});
      break;

    default:
      if (id !== undefined) {
        replyError(-32601, `Method not found: ${method}`);
      }
  }
});

rl.on('close', () => process.exit(0));
process.on('SIGTERM', () => process.exit(0));
