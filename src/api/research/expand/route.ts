// F0061: POST /api/research/expand endpoint registration

// F0214: API route timeout protection
export const maxDuration = 60; // 60 seconds for Perplexity API calls

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { perplexityClient } from '@/lib/perplexity';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

const researchExpandSchema = z.object({
  topic: z.string().min(5).max(500),
  platform: z.enum(['youtube', 'instagram', 'tiktok', 'linkedin']).optional(),
  cacheTtlHours: z.number().int().min(1).max(168).optional().default(24),
});

type ResearchExpandInput = z.infer<typeof researchExpandSchema>;

export async function POST(request: NextRequest) {
  try {
    // F0009: Bearer token authentication with JWT support
    const authResult = await extractUserId(request);

    if (!authResult.success) {
      return NextResponse.json(
        {
          error: authResult.error || 'Authentication failed',
          code: authResult.code || 'UNAUTHORIZED',
          request_id: crypto.randomUUID(),
        },
        { status: 401 }
      );
    }

    const userId = authResult.user_id!;

    const body = await request.json();
    const validationResult = researchExpandSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          code: 'VALIDATION_ERROR',
          request_id: crypto.randomUUID(),
          details: validationResult.error.flatten(),
        },
        { status: 422 }
      );
    }

    const input: ResearchExpandInput = validationResult.data;

    // Check if Perplexity is configured
    if (!perplexityClient.isConfigured()) {
      return NextResponse.json(
        {
          error: 'Research service not configured',
          code: 'SERVICE_UNAVAILABLE',
          request_id: crypto.randomUUID(),
        },
        { status: 503 }
      );
    }

    // Check cache first
    const cacheExpiry = new Date();
    cacheExpiry.setHours(cacheExpiry.getHours() - input.cacheTtlHours);

    // F1345: Select only needed columns instead of *
    const { data: cachedResearch, error: cacheError } = await supabaseAdmin
      .from('research_findings')
      .select('id, topic, stats, quotes, sources, created_at')
      .eq('topic', input.topic)
      .gte('created_at', cacheExpiry.toISOString())
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    // F0084: Full response format with research_id, stats, quotes, cached flag
    if (!cacheError && cachedResearch) {
      // F0471: Deduplicate sources even from cache
      const { deduplicateSourceUrls } = await import('@/lib/research-utils');
      const deduplicatedSources = deduplicateSourceUrls(cachedResearch.sources || []);

      return NextResponse.json({
        research_id: cachedResearch.id,
        topic: cachedResearch.topic,
        stats: cachedResearch.stats || [],
        quotes: cachedResearch.quotes || [],
        sources: deduplicatedSources,
        cached: true,
        created_at: cachedResearch.created_at,
      });
    }

    // Perform new research
    let researchResult;
    try {
      researchResult = await perplexityClient.researchTopic(input.topic);
    } catch (error) {
      // F0088: Perplexity 429 rate limit handling
      if (error instanceof Error && error.message.includes('429')) {
        return NextResponse.json(
          {
            error: 'Rate limit exceeded',
            code: 'RATE_LIMIT_EXCEEDED',
            request_id: crypto.randomUUID(),
          },
          {
            status: 429,
            headers: {
              'Retry-After': '60', // Default 60 seconds
            },
          }
        );
      }
      throw error;
    }

    // F0087: Empty result graceful handling
    const hasResults = researchResult.stats.length > 0 || researchResult.quotes.length > 0;

    // F0471: Deduplicate sources before saving to database
    const { deduplicateSourceUrls } = await import('@/lib/research-utils');
    const deduplicatedSources = deduplicateSourceUrls(researchResult.sources);

    // Save to database (even if empty)
    const { data: savedResearch, error: dbError } = await supabaseAdmin
      .from('research_findings')
      .insert({
        topic: input.topic,
        platform: input.platform,
        facts: researchResult.facts,
        statistics: researchResult.statistics,
        stats: researchResult.stats,
        quotes: researchResult.quotes,
        sources: deduplicatedSources, // F0471: Use deduplicated sources
        summary: researchResult.summary,
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error saving research:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to save research to database',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // F0084: Standalone response format with research_id, stats, quotes
    return NextResponse.json({
      research_id: savedResearch.id,
      topic: savedResearch.topic,
      stats: savedResearch.stats || [],
      quotes: savedResearch.quotes || [],
      sources: savedResearch.sources || [],
      cached: false,
      created_at: savedResearch.created_at,
    });

  } catch (error) {
    console.error('Research expansion error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
        code: 'INTERNAL_ERROR',
        request_id: crypto.randomUUID(),
      },
      { status: 500 }
    );
  }
}

// Return 405 for non-POST requests
export async function GET() {
  return NextResponse.json(
    {
      error: 'Method not allowed',
      code: 'METHOD_NOT_ALLOWED',
      request_id: crypto.randomUUID(),
    },
    { status: 405 }
  );
}
