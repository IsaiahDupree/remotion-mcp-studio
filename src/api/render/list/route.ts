// F0127: GET /api/render/list endpoint
// Returns the authenticated user's last 20 render jobs

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    // Bearer token authentication
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

    // Query last 20 render jobs for this user
    const { data: renderJobs, error: dbError } = await supabaseAdmin
      .from('render_jobs')
      .select('id, status, script_id, composition_id, created_at, output_url')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(20);

    if (dbError) {
      console.error('Database error fetching render jobs:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to fetch render jobs',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Format response
    const jobs = (renderJobs || []).map(job => ({
      render_job_id: job.id,
      status: job.status,
      script_id: job.script_id,
      composition_id: job.composition_id,
      created_at: job.created_at,
      output_url: job.output_url,
    }));

    return NextResponse.json({
      success: true,
      jobs,
      count: jobs.length,
    });

  } catch (error) {
    console.error('Render list error:', error);
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
