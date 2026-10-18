// F0091: POST /api/render/start endpoint registration
// F1272: Explicitly use Node.js runtime for heavy operations
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { assembleInputProps } from '@/lib/remotion-props';

// F0092: Request body validation for render start
const renderStartSchema = z.object({
  script_id: z.string().uuid('script_id must be a valid UUID'),
  composition_id: z.enum(['DefaultVideo', 'UGCStyle', 'NewsStyle', 'TutorialStyle'], {
    errorMap: () => ({ message: 'composition_id must be a valid composition name' })
  }),
  video_url: z.string().url('video_url must be a valid URL').optional(),
  platform: z.enum(['youtube', 'instagram', 'tiktok', 'linkedin']).optional(),
});

type RenderStartInput = z.infer<typeof renderStartSchema>;

export async function POST(request: NextRequest) {
  try {
    // Bearer token authentication with JWT support
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
    const validationResult = renderStartSchema.safeParse(body);

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

    const input: RenderStartInput = validationResult.data;

    // F0093: script_id existence check before render job creation
    const { data: scriptRecord, error: scriptError } = await supabaseAdmin
      .from('content_scripts')
      .select('id, hook, body_points, cta, script_text, platform, estimated_duration_sec')
      .eq('id', input.script_id)
      .single();

    if (scriptError || !scriptRecord) {
      return NextResponse.json(
        {
          error: 'Script not found',
          code: 'SCRIPT_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // F0101-F0110: Assemble InputProps from script data
    // F0102, F0106, F0107: Now includes brandName, editPlan, faceBoxes
    const inputProps = await assembleInputProps({
      scriptText: scriptRecord.script_text,
      hook: scriptRecord.hook,
      platform: input.platform || scriptRecord.platform,
      estimatedDurationSec: scriptRecord.estimated_duration_sec,
      sourceVideoUrl: input.video_url,
      userId,  // F0102: Pass userId for brandName lookup
    });

    // F0095: Create render_jobs row with QUEUED status
    // F0110: Store assembled InputProps JSON in render_jobs row
    // F1102: Include user_id and progress_pct=0
    const { data: renderJob, error: dbError } = await supabaseAdmin
      .from('render_jobs')
      .insert({
        script_id: input.script_id,
        user_id: userId,
        composition_id: input.composition_id,
        platform: input.platform || scriptRecord.platform,
        status: 'QUEUED',
        video_url: input.video_url,
        input_props_json: inputProps,
        progress_pct: 0,
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error creating render job:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to create render job',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // F0100: pg_notify job dispatch alternative for background execution
    // Emit pg_notify event so a listening worker can pick up the job
    try {
      await supabaseAdmin.rpc('pg_notify_wrapper', {
        channel: 'render_jobs',
        payload: renderJob.id,
      });
      console.log(`pg_notify emitted for render_job_id: ${renderJob.id}`);
    } catch (notifyError) {
      // Log error but don't fail the request - job is still queued
      console.error('pg_notify error:', notifyError);
    }

    // F0096: Return render_job_id immediately after queue
    return NextResponse.json({
      success: true,
      render_job_id: renderJob.id,
      status: 'QUEUED',
      message: 'Render job queued successfully',
    });

  } catch (error) {
    console.error('Render start error:', error);
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
