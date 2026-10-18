// F0269: POST /api/publish/webhook - Accept Blotato push status updates
// Webhook fallback: if webhook fires, cancel remaining polling for that job
// F0797: SSRF prevention for webhook URLs

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { mapBlotatoStatus, type InternalStatus } from '@/lib/blotato-polling';
import { validateWebhookURL } from '@/lib/security/ssrf-prevention';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Blotato webhook payload structure:
    // {
    //   post_submission_id: string,
    //   status: 'queued' | 'processing' | 'published' | 'failed' | 'rejected',
    //   post_url?: string,
    //   error?: string
    // }

    const { post_submission_id, status: blotatoStatus, post_url, error } = body;

    if (!post_submission_id || !blotatoStatus) {
      console.warn('[Webhook] Missing required fields:', { post_submission_id, blotatoStatus });
      return NextResponse.json(
        {
          error: 'Missing post_submission_id or status',
          code: 'INVALID_PAYLOAD',
        },
        { status: 400 }
      );
    }

    // F0797: SSRF prevention - validate webhook URL if provided
    if (post_url) {
      const urlValidation = validateWebhookURL(post_url);
      if (!urlValidation.valid) {
        console.warn('[Webhook] SSRF violation:', urlValidation.error);
        return NextResponse.json(
          {
            error: urlValidation.error || 'Invalid webhook URL',
            code: 'SSRF_VIOLATION',
          },
          { status: 400 }
        );
      }
    }

    // Find the publish_result with this submission ID
    const { data: publishResult, error: resultError } = await supabaseAdmin
      .from('publish_results')
      .select('id, publish_job_id, platform')
      .eq('post_submission_id', post_submission_id)
      .single();

    if (resultError || !publishResult) {
      console.warn(`[Webhook] No publish_result found for submission ${post_submission_id}`);
      return NextResponse.json(
        {
          error: 'Submission not found',
          code: 'NOT_FOUND',
        },
        { status: 404 }
      );
    }

    // Map Blotato status to internal status
    const internalStatus: InternalStatus = mapBlotatoStatus(blotatoStatus);
    const isTerminal = internalStatus === 'PUBLISHED' || internalStatus === 'FAILED';

    // Update the publish_result with the webhook status
    const updateData: any = {
      status: internalStatus,
      updated_at: new Date().toISOString(),
    };

    if (internalStatus === 'PUBLISHED' && post_url) {
      updateData.post_url = post_url;
    }

    if (internalStatus === 'FAILED' && error) {
      updateData.error_message = error;
    }

    await supabaseAdmin
      .from('publish_results')
      .update(updateData)
      .eq('id', publishResult.id);

    console.log(
      `[Webhook] Updated submission ${post_submission_id} to ${internalStatus} (${blotatoStatus})`
    );

    // F0269: If terminal state reached via webhook, check if we should cancel polling
    if (isTerminal) {
      // Check if all results for this job are now in terminal state
      const { data: allResults } = await supabaseAdmin
        .from('publish_results')
        .select('status')
        .eq('publish_job_id', publishResult.publish_job_id);

      const allTerminal = allResults?.every(r =>
        r.status === 'PUBLISHED' || r.status === 'FAILED'
      ) || false;

      if (allTerminal) {
        // All results are terminal - cancel polling by marking the job complete
        const anyFailed = allResults?.some(r => r.status === 'FAILED') || false;
        const finalStatus = anyFailed ? 'FAILED' : 'PUBLISHED';

        await supabaseAdmin
          .from('publish_jobs')
          .update({
            status: finalStatus,
            completed_at: new Date().toISOString(),
          })
          .eq('id', publishResult.publish_job_id);

        console.log(
          `[Webhook] Job ${publishResult.publish_job_id} completed early via webhook: ${finalStatus}`
        );
      }
    }

    return NextResponse.json(
      {
        success: true,
        post_submission_id,
        status: internalStatus,
        message: 'Webhook received and processed',
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('[Webhook] Error processing webhook:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
        code: 'INTERNAL_ERROR',
      },
      { status: 500 }
    );
  }
}
