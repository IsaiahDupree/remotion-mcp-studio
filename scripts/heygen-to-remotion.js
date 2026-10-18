#!/usr/bin/env node
/**
 * heygen-to-remotion.js
 *
 * Full pipeline: HeyGen green-screen avatar → transparent WebM → Remotion props JSON
 *
 * Usage:
 *   node scripts/heygen-to-remotion.js <greenscreen.mp4> <captions.ass> [--title "My Title"]
 *
 * Steps:
 *   1. FFmpeg chromakey removal (green → transparent WebM)
 *   2. Parse .ass captions into word-level timings
 *   3. Output Remotion props JSON ready for AvatarWithCaptions composition
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ── Parse .ass captions to word timings ──────────────────────────────────────

function parseAssToWordTimings(assContent) {
  const lines = assContent.split('\n');
  const dialogues = lines.filter(l => l.startsWith('Dialogue:'));
  const wordTimings = [];

  for (const line of dialogues) {
    // Format: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    const match = line.match(/Dialogue:\s*\d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),[^,]*,[^,]*,\d+,\d+,\d+,[^,]*,(.*)/);
    if (!match) continue;

    const start = parseAssTime(match[1]);
    const end = parseAssTime(match[2]);
    const text = match[3].replace(/\\n/g, ' ').replace(/\\N/g, ' ').trim();
    const words = text.split(/\s+/).filter(Boolean);

    if (words.length === 0) continue;

    // Distribute time evenly across words in this dialogue line
    const wordDuration = (end - start) / words.length;
    for (let i = 0; i < words.length; i++) {
      wordTimings.push({
        word: words[i],
        start: Math.round((start + i * wordDuration) * 1000) / 1000,
        end: Math.round((start + (i + 1) * wordDuration) * 1000) / 1000,
      });
    }
  }

  return wordTimings;
}

function parseAssTime(timeStr) {
  // Format: H:MM:SS.CC (centiseconds)
  const parts = timeStr.split(':');
  const hours = parseInt(parts[0]);
  const minutes = parseInt(parts[1]);
  const secParts = parts[2].split('.');
  const seconds = parseInt(secParts[0]);
  const centiseconds = parseInt(secParts[1] || '0');
  return hours * 3600 + minutes * 60 + seconds + centiseconds / 100;
}

// ── FFmpeg green screen removal ──────────────────────────────────────────────

function removeGreenScreen(inputPath, outputPath, options = {}) {
  const {
    keyColor = '0x00b140',
    similarity = 0.15,
    blend = 0.08,
    bitrate = '2M',
  } = options;

  console.log(`Converting green screen → transparent WebM...`);
  console.log(`  Input:  ${inputPath}`);
  console.log(`  Output: ${outputPath}`);

  const cmd = [
    'ffmpeg', '-y',
    '-i', `"${inputPath}"`,
    '-vf', `"chromakey=${keyColor}:similarity=${similarity}:blend=${blend},format=yuva420p"`,
    '-c:v', 'libvpx-vp9',
    '-pix_fmt', 'yuva420p',
    '-auto-alt-ref', '0',
    '-b:v', bitrate,
    '-an',  // strip audio (Remotion handles audio separately)
    `"${outputPath}"`,
  ].join(' ');

  execSync(cmd, { stdio: 'inherit' });
  console.log(`  ✓ Done! Size: ${(fs.statSync(outputPath).size / 1024 / 1024).toFixed(1)} MB`);
}

// ── Generate Remotion props ──────────────────────────────────────────────────

function generateRemotionProps(options) {
  const {
    avatarWebmPath,
    captions,
    title = 'Remotion MCP Studio',
    subtitle = '',
    accentColor = '#3b82f6',
    backgroundType = 'color',
    backgroundValue = '#0a0a1a',
    captionStyle = 'tiktok',
    durationInSeconds,
  } = options;

  return {
    avatarVideoSrc: path.basename(avatarWebmPath),
    backgroundType,
    backgroundValue,
    title,
    subtitle,
    captions,
    captionStyle,
    accentColor,
    avatarScale: 1.0,
    avatarPosition: 'center',
    showGradientOverlay: true,
    durationInSeconds: durationInSeconds || Math.ceil(captions[captions.length - 1]?.end || 30),
  };
}

// ── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node scripts/heygen-to-remotion.js <greenscreen.mp4> <captions.ass> [--title "Title"]');
    console.log('');
    console.log('Example:');
    console.log('  node scripts/heygen-to-remotion.js output/avatars/isaiah-v2-greenscreen.mp4 output/avatars/isaiah-v2-captions.ass --title "Welcome to MCP Studio"');
    process.exit(1);
  }

  const inputVideo = args[0];
  const captionsFile = args[1];
  const titleIdx = args.indexOf('--title');
  const title = titleIdx >= 0 ? args[titleIdx + 1] : 'Remotion MCP Studio';
  const subtitleIdx = args.indexOf('--subtitle');
  const subtitle = subtitleIdx >= 0 ? args[subtitleIdx + 1] : '';

  if (!fs.existsSync(inputVideo)) {
    console.error(`Error: Input video not found: ${inputVideo}`);
    process.exit(1);
  }
  if (!fs.existsSync(captionsFile)) {
    console.error(`Error: Captions file not found: ${captionsFile}`);
    process.exit(1);
  }

  const timestamp = Date.now();
  const outputWebm = `public/avatar-transparent-${timestamp}.webm`;
  const outputProps = `output/avatars/remotion-props-${timestamp}.json`;

  // Step 1: Green screen removal
  removeGreenScreen(inputVideo, outputWebm);

  // Step 2: Parse captions
  console.log('\nParsing captions...');
  const assContent = fs.readFileSync(captionsFile, 'utf8');
  const captions = parseAssToWordTimings(assContent);
  console.log(`  ✓ ${captions.length} words parsed`);
  console.log(`  First: "${captions[0]?.word}" at ${captions[0]?.start}s`);
  console.log(`  Last: "${captions[captions.length - 1]?.word}" at ${captions[captions.length - 1]?.end}s`);

  // Step 3: Generate props
  console.log('\nGenerating Remotion props...');
  const props = generateRemotionProps({
    avatarWebmPath: outputWebm,
    captions,
    title,
    subtitle,
  });

  fs.mkdirSync(path.dirname(outputProps), { recursive: true });
  fs.writeFileSync(outputProps, JSON.stringify(props, null, 2));
  console.log(`  ✓ Props saved to ${outputProps}`);

  // Summary
  console.log('\n═══════════════════════════════════════════════');
  console.log('  PIPELINE COMPLETE');
  console.log(`  Avatar WebM:  ${outputWebm}`);
  console.log(`  Props JSON:   ${outputProps}`);
  console.log(`  Duration:     ${props.durationInSeconds}s`);
  console.log(`  Words:        ${captions.length}`);
  console.log('');
  console.log('  To render:');
  console.log(`  npx remotion render AvatarWithCaptions --props="${outputProps}"`);
  console.log('═══════════════════════════════════════════════');
}

// Export for use in MCP server
module.exports = { parseAssToWordTimings, removeGreenScreen, generateRemotionProps };

if (require.main === module) {
  main();
}
