// F0191: POST /api/pipeline/retry/:runId endpoint
// Re-runs a FAILED pipeline from the failing stage

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function POST(
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

    // F1345: Query pipeline_runs table with explicit column list
    const { data: pipelineRun, error: runError } = await supabaseAdmin
      .from('content_pipeline_runs')
      .select('id, user_id, status, current_stage')
      .eq('id', runId)
      .single();

    if (runError || !pipelineRun) {
      return NextResponse.json(
        {
          error: 'Pipeline run not found',
          code: 'RUN_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // Owner-only access authorization
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

    // F0191: Only allow retry on FAILED status
    if (pipelineRun.status !== 'FAILED') {
      return NextResponse.json(
        {
          error: 'Can only retry FAILED pipeline runs',
          code: 'INVALID_STATUS',
          request_id: crypto.randomUUID(),
          current_status: pipelineRun.status,
        },
        { status: 400 }
      );
    }

    // F0191: Reset status to RUNNING and clear error, keep completed stage outputs
    // completed_stages array tracks which stages finished successfully
    const { data: updatedRun, error: updateError } = await supabaseAdmin
      .from('content_pipeline_runs')
      .update({
        status: 'RUNNING',
        error_message: null,
        retried_at: new Date().toISOString(),
        // Do NOT reset script_id, research_id, render_id, voiceover_id, publish_id
        // These are reused from completed stages
      })
      .eq('id', runId)
      .select()
      .single();

    if (updateError) {
      console.error('Failed to update pipeline run:', updateError);
      return NextResponse.json(
        {
          error: 'Failed to retry pipeline run',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Emit pg_notify for background worker to pick up
    try {
      await supabaseAdmin.rpc('pg_notify_wrapper', {
        channel: 'pipeline_runs',
        payload: runId,
      });
      console.log(`pg_notify emitted for retried pipeline_run_id: ${runId}`);
    } catch (notifyError) {
      console.error('pg_notify error:', notifyError);
      // Don't fail the request - retry was recorded
    }

    return NextResponse.json({
      success: true,
      run_id: runId,
      status: 'RUNNING',
      current_stage: updatedRun.current_stage,
      message: 'Pipeline retry initiated. Will resume from failing stage.',
    });

  } catch (error) {
    console.error('Pipeline retry error:', error);
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
