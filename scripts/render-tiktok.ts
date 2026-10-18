#!/usr/bin/env tsx
/**
 * render.ts — CLI render script for the TikTok pipeline
 *
 * Usage:
 *   npx tsx scripts/render.ts <brief.json> <output.mp4> [--quality preview|production]
 *   npx tsx scripts/render.ts --brief '{"hook_text":"..."}' output.mp4
 */
import path from 'path';
import fs from 'fs';
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import type { ContentBrief } from '../src/types';

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: npx tsx scripts/render.ts <brief.json> <output.mp4>');
    process.exit(1);
  }

  const briefArg = args[0];
  const outputArg = args[1];
  const quality = args.includes('--quality') ? args[args.indexOf('--quality') + 1] : 'production';
  const isProRes = args.includes('--prores');

  // Load brief
  let brief: ContentBrief;
  if (briefArg.startsWith('{')) {
    brief = JSON.parse(briefArg);
  } else {
    brief = JSON.parse(fs.readFileSync(briefArg, 'utf-8'));
  }

  const outputPath = path.resolve(outputArg);
  const projectRoot = path.resolve(__dirname, '..');

  console.log('TikTok Pipeline Render');
  console.log('==========================');
  console.log(`Brief: ${brief.id || 'unnamed'} | Format: ${brief.format} | Duration: ${brief.duration_sec ?? 30}s`);
  console.log(`Theme: ${brief.color_theme ?? 'dark'} | Output: ${path.basename(outputPath)}`);
  console.log('');

  // CRF based on quality
  const crf = quality === 'preview' ? 28 : 18;

  console.log('1/3 Bundling...');
  const bundled = await bundle({
    entryPoint: path.join(projectRoot, 'src', 'Root.tsx'),
    webpackOverride: (config) => config,
  });

  console.log('2/3 Selecting composition...');
  const durationSec = brief.duration_sec ?? 30;
  const composition = await selectComposition({
    serveUrl: bundled,
    id: 'TikTokVideo',
    inputProps: { brief },
  });

  const durationInFrames = Math.round(durationSec * composition.fps);

  if (isProRes) {
    const proResOutput = outputPath.replace(/\.mp4$/i, '.mov');
    console.log(`3/3 Rendering ProRes 4444 alpha — ${durationInFrames} frames...`);
    await renderMedia({
      composition: { ...composition, durationInFrames },
      serveUrl: bundled,
      codec: 'prores',
      outputLocation: proResOutput,
      inputProps: { brief },
      concurrency: 4,
      onProgress: ({ progress }) => {
        process.stdout.write(`\r    ${Math.round(progress * 100)}%`);
      },
    });
    process.stdout.write('\n');
    const stats = fs.statSync(proResOutput);
    console.log(`\nDone — ${(stats.size / 1024 / 1024).toFixed(1)}MB -> ${proResOutput}`);
  } else {
    console.log(`3/3 Rendering ${durationInFrames} frames @ ${composition.fps}fps...`);
    await renderMedia({
      composition: { ...composition, durationInFrames },
      serveUrl: bundled,
      codec: 'h264',
      audioCodec: 'mp3',
      outputLocation: outputPath,
      inputProps: { brief },
      crf,
      concurrency: 4,
      onProgress: ({ progress }) => {
        process.stdout.write(`\r    ${Math.round(progress * 100)}%`);
      },
    });
    process.stdout.write('\n');
    const stats = fs.statSync(outputPath);
    console.log(`\nDone — ${(stats.size / 1024 / 1024).toFixed(1)}MB -> ${outputPath}`);
  }
}

main().catch((e) => {
  console.error('Render failed:', e.message);
  process.exit(1);
});
