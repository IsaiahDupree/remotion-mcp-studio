// F0121: GET /api/render/logs/:jobId endpoint
// Returns the last 100 log lines from render_logs table

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
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
    const { jobId } = params;

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(jobId)) {
      return NextResponse.json(
        {
          error: 'Invalid job ID format',
          code: 'INVALID_JOB_ID',
          request_id: crypto.randomUUID(),
        },
        { status: 400 }
      );
    }

    // Verify render job exists and user has access
    const { data: renderJob, error: jobError } = await supabaseAdmin
      .from('render_jobs')
      .select('user_id')
      .eq('id', jobId)
      .single();

    if (jobError || !renderJob) {
      return NextResponse.json(
        {
          error: 'Render job not found',
          code: 'JOB_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // Owner-only access authorization
    if (renderJob.user_id !== userId) {
      return NextResponse.json(
        {
          error: 'Forbidden: You do not have access to this render job',
          code: 'FORBIDDEN',
          request_id: crypto.randomUUID(),
        },
        { status: 403 }
      );
    }

    // Fetch last 100 log lines ordered by line_number DESC
    const { data: logs, error: logsError } = await supabaseAdmin
      .from('render_logs')
      .select('line_number, source, content, created_at')
      .eq('render_job_id', jobId)
      .order('line_number', { ascending: false })
      .limit(100);

    if (logsError) {
      console.error('Error fetching render logs:', logsError);
      return NextResponse.json(
        {
          error: 'Failed to fetch logs',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Format log lines as string array (most recent first)
    const lines = (logs || []).map(log =>
      `[${log.source}] ${log.content}`
    );

    return NextResponse.json({
      success: true,
      job_id: jobId,
      lines,
      count: lines.length,
    });

  } catch (error) {
    console.error('Render logs error:', error);
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
