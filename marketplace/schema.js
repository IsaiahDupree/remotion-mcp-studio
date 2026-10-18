/**
 * Remotion MCP Marketplace — Data Schema & Template Package Format
 *
 * Templates and automations are packaged as .rmt (Remotion Template) bundles:
 *   template.rmt/
 *   ├── manifest.json    — metadata, pricing, dependencies
 *   ├── preview.mp4      — 10s preview video
 *   ├── thumbnail.png    — 1200x630 preview image
 *   ├── src/             — Remotion source files
 *   ├── briefs/          — Example brief JSONs
 *   └── README.md        — Usage documentation
 */

'use strict';

// ── Template Categories ──────────────────────────────────────────────────────

const CATEGORIES = {
  'social-video':     { name: 'Social Video',     icon: '📱', description: 'TikTok, Reels, Shorts, Stories' },
  'youtube':          { name: 'YouTube',           icon: '▶️', description: 'Explainers, tutorials, thumbnails' },
  'ads':              { name: 'Ads & Marketing',   icon: '📢', description: 'Product ads, UGC, promos' },
  'presentations':    { name: 'Presentations',     icon: '📊', description: 'Pitch decks, demos, walkthroughs' },
  'podcast':          { name: 'Podcast & Audio',   icon: '🎙️', description: 'Podcast clips, audiograms, waveforms' },
  'ecommerce':        { name: 'E-Commerce',        icon: '🛒', description: 'Product showcases, unboxings, comparisons' },
  'automation':       { name: 'Automations',       icon: '⚡', description: 'Pipelines, batch renderers, MCP tools' },
  'effects':          { name: 'Effects & Overlays', icon: '✨', description: 'Transitions, overlays, captions, grain' },
  'brand-kits':       { name: 'Brand Kits',        icon: '🎨', description: 'Theme packs, font bundles, color systems' },
};

// ── License Types ────────────────────────────────────────────────────────────

const LICENSES = {
  'free':         { name: 'Free',              commercial: true,  resale: false, attribution: false },
  'personal':     { name: 'Personal Use',      commercial: false, resale: false, attribution: false },
  'commercial':   { name: 'Commercial',        commercial: true,  resale: false, attribution: false },
  'extended':     { name: 'Extended',          commercial: true,  resale: true,  attribution: false },
  'open-source':  { name: 'Open Source (MIT)', commercial: true,  resale: true,  attribution: true },
};

// ── Manifest Schema ──────────────────────────────────────────────────────────

/**
 * @typedef {Object} TemplateManifest
 * @property {string} id - Unique template ID (e.g., "tiktok-countdown-pro")
 * @property {string} name - Display name
 * @property {string} version - Semver version
 * @property {string} description - Short description (max 200 chars)
 * @property {string} longDescription - Full description with markdown
 * @property {string} category - Category ID from CATEGORIES
 * @property {string[]} tags - Searchable tags
 * @property {string} author - Author display name
 * @property {string} authorId - Author marketplace account ID
 * @property {string} license - License type from LICENSES
 * @property {Object} pricing
 * @property {number} pricing.price - Price in cents (0 = free)
 * @property {string} pricing.currency - Currency code (default: "usd")
 * @property {string} [pricing.stripeProductId] - Stripe product ID
 * @property {string} [pricing.stripePriceId] - Stripe price ID
 * @property {Object} technical
 * @property {string} technical.remotionVersion - Min Remotion version required
 * @property {string[]} technical.dependencies - npm package dependencies
 * @property {string[]} technical.compositions - Exported Remotion composition IDs
 * @property {string[]} technical.mcpTools - Exported MCP tool names (for automations)
 * @property {string} technical.entryPoint - Main file (default: "src/index.tsx")
 * @property {Object} [technical.envVars] - Required environment variables {name: description}
 * @property {Object} assets
 * @property {string} assets.thumbnail - Path to thumbnail image
 * @property {string} [assets.preview] - Path to preview video
 * @property {string[]} [assets.screenshots] - Additional screenshot paths
 * @property {Object} stats
 * @property {number} stats.downloads - Total downloads
 * @property {number} stats.rating - Average rating (1-5)
 * @property {number} stats.reviews - Number of reviews
 * @property {string} stats.publishedAt - ISO date first published
 * @property {string} stats.updatedAt - ISO date last updated
 */

