// F0232: GET /api/scripts/list endpoint
// Returns user's script history

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    // Authentication
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

    // Parse query params for pagination
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1', 10);
    const limit = parseInt(searchParams.get('limit') || '20', 10);

    // Validate pagination params
    const validatedPage = Math.max(1, page);
    const validatedLimit = Math.min(Math.max(1, limit), 100); // Max 100 per page
    const offset = (validatedPage - 1) * validatedLimit;

    // Query content_scripts table for user's scripts
    const { data: scripts, error: scriptsError, count } = await supabaseAdmin
      .from('content_scripts')
      .select('id, topic, platform, tone, hook, estimated_duration_sec, created_at, cost_usd', { count: 'exact' })
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + validatedLimit - 1);

    if (scriptsError) {
      console.error('Database error fetching scripts:', scriptsError);
      return NextResponse.json(
        {
          error: 'Failed to fetch scripts',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Format response
    const scriptList = (scripts || []).map(script => ({
      script_id: script.id,
      topic: script.topic,
      platform: script.platform,
      tone: script.tone,
      hook: script.hook,
      estimated_duration_sec: script.estimated_duration_sec,
      created_at: script.created_at,
      cost_usd: script.cost_usd,
    }));

    const totalCount = count || 0;
    const totalPages = Math.ceil(totalCount / validatedLimit);

    return NextResponse.json({
      success: true,
      scripts: scriptList,
      pagination: {
        page: validatedPage,
        limit: validatedLimit,
        total_count: totalCount,
        total_pages: totalPages,
      },
    });

  } catch (error) {
    console.error('Script list error:', error);
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
