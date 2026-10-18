// F0181: End-to-end pipeline orchestrator: POST /api/pipeline/run
// Runs Research → Script → Voiceover → Render → Publish in sequence

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { env } from '@/lib/env';

// Pipeline run request schema
const pipelineRunSchema = z.object({
  topic: z.string().min(5).max(500),
  platform: z.enum(['youtube', 'instagram', 'tiktok', 'linkedin', 'facebook']),
  tone: z.enum(['professional', 'casual', 'educational', 'entertaining', 'inspirational', 'controversial', 'storytelling']),
  target_duration_sec: z.number().min(15).max(600),
  voice_id: z.string().optional(),
  platforms: z.array(z.enum(['youtube', 'instagram', 'tiktok', 'linkedin', 'facebook'])).min(1),
  caption_template: z.string().optional(),
  composition_id: z.string().optional().default('DefaultVideo'),
  webhook_url: z.string().url().optional(), // F0193: Optional webhook for completion notification
});

type PipelineRunInput = z.infer<typeof pipelineRunSchema>;

// F0193: Helper to send webhook notification on pipeline completion/failure
async function sendWebhookNotification(
  webhookUrl: string,
  runId: string,
  status: 'COMPLETED' | 'FAILED',
  outputUrl?: string
) {
  try {
    const payload = {
      run_id: runId,
      status,
      output_url: outputUrl || null,
    };

    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    if (!response.ok) {
      console.warn(`Webhook notification failed: ${response.status} ${response.statusText}`);
    } else {
      console.log(`✓ Webhook notification sent to ${webhookUrl}`);
    }
  } catch (error) {
    // F0193: Do not throw error if webhook is unreachable - just log
    console.warn('Webhook notification error (ignored):', error instanceof Error ? error.message : 'Unknown error');
  }
}

