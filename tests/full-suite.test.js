#!/usr/bin/env node
/**
 * Remotion MCP Studio — Full Test Suite
 *
 * Tests: MCP server, marketplace, HeyGen integration, template parsing, pipeline scripts
 * Run: node --test tests/full-suite.test.js
 */

'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ── Helper: Send MCP message and get response ───────────────────────────────

function mcpCall(toolName, args, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', ['mcp-server.js'], {
      cwd: ROOT,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env },
    });

    let output = '';
    proc.stdout.on('data', (d) => { output += d.toString(); });

    const timer = setTimeout(() => {
      proc.kill();
      reject(new Error(`MCP call ${toolName} timed out after ${timeout}ms`));
    }, timeout);

    // Initialize
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {} }) + '\n');

    setTimeout(() => {
      proc.stdin.write(JSON.stringify({
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: toolName, arguments: args },
      }) + '\n');
    }, 300);

    setTimeout(() => {
      clearTimeout(timer);
      proc.kill();
      const lines = output.trim().split('\n');
      for (const line of lines) {
        try {
          const msg = JSON.parse(line);
          if (msg.id === 2) {
            const text = msg.result?.content?.[0]?.text;
            resolve(text ? JSON.parse(text) : null);
            return;
          }
        } catch {}
      }
      reject(new Error(`No response for ${toolName}`));
    }, 3000);
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// 1. MCP SERVER CORE
// ═══════════════════════════════════════════════════════════════════════════════

