import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

// F0190: Pipeline run list - GET /api/pipeline/list
export async function GET(request: NextRequest) {
  try {
    // Extract user ID from bearer token
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

    // Fetch user's last 10 pipeline runs
    const { data: pipelineRuns, error } = await supabaseAdmin
      .from('pipeline_runs')
      .select(`
        id,
        status,
        current_stage,
        script_id,
        research_id,
        voiceover_id,
        render_job_id,
        publish_job_id,
        error_message,
        created_at,
        completed_at
      `)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('Database error fetching pipeline runs:', error);
      return NextResponse.json(
        {
          error: 'Failed to fetch pipeline runs',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Return list of pipeline runs
    return NextResponse.json({
      runs: pipelineRuns || [],
      count: pipelineRuns?.length || 0,
      request_id: crypto.randomUUID(),
    });

  } catch (error) {
    console.error('Pipeline list error:', error);
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

// Return 405 for non-GET requests
export async function POST() {
  return NextResponse.json(
    {
      error: 'Method not allowed',
      code: 'METHOD_NOT_ALLOWED',
      request_id: crypto.randomUUID(),
    },
    { status: 405 }
  );
}
