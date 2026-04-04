/**
 * Remotion MCP Marketplace — API Server
 *
 * REST API for the template marketplace with Stripe integration.
 * Run standalone: node marketplace/server.js
 * Or integrated into the MCP server via marketplace tools.
 *
 * Endpoints:
 *   GET  /api/marketplace/browse         — Browse listings by category
 *   GET  /api/marketplace/search?q=      — Search templates
 *   GET  /api/marketplace/template/:id   — Get template details
 *   POST /api/marketplace/publish        — Publish a template (seller)
 *   POST /api/marketplace/purchase       — Purchase a template (Stripe checkout)
 *   GET  /api/marketplace/my/templates   — Seller's templates
 *   GET  /api/marketplace/my/purchases   — Buyer's purchased templates
 *   POST /api/marketplace/review         — Submit a review
 *   POST /api/marketplace/webhook/stripe — Stripe webhook for payment confirmation
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { URL } = require('url');
const { CATEGORIES, LICENSES, createManifest, validateManifest } = require('./schema');

const DATA_DIR = path.join(__dirname, 'data');
const LISTINGS_FILE = path.join(DATA_DIR, 'listings.json');
const PURCHASES_FILE = path.join(DATA_DIR, 'purchases.json');
const SELLERS_FILE = path.join(DATA_DIR, 'sellers.json');
const TEMPLATES_DIR = path.join(DATA_DIR, 'templates');
const PORT = process.env.MARKETPLACE_PORT || 4200;
const PLATFORM_FEE = 0.15; // 15%

// ── Data Store ───────────────────────────────────────────────────────────────

function ensureDataDir() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(TEMPLATES_DIR, { recursive: true });
  if (!fs.existsSync(LISTINGS_FILE)) fs.writeFileSync(LISTINGS_FILE, '[]');
  if (!fs.existsSync(PURCHASES_FILE)) fs.writeFileSync(PURCHASES_FILE, '[]');
  if (!fs.existsSync(SELLERS_FILE)) fs.writeFileSync(SELLERS_FILE, '[]');
}

function readJSON(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return []; }
}

function writeJSON(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
}

// ── Listings CRUD ────────────────────────────────────────────────────────────

function getAllListings() { return readJSON(LISTINGS_FILE); }
function saveListing(listing) {
  const all = getAllListings();
  const idx = all.findIndex(l => l.manifest.id === listing.manifest.id);
  if (idx >= 0) all[idx] = listing;
  else all.push(listing);
  writeJSON(LISTINGS_FILE, all);
  return listing;
}

function getListingById(id) {
  return getAllListings().find(l => l.manifest.id === id) || null;
}

function browseListings({ category, sort = 'popular', limit = 20, offset = 0 }) {
  let listings = getAllListings().filter(l => l.status === 'published');
  if (category) listings = listings.filter(l => l.manifest.category === category);

  switch (sort) {
    case 'newest': listings.sort((a, b) => b.manifest.stats.publishedAt.localeCompare(a.manifest.stats.publishedAt)); break;
    case 'popular': listings.sort((a, b) => b.manifest.stats.downloads - a.manifest.stats.downloads); break;
    case 'rating': listings.sort((a, b) => b.manifest.stats.rating - a.manifest.stats.rating); break;
    case 'price-low': listings.sort((a, b) => a.manifest.pricing.price - b.manifest.pricing.price); break;
    case 'price-high': listings.sort((a, b) => b.manifest.pricing.price - a.manifest.pricing.price); break;
  }

  return {
    total: listings.length,
    listings: listings.slice(offset, offset + limit).map(l => ({
      id: l.manifest.id,
      name: l.manifest.name,
      description: l.manifest.description,
      category: l.manifest.category,
      author: l.manifest.author,
      price: l.manifest.pricing.price,
      currency: l.manifest.pricing.currency,
      license: l.manifest.license,
      rating: l.manifest.stats.rating,
      downloads: l.manifest.stats.downloads,
      thumbnailUrl: l.thumbnailUrl,
      tags: l.manifest.tags,
    })),
  };
}

function searchListings(query, { limit = 20, offset = 0 } = {}) {
  const q = query.toLowerCase();
  const listings = getAllListings()
    .filter(l => l.status === 'published')
    .filter(l =>
      l.manifest.name.toLowerCase().includes(q) ||
      l.manifest.description.toLowerCase().includes(q) ||
      l.manifest.tags.some(t => t.toLowerCase().includes(q)) ||
      l.manifest.author.toLowerCase().includes(q)
    )
    .sort((a, b) => {
      // Prioritize name matches, then tag matches, then description
      const aNameMatch = a.manifest.name.toLowerCase().includes(q) ? 2 : 0;
      const bNameMatch = b.manifest.name.toLowerCase().includes(q) ? 2 : 0;
      const aTagMatch = a.manifest.tags.some(t => t.toLowerCase().includes(q)) ? 1 : 0;
      const bTagMatch = b.manifest.tags.some(t => t.toLowerCase().includes(q)) ? 1 : 0;
      return (bNameMatch + bTagMatch) - (aNameMatch + aTagMatch);
    });

  return {
    query,
    total: listings.length,
    listings: listings.slice(offset, offset + limit).map(l => ({
      id: l.manifest.id,
      name: l.manifest.name,
      description: l.manifest.description,
      category: l.manifest.category,
      author: l.manifest.author,
      price: l.manifest.pricing.price,
      currency: l.manifest.pricing.currency,
      rating: l.manifest.stats.rating,
      downloads: l.manifest.stats.downloads,
      tags: l.manifest.tags,
    })),
  };
}

// ── Publish ──────────────────────────────────────────────────────────────────

function publishTemplate(manifestInput, sellerId) {
  const manifest = createManifest({
    ...manifestInput,
    authorId: sellerId,
  });

  const validation = validateManifest(manifest);
  if (!validation.valid) return { success: false, errors: validation.errors };

  const listing = {
    manifest,
    status: manifest.pricing.price === 0 ? 'published' : 'pending_review',
    storagePath: path.join(TEMPLATES_DIR, manifest.id),
    thumbnailUrl: `/api/marketplace/assets/${manifest.id}/thumbnail.png`,
    previewUrl: manifest.assets.preview ? `/api/marketplace/assets/${manifest.id}/preview.mp4` : null,
    reviews: [],
    earnings: { totalRevenue: 0, totalSales: 0, platformFee: PLATFORM_FEE },
  };

  // Create template directory
  fs.mkdirSync(listing.storagePath, { recursive: true });
  fs.writeFileSync(path.join(listing.storagePath, 'manifest.json'), JSON.stringify(manifest, null, 2));

  saveListing(listing);

  return {
    success: true,
    templateId: manifest.id,
    status: listing.status,
    message: listing.status === 'published'
      ? 'Free template published immediately!'
      : 'Template submitted for review. You will be notified when approved.',
  };
}

// ── Purchase ─────────────────────────────────────────────────────────────────

function initiatePurchase(templateId, buyerId) {
  const listing = getListingById(templateId);
  if (!listing) return { success: false, error: 'Template not found' };
  if (listing.status !== 'published') return { success: false, error: 'Template not available' };

  // Check if already purchased
  const purchases = readJSON(PURCHASES_FILE);
  const existing = purchases.find(p => p.templateId === templateId && p.buyerId === buyerId);
  if (existing) return { success: false, error: 'Already purchased', purchaseId: existing.id };

  // Free templates — instant purchase
  if (listing.manifest.pricing.price === 0) {
    const purchase = {
      id: `pur_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`,
      templateId,
      buyerId,
      amount: 0,
      currency: 'usd',
      status: 'completed',
      createdAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
    };
    purchases.push(purchase);
    writeJSON(PURCHASES_FILE, purchases);

    // Update download count
    listing.manifest.stats.downloads++;
    saveListing(listing);

    return { success: true, purchaseId: purchase.id, status: 'completed', message: 'Free template added to your collection!' };
  }

  // Paid templates — create Stripe checkout session
  const stripeKey = process.env.STRIPE_SECRET_KEY;
  if (!stripeKey) {
    return { success: false, error: 'STRIPE_SECRET_KEY not configured. Set it in .env to enable purchases.' };
  }

  const purchaseId = `pur_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  const purchase = {
    id: purchaseId,
    templateId,
    buyerId,
    amount: listing.manifest.pricing.price,
    currency: listing.manifest.pricing.currency || 'usd',
    status: 'pending',
    createdAt: new Date().toISOString(),
    completedAt: null,
    stripeSessionId: null,
  };
  purchases.push(purchase);
  writeJSON(PURCHASES_FILE, purchases);

  // Return info needed to create Stripe checkout
  return {
    success: true,
    purchaseId,
    status: 'pending',
    amount: listing.manifest.pricing.price,
    currency: listing.manifest.pricing.currency || 'usd',
    templateName: listing.manifest.name,
    message: 'Use Stripe checkout to complete purchase.',
    checkoutParams: {
      mode: 'payment',
      line_items: [{
        price_data: {
          currency: listing.manifest.pricing.currency || 'usd',
          product_data: {
            name: listing.manifest.name,
            description: listing.manifest.description,
          },
          unit_amount: listing.manifest.pricing.price,
        },
        quantity: 1,
      }],
      metadata: { purchaseId, templateId, buyerId },
    },
  };
}

function completePurchase(purchaseId) {
  const purchases = readJSON(PURCHASES_FILE);
  const purchase = purchases.find(p => p.id === purchaseId);
  if (!purchase) return { success: false, error: 'Purchase not found' };

  purchase.status = 'completed';
  purchase.completedAt = new Date().toISOString();
  writeJSON(PURCHASES_FILE, purchases);

  // Update listing stats
  const listing = getListingById(purchase.templateId);
  if (listing) {
    listing.manifest.stats.downloads++;
    listing.earnings.totalSales++;
    listing.earnings.totalRevenue += purchase.amount;
    saveListing(listing);
  }

  return { success: true, purchaseId, status: 'completed' };
}

function getUserPurchases(buyerId) {
  return readJSON(PURCHASES_FILE)
    .filter(p => p.buyerId === buyerId && p.status === 'completed')
    .map(p => {
      const listing = getListingById(p.templateId);
      return {
        purchaseId: p.id,
        templateId: p.templateId,
        templateName: listing?.manifest.name || 'Unknown',
        author: listing?.manifest.author || 'Unknown',
        amount: p.amount,
        purchasedAt: p.completedAt,
      };
    });
}

function getSellerTemplates(sellerId) {
  return getAllListings()
    .filter(l => l.manifest.authorId === sellerId)
    .map(l => ({
      id: l.manifest.id,
      name: l.manifest.name,
      status: l.status,
      price: l.manifest.pricing.price,
      downloads: l.manifest.stats.downloads,
      rating: l.manifest.stats.rating,
      revenue: l.earnings.totalRevenue,
      sales: l.earnings.totalSales,
    }));
}

// ── Reviews ──────────────────────────────────────────────────────────────────

function addReview(templateId, userId, userName, rating, title, body) {
  const listing = getListingById(templateId);
  if (!listing) return { success: false, error: 'Template not found' };

  // Check if already reviewed
  if (listing.reviews.some(r => r.userId === userId)) {
    return { success: false, error: 'You already reviewed this template' };
  }

  const review = {
    id: `rev_${Date.now()}`,
    templateId,
    userId,
    userName,
    rating: Math.min(5, Math.max(1, rating)),
    title,
    body,
    createdAt: new Date().toISOString(),
  };
  listing.reviews.push(review);

  // Recalculate average rating
  const totalRating = listing.reviews.reduce((sum, r) => sum + r.rating, 0);
  listing.manifest.stats.rating = Math.round((totalRating / listing.reviews.length) * 10) / 10;
  listing.manifest.stats.reviews = listing.reviews.length;

  saveListing(listing);
  return { success: true, reviewId: review.id };
}

// ── HTTP Server ──────────────────────────────────────────────────────────────

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; if (body.length > 1e7) reject(new Error('Body too large')); });
    req.on('end', () => { try { resolve(JSON.parse(body)); } catch { resolve({}); } });
  });
}

function json(res, data, status = 200) {
  res.writeHead(status, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
  res.end(JSON.stringify(data, null, 2));
}

async function handleRequest(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = url.pathname;
  const method = req.method;

  // CORS preflight
  if (method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    return res.end();
  }

  try {
    // ── Browse ──
    if (method === 'GET' && pathname === '/api/marketplace/browse') {
      const category = url.searchParams.get('category') || null;
      const sort = url.searchParams.get('sort') || 'popular';
      const limit = parseInt(url.searchParams.get('limit') || '20');
      const offset = parseInt(url.searchParams.get('offset') || '0');
      return json(res, browseListings({ category, sort, limit, offset }));
    }

    // ── Search ──
    if (method === 'GET' && pathname === '/api/marketplace/search') {
      const q = url.searchParams.get('q') || '';
      if (!q) return json(res, { error: 'Query parameter q is required' }, 400);
      return json(res, searchListings(q));
    }

    // ── Get Template Details ──
    if (method === 'GET' && pathname.startsWith('/api/marketplace/template/')) {
      const id = pathname.split('/').pop();
      const listing = getListingById(id);
      if (!listing) return json(res, { error: 'Template not found' }, 404);
      return json(res, {
        ...listing.manifest,
        status: listing.status,
        reviews: listing.reviews.slice(0, 10),
        previewUrl: listing.previewUrl,
        thumbnailUrl: listing.thumbnailUrl,
      });
    }

    // ── Publish ──
    if (method === 'POST' && pathname === '/api/marketplace/publish') {
      const body = await parseBody(req);
      const sellerId = body.sellerId || 'default';
      return json(res, publishTemplate(body.manifest || body, sellerId));
    }

    // ── Purchase ──
    if (method === 'POST' && pathname === '/api/marketplace/purchase') {
      const body = await parseBody(req);
      if (!body.templateId) return json(res, { error: 'templateId is required' }, 400);
      const buyerId = body.buyerId || 'default';
      return json(res, initiatePurchase(body.templateId, buyerId));
    }

    // ── My Templates (Seller) ──
    if (method === 'GET' && pathname === '/api/marketplace/my/templates') {
      const sellerId = url.searchParams.get('sellerId') || 'default';
      return json(res, { templates: getSellerTemplates(sellerId) });
    }

    // ── My Purchases (Buyer) ──
    if (method === 'GET' && pathname === '/api/marketplace/my/purchases') {
      const buyerId = url.searchParams.get('buyerId') || 'default';
      return json(res, { purchases: getUserPurchases(buyerId) });
    }

    // ── Submit Review ──
    if (method === 'POST' && pathname === '/api/marketplace/review') {
      const body = await parseBody(req);
      if (!body.templateId || !body.rating) return json(res, { error: 'templateId and rating are required' }, 400);
      return json(res, addReview(
        body.templateId,
        body.userId || 'default',
        body.userName || 'Anonymous',
        body.rating,
        body.title || '',
        body.body || ''
      ));
    }

    // ── Categories ──
    if (method === 'GET' && pathname === '/api/marketplace/categories') {
      return json(res, CATEGORIES);
    }

    // ── Stripe Webhook ──
    if (method === 'POST' && pathname === '/api/marketplace/webhook/stripe') {
      const body = await parseBody(req);
      if (body.type === 'checkout.session.completed') {
        const { purchaseId } = body.data?.object?.metadata || {};
        if (purchaseId) completePurchase(purchaseId);
        return json(res, { received: true });
      }
      return json(res, { received: true });
    }

    // ── Health ──
    if (method === 'GET' && pathname === '/api/marketplace/health') {
      const listings = getAllListings();
      return json(res, {
        status: 'ok',
        totalListings: listings.length,
        publishedListings: listings.filter(l => l.status === 'published').length,
        categories: Object.keys(CATEGORIES).length,
      });
    }

    // 404
    json(res, { error: 'Not found' }, 404);
  } catch (err) {
    json(res, { error: err.message }, 500);
  }
}

// ── Start Server ─────────────────────────────────────────────────────────────

function startMarketplaceServer(port = PORT) {
  ensureDataDir();
  const server = http.createServer(handleRequest);
  server.listen(port, () => {
    console.log(`Marketplace API running on http://localhost:${port}`);
    console.log(`  Browse:    http://localhost:${port}/api/marketplace/browse`);
    console.log(`  Search:    http://localhost:${port}/api/marketplace/search?q=tiktok`);
    console.log(`  Health:    http://localhost:${port}/api/marketplace/health`);
  });
  return server;
}

// Run standalone or export for integration
if (require.main === module) {
  startMarketplaceServer();
} else {
  module.exports = {
    startMarketplaceServer,
    browseListings,
    searchListings,
    getListingById,
    publishTemplate,
    initiatePurchase,
    completePurchase,
    getUserPurchases,
    getSellerTemplates,
    addReview,
    CATEGORIES,
    LICENSES,
  };
}