describe('MCP Server Core', () => {
  it('loads without errors', () => {
    const m = require(path.join(ROOT, 'mcp-server.js'));
    assert.ok(true, 'MCP server loaded');
  });

  it('lists 37+ tools', async () => {
    const proc = spawn('node', ['mcp-server.js'], { cwd: ROOT, stdio: ['pipe', 'pipe', 'pipe'] });
    let output = '';
    proc.stdout.on('data', (d) => { output += d.toString(); });

    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {} }) + '\n');
    setTimeout(() => proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }) + '\n'), 300);

    await new Promise((resolve) => setTimeout(resolve, 2000));
    proc.kill();

    const lines = output.trim().split('\n');
    for (const line of lines) {
      try {
        const msg = JSON.parse(line);
        if (msg.id === 2) {
          assert.ok(msg.result.tools.length >= 34, `Expected 34+ tools, got ${msg.result.tools.length}`);
          return;
        }
      } catch {}
    }
    assert.fail('No tools/list response');
  });

  it('remotion_list_formats returns 10+ formats', async () => {
    const result = await mcpCall('remotion_list_formats', {});
    assert.ok(Array.isArray(result), 'Should return array');
    assert.ok(result.length >= 10, `Expected 10+ formats, got ${result.length}`);
  });

  it('remotion_generate_brief creates valid brief', async () => {
    const result = await mcpCall('remotion_generate_brief', {
      title: 'Test Video',
      format: 'explainer_v1',
      topics: ['Point A', 'Point B'],
    });
    assert.ok(result.success, 'Should succeed');
    assert.ok(result.brief.sections.length >= 3, 'Should have sections');
    assert.ok(result.brief.id, 'Should have ID');
  });

  it('remotion_validate_brief catches invalid briefs', async () => {
    const result = await mcpCall('remotion_validate_brief', { brief: {} });
    assert.ok(!result.valid, 'Empty brief should be invalid');
    assert.ok(result.errors.length > 0, 'Should have errors');
  });

  it('remotion_validate_brief accepts valid briefs', async () => {
    const result = await mcpCall('remotion_validate_brief', {
      brief: {
        id: 'test', format: 'explainer_v1',
        settings: { resolution: { width: 1080, height: 1920 }, fps: 30, duration_sec: 30, aspect_ratio: '9:16' },
        style: { theme: 'dark' },
        sections: [{ id: 's1', type: 'intro' }],
      },
    });
    assert.ok(result.valid, 'Valid brief should pass');
  });

  it('remotion_list_compositions finds 50+', async () => {
    const result = await mcpCall('remotion_list_compositions', {});
    assert.ok(result.total >= 50, `Expected 50+ compositions, got ${result.total}`);
  });

  it('remotion_list_scenes finds 25+', async () => {
    const result = await mcpCall('remotion_list_scenes', {});
    assert.ok(result.total >= 25, `Expected 25+ scenes, got ${result.total}`);
  });

  it('remotion_list_animations finds 10+', async () => {
    const result = await mcpCall('remotion_list_animations', {});
    assert.ok(result.total >= 10, `Expected 10+ animations, got ${result.total}`);
  });

  it('remotion_job_status handles missing jobs', async () => {
    const result = await mcpCall('remotion_job_status', { jobId: 'nonexistent' });
    assert.ok(result.error, 'Should return error for missing job');
  });

  it('remotion_list_jobs returns array', async () => {
    const result = await mcpCall('remotion_list_jobs', {});
    assert.ok(Array.isArray(result), 'Should return array');
  });

  it('remotion_list_outputs returns array', async () => {
    const result = await mcpCall('remotion_list_outputs', {});
    assert.ok(Array.isArray(result), 'Should return array');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 2. TIKTOK PIPELINE
// ═══════════════════════════════════════════════════════════════════════════════

describe('TikTok Pipeline', () => {
  it('tiktok_list_briefs finds 4+ briefs', async () => {
    const result = await mcpCall('tiktok_list_briefs', {});
    assert.ok(Array.isArray(result), 'Should return array');
    assert.ok(result.length >= 4, `Expected 4+ briefs, got ${result.length}`);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 3. MARKETPLACE
// ═══════════════════════════════════════════════════════════════════════════════

describe('Marketplace', () => {
  it('marketplace_categories returns 9 categories', async () => {
    const result = await mcpCall('marketplace_categories', {});
    assert.ok(Object.keys(result).length >= 9, 'Should have 9+ categories');
  });

  it('marketplace_browse returns listings', async () => {
    const result = await mcpCall('marketplace_browse', { sort: 'popular' });
    assert.ok(typeof result.total === 'number', 'Should have total count');
    assert.ok(Array.isArray(result.listings), 'Should have listings array');
  });

  it('marketplace_search finds results', async () => {
    const result = await mcpCall('marketplace_search', { query: 'animation' });
    assert.ok(typeof result.total === 'number', 'Should have total');
    assert.ok(result.query === 'animation', 'Should echo query');
  });

  it('marketplace_my_templates shows seller templates', async () => {
    const result = await mcpCall('marketplace_my_templates', { sellerId: 'isaiah-dupree' });
    assert.ok(Array.isArray(result.templates), 'Should have templates');
    assert.ok(result.templates.length >= 10, `Expected 10+ templates, got ${result.templates.length}`);
  });

  it('marketplace_my_purchases returns array', async () => {
    const result = await mcpCall('marketplace_my_purchases', {});
    assert.ok(Array.isArray(result.purchases), 'Should have purchases');
  });

  it('marketplace_details handles missing template', async () => {
    const result = await mcpCall('marketplace_details', { templateId: 'nonexistent' });
    assert.ok(result.error, 'Should return error');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 4. SERVICES
// ═══════════════════════════════════════════════════════════════════════════════

describe('Python Services', () => {
  it('services_status shows installed services', async () => {
    const result = await mcpCall('services_status', {});
    assert.ok(result['music-analysis']?.installed, 'music-analysis should be installed');
    assert.ok(result['text-overlay']?.installed, 'text-overlay should be installed');
    assert.ok(result['video-generator']?.installed, 'video-generator should be installed');
    assert.ok(result['google-drive']?.installed, 'google-drive should be installed');
    assert.ok(result.dockerCompose, 'docker-compose.yml should exist');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 5. HEYGEN INTEGRATION
// ═══════════════════════════════════════════════════════════════════════════════

describe('HeyGen Integration', () => {
  it('heygen module loads', () => {
    const heygen = require(path.join(ROOT, 'marketplace', 'heygen.js'));
    assert.ok(heygen.generateAvatar, 'Should export generateAvatar');
    assert.ok(heygen.pollVideoStatus, 'Should export pollVideoStatus');
    assert.ok(heygen.downloadVideo, 'Should export downloadVideo');
    assert.ok(heygen.generateAndDownload, 'Should export generateAndDownload');
    assert.ok(heygen.listAvatars, 'Should export listAvatars');
  });

  it('heygen-to-remotion pipeline script loads', () => {
    const pipeline = require(path.join(ROOT, 'scripts', 'heygen-to-remotion.js'));
    assert.ok(pipeline.parseAssToWordTimings, 'Should export parseAssToWordTimings');
    assert.ok(pipeline.generateRemotionProps, 'Should export generateRemotionProps');
  });

  it('parseAssToWordTimings parses .ass captions', () => {
    const { parseAssToWordTimings } = require(path.join(ROOT, 'scripts', 'heygen-to-remotion.js'));
    const assContent = `[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:0:0.00,0:0:2.00,Default,,0000,0000,0000,,Hello world
Dialogue: 0,0:0:2.00,0:0:4.50,Default,,0000,0000,0000,,This is a test`;

    const words = parseAssToWordTimings(assContent);
    assert.ok(words.length === 6, `Expected 6 words, got ${words.length}`);
    assert.strictEqual(words[0].word, 'Hello');
    assert.strictEqual(words[0].start, 0);
    assert.ok(words[5].end <= 4.5, 'Last word should end at or before 4.5s');
  });

  it('generateRemotionProps creates valid props', () => {
    const { generateRemotionProps } = require(path.join(ROOT, 'scripts', 'heygen-to-remotion.js'));
    const props = generateRemotionProps({
      avatarWebmPath: 'public/test.webm',
      captions: [{ word: 'Hello', start: 0, end: 0.5 }],
      title: 'Test',
    });
    assert.strictEqual(props.title, 'Test');
    assert.strictEqual(props.captions.length, 1);
    assert.ok(props.avatarVideoSrc, 'Should have avatar source');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 6. MARKETPLACE SCHEMA
// ═══════════════════════════════════════════════════════════════════════════════

describe('Marketplace Schema', () => {
  it('createManifest generates valid manifest', () => {
    const { createManifest, validateManifest } = require(path.join(ROOT, 'marketplace', 'schema.js'));
    const manifest = createManifest({
      name: 'Test Template',
      description: 'A test',
      author: 'Tester',
      category: 'social-video',
    });
    assert.ok(manifest.id, 'Should have ID');
    assert.strictEqual(manifest.name, 'Test Template');
    const validation = validateManifest(manifest);
    assert.ok(validation.valid, `Should be valid: ${validation.errors.join(', ')}`);
  });

  it('validateManifest catches missing fields', () => {
    const { validateManifest } = require(path.join(ROOT, 'marketplace', 'schema.js'));
    const result = validateManifest({});
    assert.ok(!result.valid, 'Empty should be invalid');
    assert.ok(result.errors.length >= 3, 'Should have multiple errors');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// 7. FILE STRUCTURE
// ═══════════════════════════════════════════════════════════════════════════════

describe('Project Structure', () => {
  const requiredDirs = [
    'src/compositions/tiktok-pipeline',
    'src/compositions/content-pipeline',
    'src/compositions/marketplace-templates',
    'src/compositions/everreach',
    'src/compositions/ugc',
    'src/components/tiktok-pipeline',
    'src/pipeline/ai-generation',
    'src/scenes',
    'src/animations',
    'services/music-analysis',
    'services/text-overlay',
    'services/video-generator',
    'services/google-drive',
    'marketplace',
    'data/briefs/tiktok',
  ];

  for (const dir of requiredDirs) {
    it(`directory exists: ${dir}`, () => {
      assert.ok(fs.existsSync(path.join(ROOT, dir)), `Missing: ${dir}`);
    });
  }

  const requiredFiles = [
    'mcp-server.js',
    'remotion.config.ts',
    'package.json',
    '.env.example',
    '.gitignore',
    'marketplace/schema.js',
    'marketplace/server.js',
    'marketplace/heygen.js',
    'marketplace/seed.js',
    'scripts/heygen-to-remotion.js',
    'services/docker-compose.yml',
    'docs/heygen-api-reference.md',
    'src/compositions/marketplace-templates/AvatarWithCaptions.tsx',
    'src/compositions/marketplace-templates/LogoReveal.tsx',
    'src/compositions/marketplace-templates/ProductShowcase.tsx',
    'src/compositions/marketplace-templates/DataVisualization.tsx',
    'src/compositions/marketplace-templates/SplitScreenTalkingHead.tsx',
    'src/compositions/marketplace-templates/TestimonialCard.tsx',
  ];

  for (const file of requiredFiles) {
    it(`file exists: ${file}`, () => {
      assert.ok(fs.existsSync(path.join(ROOT, file)), `Missing: ${file}`);
    });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// 8. RENDERED OUTPUT
// ═══════════════════════════════════════════════════════════════════════════════

describe('Rendered Output', () => {
  it('final avatar video exists', () => {
    const videoPath = path.join(ROOT, 'output', 'isaiah-avatar-final.mp4');
    assert.ok(fs.existsSync(videoPath), 'Final video should exist');
    const stat = fs.statSync(videoPath);
    assert.ok(stat.size > 1_000_000, `Video should be > 1MB, got ${stat.size}`);
  });

  it('transparent WebM exists', () => {
    const webmPath = path.join(ROOT, 'public', 'avatar-transparent.webm');
    assert.ok(fs.existsSync(webmPath), 'Transparent WebM should exist');
    const stat = fs.statSync(webmPath);
    assert.ok(stat.size > 500_000, `WebM should be > 500KB, got ${stat.size}`);
  });

  it('props JSON is valid', () => {
    const propsPath = path.join(ROOT, 'output', 'avatars', 'remotion-props.json');
    assert.ok(fs.existsSync(propsPath), 'Props should exist');
    const props = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
    assert.ok(props.avatarVideoSrc, 'Should have avatar source');
    assert.ok(Array.isArray(props.captions), 'Should have captions array');
    assert.ok(props.captions.length > 0, 'Should have words');
    assert.ok(props.title, 'Should have title');
  });
});
