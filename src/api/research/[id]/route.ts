/**
 * F0488: GET /api/research/[id] — retrieve research findings
 *
 * Returns research findings data for a given research ID.
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Bearer token authentication (optional - research may be accessible by ID alone for now)
    const authResult = await extractUserId(request);
    const userId = authResult.user_id || null;

    const { id: researchId } = params;

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(researchId)) {
      return NextResponse.json(
        {
          error: 'Invalid research ID format',
          code: 'INVALID_ID',
          request_id: crypto.randomUUID(),
        },
        { status: 400 }
      );
    }

    // Fetch research findings
    const { data: findings, error: findingsError } = await supabaseAdmin
      .from('research_findings')
      .select('id, topic, stats, quotes_with_attribution, sources, created_at')
      .eq('id', researchId)
      .single();

    if (findingsError || !findings) {
      return NextResponse.json(
        {
          error: 'Research findings not found',
          code: 'NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // If user is authenticated, check ownership (optional - can be removed for public access)
    // For now, allowing public read access to research findings

    return NextResponse.json(
      {
        success: true,
        id: findings.id,
        topic: findings.topic,
        stats: findings.stats || [],
        quotes: findings.quotes_with_attribution || [],
        sources: findings.sources || [],
        created_at: findings.created_at,
        request_id: crypto.randomUUID(),
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Research findings retrieval error:', error);
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

export async function OPTIONS(request: NextRequest) {
  return NextResponse.json({}, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