// Helper function to execute pipeline stages
async function executePipeline(pipelineRunId: string, input: PipelineRunInput, userId: string) {
  try {
    const baseUrl = env.supabaseUrl.replace('.supabase.co', '.vercel.app') || 'http://localhost:3001';
    const authHeader = `Bearer ${env.scriptApiSecret}`;

    // F0183: Stage 1 - Research expansion
    await supabaseAdmin
      .from('pipeline_runs')
      .update({ current_stage: 'research', status: 'RUNNING' })
      .eq('id', pipelineRunId);

    const researchResponse = await fetch(`${baseUrl}/api/research/expand`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({ topic: input.topic }),
    });

    if (!researchResponse.ok) {
      const errorData = await researchResponse.json().catch(() => ({}));
      throw new Error(`Research failed: ${errorData.error || researchResponse.statusText}`);
    }

    const researchData = await researchResponse.json();
    const researchId = researchData.research_id;

    await supabaseAdmin
      .from('pipeline_runs')
      .update({ research_id: researchId })
      .eq('id', pipelineRunId);

    // F0184: Stage 2 - Script generation
    await supabaseAdmin
      .from('pipeline_runs')
      .update({ current_stage: 'script' })
      .eq('id', pipelineRunId);

    const scriptResponse = await fetch(`${baseUrl}/api/scripts/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        topic: input.topic,
        platform: input.platform,
        tone: input.tone,
        targetLength: input.target_duration_sec,
        researchId: researchId,
      }),
    });

    if (!scriptResponse.ok) {
      const errorData = await scriptResponse.json().catch(() => ({}));
      throw new Error(`Script generation failed: ${errorData.error || scriptResponse.statusText}`);
    }

    const scriptData = await scriptResponse.json();
    const scriptId = scriptData.script_id;
    const scriptHook = scriptData.hook || '';

    await supabaseAdmin
      .from('pipeline_runs')
      .update({ script_id: scriptId })
      .eq('id', pipelineRunId);

    // F0185: Stage 3 - Voiceover generation
    await supabaseAdmin
      .from('pipeline_runs')
      .update({ current_stage: 'voiceover' })
      .eq('id', pipelineRunId);

    const voiceoverResponse = await fetch(`${baseUrl}/api/voiceover/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        script_id: scriptId,
        voice_id: input.voice_id,
      }),
    });

    if (!voiceoverResponse.ok) {
      const errorData = await voiceoverResponse.json().catch(() => ({}));
      throw new Error(`Voiceover generation failed: ${errorData.error || voiceoverResponse.statusText}`);
    }

    const voiceoverData = await voiceoverResponse.json();
    const voiceoverId = voiceoverData.voiceover_id;

    await supabaseAdmin
      .from('pipeline_runs')
      .update({ voiceover_id: voiceoverId })
      .eq('id', pipelineRunId);

    // F0186: Stage 4 - Render start
    await supabaseAdmin
      .from('pipeline_runs')
      .update({ current_stage: 'render' })
      .eq('id', pipelineRunId);

    const renderResponse = await fetch(`${baseUrl}/api/render/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        script_id: scriptId,
        composition_id: input.composition_id,
      }),
    });

    if (!renderResponse.ok) {
      const errorData = await renderResponse.json().catch(() => ({}));
      throw new Error(`Render start failed: ${errorData.error || renderResponse.statusText}`);
    }

    const renderData = await renderResponse.json();
    const renderJobId = renderData.render_job_id;

    await supabaseAdmin
      .from('pipeline_runs')
      .update({ render_job_id: renderJobId })
      .eq('id', pipelineRunId);

    // F0187: Stage 5 - Wait for render completion and publish
    await supabaseAdmin
      .from('pipeline_runs')
      .update({ current_stage: 'publishing' })
      .eq('id', pipelineRunId);

    // Poll render status every 5 seconds (max 10 minutes = 120 attempts)
    let renderComplete = false;
    let outputUrl: string | null = null;
    const maxAttempts = 120;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds

      const statusResponse = await fetch(`${baseUrl}/api/render/status/${renderJobId}`, {
        headers: { 'Authorization': authHeader },
      });

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();

        if (statusData.status === 'COMPLETED') {
          renderComplete = true;
          outputUrl = statusData.output_url;
          break;
        } else if (statusData.status === 'FAILED') {
          throw new Error(`Render failed: ${statusData.error_message || 'Unknown error'}`);
        }
      }
    }

    if (!renderComplete || !outputUrl) {
      throw new Error('Render timeout after 10 minutes');
    }

    // Upload to Blotato
    const uploadResponse = await fetch(`${baseUrl}/api/publish/upload-media`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        output_url: outputUrl,
        render_job_id: renderJobId,
        platforms: input.platforms,
      }),
    });

    if (!uploadResponse.ok) {
      const errorData = await uploadResponse.json().catch(() => ({}));
      throw new Error(`Media upload failed: ${errorData.error || uploadResponse.statusText}`);
    }

    // F0192: Caption template variable substitution
    let finalCaption = input.caption_template || `${input.topic}\n\nGenerated with Content AI Pipeline`;

    // Substitute template variables: {topic}, {hook}, {platform}
    if (input.caption_template) {
      finalCaption = input.caption_template
        .replace(/{topic}/g, input.topic)
        .replace(/{hook}/g, scriptHook)
        .replace(/{platform}/g, input.platform);
    }

    // Publish to platforms
    const publishResponse = await fetch(`${baseUrl}/api/publish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        render_job_id: renderJobId,
        platforms: input.platforms,
        caption: finalCaption,
        hashtags: [],
      }),
    });

    if (!publishResponse.ok) {
      const errorData = await publishResponse.json().catch(() => ({}));
      throw new Error(`Publishing failed: ${errorData.error || publishResponse.statusText}`);
    }

    const publishData = await publishResponse.json();
    const publishJobId = publishData.publish_job_id;

    await supabaseAdmin
      .from('pipeline_runs')
      .update({ publish_job_id: publishJobId })
      .eq('id', pipelineRunId);

    // F0195: Mark pipeline as COMPLETE
    await supabaseAdmin
      .from('pipeline_runs')
      .update({
        status: 'COMPLETED',
        current_stage: 'completed',
        completed_at: new Date().toISOString(),
      })
      .eq('id', pipelineRunId);

    console.log(`✓ Pipeline ${pipelineRunId} completed successfully`);

    // F0193: Send webhook notification if configured
    const { data: pipelineData } = await supabaseAdmin
      .from('pipeline_runs')
      .select('webhook_url')
      .eq('id', pipelineRunId)
      .single();

    if (pipelineData?.webhook_url) {
      await sendWebhookNotification(
        pipelineData.webhook_url,
        pipelineRunId,
        'COMPLETED',
        outputUrl || undefined
      );
    }

  } catch (error) {
    // F0189: Mark pipeline as FAILED
    console.error(`Pipeline ${pipelineRunId} failed:`, error);

    await supabaseAdmin
      .from('pipeline_runs')
      .update({
        status: 'FAILED',
        error_message: error instanceof Error ? error.message : 'Unknown error',
      })
      .eq('id', pipelineRunId);

    // F0193: Send webhook notification on failure
    const { data: pipelineData } = await supabaseAdmin
      .from('pipeline_runs')
      .select('webhook_url')
      .eq('id', pipelineRunId)
      .single();

    if (pipelineData?.webhook_url) {
      await sendWebhookNotification(
        pipelineData.webhook_url,
        pipelineRunId,
        'FAILED'
      );
    }
  }
}

export async function POST(request: NextRequest) {
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

    const body = await request.json();
    const validationResult = pipelineRunSchema.safeParse(body);

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

    const input: PipelineRunInput = validationResult.data;

    // Create pipeline_runs row
    const { data: pipelineRun, error: dbError } = await supabaseAdmin
      .from('pipeline_runs')
      .insert({
        user_id: userId,
        status: 'QUEUED',
        current_stage: 'queued',
        webhook_url: input.webhook_url || null, // F0193: Store webhook URL for completion notification
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error creating pipeline run:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to create pipeline run',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    const pipelineRunId = pipelineRun.id;

    // Execute pipeline asynchronously (non-blocking)
    executePipeline(pipelineRunId, input, userId).catch(err => {
      console.error('Pipeline execution error:', err);
    });

    // Return pipeline_run_id immediately
    return NextResponse.json({
      pipeline_run_id: pipelineRunId,
      status: 'QUEUED',
      message: 'Pipeline started. Check status at /api/pipeline/status/:runId',
    });

  } catch (error) {
    console.error('Pipeline run error:', error);
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
