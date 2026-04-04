// F0194: GET /api/pipeline/cost/:runId endpoint
// Aggregates cost from script, research, and voiceover jobs

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

    // Query pipeline_runs table to verify ownership
    const { data: pipelineRun, error: runError } = await supabaseAdmin
      .from('content_pipeline_runs')
      .select('user_id, script_id, research_id, voiceover_id')
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

    // Initialize costs
    let scriptCostUsd = 0;
    let researchCostUsd = 0;
    let voiceoverCostUsd = 0;

    // Fetch script cost if script_id exists
    if (pipelineRun.script_id) {
      const { data: scriptData } = await supabaseAdmin
        .from('content_scripts')
        .select('cost_usd')
        .eq('id', pipelineRun.script_id)
        .single();

      if (scriptData?.cost_usd) {
        scriptCostUsd = parseFloat(scriptData.cost_usd) || 0;
      }
    }

    // Fetch research cost if research_id exists
    if (pipelineRun.research_id) {
      const { data: researchData } = await supabaseAdmin
        .from('content_research_findings')
        .select('cost_usd')
        .eq('id', pipelineRun.research_id)
        .single();

      if (researchData?.cost_usd) {
        researchCostUsd = parseFloat(researchData.cost_usd) || 0;
      }
    }

    // Fetch voiceover cost if voiceover_id exists
    if (pipelineRun.voiceover_id) {
      const { data: voiceoverData } = await supabaseAdmin
        .from('content_voiceover_jobs')
        .select('chars_billed')
        .eq('id', pipelineRun.voiceover_id)
        .single();

      if (voiceoverData?.chars_billed) {
        // ElevenLabs pricing: ~$0.30 per 1000 characters (approximate)
        const charsBilled = parseInt(voiceoverData.chars_billed, 10) || 0;
        voiceoverCostUsd = (charsBilled / 1000) * 0.30;
      }
    }

    // Calculate total
    const totalCostUsd = scriptCostUsd + researchCostUsd + voiceoverCostUsd;

    return NextResponse.json({
      success: true,
      run_id: runId,
      script_cost_usd: scriptCostUsd.toFixed(4),
      research_cost_usd: researchCostUsd.toFixed(4),
      voiceover_cost_usd: voiceoverCostUsd.toFixed(4),
      total_cost_usd: totalCostUsd.toFixed(4),
    });

  } catch (error) {
    console.error('Pipeline cost summary error:', error);
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
