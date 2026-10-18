#!/usr/bin/env node
/**
 * Seed the marketplace with starter templates from the existing compositions.
 * Run: npm run marketplace:seed
 */

'use strict';

const { publishTemplate } = require('./server');

const templates = [
  {
    manifest: {
      name: 'TikTok Countdown Timer',
      description: 'Animated countdown video for TikTok with hook text, numbered items, and CTA. 5 built-in themes.',
      category: 'social-video',
      tags: ['tiktok', 'countdown', 'shorts', 'vertical', 'hook'],
      author: 'Isaiah Dupree',
      license: 'free',
      pricing: { price: 0 },
      technical: {
        compositions: ['TikTokVideo'],
        entryPoint: 'src/compositions/tiktok-pipeline/TikTokVideo.tsx',
        dependencies: ['@remotion/captions', '@remotion/media-utils'],
      },
    },
  },
  {
    manifest: {
      name: 'UGC Product Demo Pack',
      description: 'Complete UGC ad pack: before/after, feature list, testimonial, problem/solution, stat counter, and urgency formats.',
      category: 'ads',
      tags: ['ugc', 'product', 'ads', 'meta', 'instagram', 'tiktok'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 1999 },
      technical: {
        compositions: ['UGCBeforeAfter', 'UGCFeatureList', 'UGCTestimonial', 'UGCProblemSolution', 'UGCStatCounter', 'UGCUrgency'],
        entryPoint: 'src/compositions/ugc/index.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'EverReach Ad Suite',
      description: 'Full app marketing suite: pain point ads, listicle, comparison, stat cards, App Store mockups, and reels.',
      category: 'ads',
      tags: ['app', 'marketing', 'ads', 'app-store', 'screenshots', 'meta'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 2999 },
      technical: {
        compositions: ['EverReachAd', 'PainPointAd', 'ListicleAd', 'ComparisonAd', 'EverReachAppStoreMockup', 'EverReachReel'],
        entryPoint: 'src/compositions/everreach/index.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'YouTube Explainer Kit',
      description: 'Professional explainer videos with SEO documentary style, chapter cards, and animated topics. 16:9 format.',
      category: 'youtube',
      tags: ['youtube', 'explainer', 'documentary', 'education', 'tutorial'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 1499 },
      technical: {
        compositions: ['SEODocumentary', 'SEODocumentaryV2', 'FullVideoDemo'],
        entryPoint: 'src/compositions/SEODocumentary.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'Podcast Clip Generator',
      description: 'Turn podcast episodes into shareable clips with waveform visualization, captions, and branding.',
      category: 'podcast',
      tags: ['podcast', 'clip', 'waveform', 'audiogram', 'captions'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 999 },
      technical: {
        compositions: ['PodcastClip'],
        entryPoint: 'src/compositions/PodcastClip.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'AI Content Pipeline Automation',
      description: 'Full automation: research topics via Perplexity, generate scripts with Claude, create voiceovers with ElevenLabs, render and publish.',
      category: 'automation',
      tags: ['ai', 'pipeline', 'automation', 'mcp', 'research', 'script', 'voiceover'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 4999 },
      technical: {
        mcpTools: ['pipeline_research', 'pipeline_generate_script', 'pipeline_generate_voiceover', 'pipeline_full_run'],
        envVars: {
          ANTHROPIC_API_KEY: 'Claude API for script generation',
          PERPLEXITY_API_KEY: 'Perplexity for topic research',
          ELEVENLABS_API_KEY: 'ElevenLabs for voiceover',
        },
      },
    },
  },
  {
    manifest: {
      name: 'Caption Styles Collection',
      description: '15+ TikTok and UGC caption styles: pop-in, karaoke-box, word-slam, neon, ig-story, and more.',
      category: 'effects',
      tags: ['captions', 'subtitles', 'tiktok', 'ugc', 'styles', 'typography'],
      author: 'Isaiah Dupree',
      license: 'free',
      pricing: { price: 0 },
      technical: {
        compositions: ['CaptionStylesBenchmark'],
        entryPoint: 'src/components/TikTokCaptions.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'Animation Presets Pack',
      description: '12 production-ready animation presets: bounce, fade, glitch, kinetic typography, typewriter, zoom, stagger, and more.',
      category: 'effects',
      tags: ['animations', 'presets', 'transitions', 'effects', 'motion'],
      author: 'Isaiah Dupree',
      license: 'free',
      pricing: { price: 0 },
      technical: {
        entryPoint: 'src/animations/index.ts',
      },
    },
  },
  {
    manifest: {
      name: 'BlankLogo Ad Templates',
      description: 'Before/after reveals, 3-step flows, comparison cards, receipt proofs, and UI mockups for SaaS marketing.',
      category: 'ads',
      tags: ['saas', 'before-after', 'comparison', 'ui-proof', 'marketing'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 1499 },
      technical: {
        compositions: ['BeforeAfterSplit', 'ThreeSteps', 'ComparisonCard', 'UIProof', 'ReceiptProof'],
        entryPoint: 'src/compositions/blanklogo/index.tsx',
      },
    },
  },
  {
    manifest: {
      name: 'Multi-Platform Format Pack',
      description: '30+ platform-specific video formats for YouTube, TikTok, Instagram, LinkedIn, Twitter, Facebook, and Threads.',
      category: 'social-video',
      tags: ['multi-platform', 'formats', 'youtube', 'tiktok', 'instagram', 'linkedin', 'twitter'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 2499 },
      technical: {
        entryPoint: 'formats/index.ts',
      },
    },
  },
  {
    manifest: {
      name: 'Music Analysis & Matching',
      description: 'Python microservice for AI-powered music-to-video matching. Analyzes tempo, mood, genre, and energy for perfect soundtrack selection.',
      category: 'automation',
      tags: ['music', 'ai', 'matching', 'audio', 'mood', 'docker'],
      author: 'Isaiah Dupree',
      license: 'free',
      pricing: { price: 0 },
      technical: {
        mcpTools: ['services_music_match'],
        envVars: { OPENAI_API_KEY: 'OpenAI for music analysis' },
      },
    },
  },
  {
    manifest: {
      name: 'Smart Text Overlay Engine',
      description: 'AI-powered text overlay using Whisper transcription, YOLO detection, and CLIP understanding. Automatically places text avoiding faces and UI.',
      category: 'automation',
      tags: ['text-overlay', 'ai', 'whisper', 'yolo', 'docker', 'video-processing'],
      author: 'Isaiah Dupree',
      license: 'commercial',
      pricing: { price: 1999 },
      technical: {
        mcpTools: ['services_text_overlay'],
        envVars: { OPENAI_API_KEY: 'OpenAI for text generation' },
      },
    },
  },
];

console.log('Seeding marketplace with', templates.length, 'templates...\n');

for (const t of templates) {
  const result = publishTemplate(t.manifest, 'isaiah-dupree');
  const price = t.manifest.pricing.price === 0 ? 'FREE' : `$${(t.manifest.pricing.price / 100).toFixed(2)}`;
  console.log(`  ${result.success ? '✓' : '✗'} ${t.manifest.name} (${price}) → ${result.status || result.errors?.join(', ')}`);
}

console.log('\nDone! Run `npm run marketplace` to start the marketplace server.');