/**
 * Create a new template manifest with defaults.
 * @param {Partial<TemplateManifest>} input
 * @returns {TemplateManifest}
 */
function createManifest(input) {
  const now = new Date().toISOString();
  return {
    id: input.id || `template-${Date.now()}`,
    name: input.name || 'Untitled Template',
    version: input.version || '1.0.0',
    description: input.description || '',
    longDescription: input.longDescription || '',
    category: input.category || 'social-video',
    tags: input.tags || [],
    author: input.author || '',
    authorId: input.authorId || '',
    license: input.license || 'commercial',
    pricing: {
      price: input.pricing?.price ?? 0,
      currency: input.pricing?.currency || 'usd',
      stripeProductId: input.pricing?.stripeProductId || null,
      stripePriceId: input.pricing?.stripePriceId || null,
    },
    technical: {
      remotionVersion: input.technical?.remotionVersion || '>=4.0.0',
      dependencies: input.technical?.dependencies || [],
      compositions: input.technical?.compositions || [],
      mcpTools: input.technical?.mcpTools || [],
      entryPoint: input.technical?.entryPoint || 'src/index.tsx',
      envVars: input.technical?.envVars || {},
    },
    assets: {
      thumbnail: input.assets?.thumbnail || 'thumbnail.png',
      preview: input.assets?.preview || null,
      screenshots: input.assets?.screenshots || [],
    },
    stats: {
      downloads: 0,
      rating: 0,
      reviews: 0,
      publishedAt: now,
      updatedAt: now,
    },
  };
}

/**
 * Validate a template manifest.
 * @param {TemplateManifest} manifest
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateManifest(manifest) {
  const errors = [];
  if (!manifest.id) errors.push('Missing required field: id');
  if (!manifest.name) errors.push('Missing required field: name');
  if (!manifest.version || !/^\d+\.\d+\.\d+/.test(manifest.version)) errors.push('Invalid version (must be semver)');
  if (!manifest.description) errors.push('Missing required field: description');
  if (manifest.description && manifest.description.length > 200) errors.push('description must be <= 200 characters');
  if (!CATEGORIES[manifest.category]) errors.push(`Invalid category: ${manifest.category}. Valid: ${Object.keys(CATEGORIES).join(', ')}`);
  if (!LICENSES[manifest.license]) errors.push(`Invalid license: ${manifest.license}. Valid: ${Object.keys(LICENSES).join(', ')}`);
  if (!manifest.author) errors.push('Missing required field: author');
  if (manifest.pricing?.price < 0) errors.push('Price cannot be negative');
  if (!manifest.technical?.entryPoint) errors.push('Missing technical.entryPoint');
  return { valid: errors.length === 0, errors };
}

// ── Review Schema ────────────────────────────────────────────────────────────

/**
 * @typedef {Object} Review
 * @property {string} id
 * @property {string} templateId
 * @property {string} userId
 * @property {string} userName
 * @property {number} rating - 1-5 stars
 * @property {string} title
 * @property {string} body
 * @property {string} createdAt
 */

// ── Marketplace Listing ──────────────────────────────────────────────────────

/**
 * @typedef {Object} MarketplaceListing
 * @property {TemplateManifest} manifest
 * @property {string} status - "draft" | "pending_review" | "published" | "suspended"
 * @property {string} storagePath - Path to .rmt bundle in storage
 * @property {string} previewUrl - Public URL for preview video
 * @property {string} thumbnailUrl - Public URL for thumbnail
 * @property {Review[]} reviews
 * @property {Object} earnings
 * @property {number} earnings.totalRevenue - Total revenue in cents
 * @property {number} earnings.totalSales - Number of sales
 * @property {number} earnings.platformFee - Platform fee percentage (default: 15%)
 */

// ── Seller Profile ───────────────────────────────────────────────────────────

/**
 * @typedef {Object} SellerProfile
 * @property {string} id
 * @property {string} displayName
 * @property {string} bio
 * @property {string} avatarUrl
 * @property {string} stripeConnectId - Stripe Connect account for payouts
 * @property {string[]} templateIds - Published template IDs
 * @property {Object} stats
 * @property {number} stats.totalSales
 * @property {number} stats.totalRevenue
 * @property {number} stats.avgRating
 * @property {string} stats.joinedAt
 */

module.exports = {
  CATEGORIES,
  LICENSES,
  createManifest,
  validateManifest,
};
