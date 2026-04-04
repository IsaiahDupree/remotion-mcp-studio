// F0188: Pipeline run status endpoint: GET /api/pipeline/status/:runId

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(
  request: NextRequest,
  { params }: { params: { runId: string } }
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
    const { runId } = params;

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(runId)) {
      return NextResponse.json(
        {
          error: 'Invalid run ID format',
          code: 'INVALID_RUN_ID',
          request_id: crypto.randomUUID(),
        },
        { status: 400 }
      );
    }

    // Query pipeline_runs table
    const { data: pipelineRun, error: dbError } = await supabaseAdmin
      .from('pipeline_runs')
      .select('user_id, status, current_stage, script_id, research_id, voiceover_id, render_job_id, publish_job_id, error_message, created_at, completed_at')
      .eq('id', runId)
      .single();

    if (dbError || !pipelineRun) {
      return NextResponse.json(
        {
          error: 'Pipeline run not found',
          code: 'RUN_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // Authorization: owner-only access
    if (pipelineRun.user_id !== userId) {
      return NextResponse.json(
        {
          error: 'Forbidden: You do not have access to this pipeline run',
          code: 'FORBIDDEN',
          request_id: crypto.randomUUID(),
        },
        { status: 403 }
      );
    }

    return NextResponse.json({
      run_id: runId,
      status: pipelineRun.status,
      current_stage: pipelineRun.current_stage,
      script_id: pipelineRun.script_id,
      research_id: pipelineRun.research_id,
      voiceover_id: pipelineRun.voiceover_id,
      render_job_id: pipelineRun.render_job_id,
      publish_job_id: pipelineRun.publish_job_id,
      error_message: pipelineRun.error_message,
      created_at: pipelineRun.created_at,
      completed_at: pipelineRun.completed_at,
    });

  } catch (error) {
    console.error('Pipeline status error:', error);
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
