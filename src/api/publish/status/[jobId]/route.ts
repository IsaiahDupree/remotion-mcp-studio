// F0262: Expose GET /api/publish/status/:jobId HTTP route
// Get publish job status with multi-platform results

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { pollBlotatoSubmission, mapBlotatoStatus } from '@/lib/blotato-polling';

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
    const jobId = params.jobId;

    // Fetch publish job
    const { data: publishJob, error: jobError } = await supabaseAdmin
      .from('publish_jobs')
      .select('*')
      .eq('id', jobId)
      .single();

    if (jobError || !publishJob) {
      return NextResponse.json(
        {
          error: 'Publish job not found',
          code: 'NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // Authorization: user must own this job
    if (publishJob.user_id !== userId) {
      return NextResponse.json(
        {
          error: 'Unauthorized access to publish job',
          code: 'FORBIDDEN',
          request_id: crypto.randomUUID(),
        },
        { status: 403 }
      );
    }

    // F0266: Aggregate multi-platform publish results
    const { data: publishResults, error: resultsError } = await supabaseAdmin
      .from('publish_results')
      .select('*')
      .eq('publish_job_id', jobId);

    if (resultsError) {
      console.error('Failed to fetch publish results:', resultsError);
      return NextResponse.json(
        {
          error: 'Failed to fetch publish results',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // For each result that's not in a terminal state, poll Blotato for updates
    const enrichedResults = await Promise.all(
      (publishResults || []).map(async (result) => {
        // If already in terminal state, return as-is
        if (result.status === 'PUBLISHED' || result.status === 'FAILED') {
          return {
            platform: result.platform,
            status: result.status,
            post_url: result.post_url,
            error_message: result.error_message,
            post_submission_id: result.post_submission_id,
          };
        }

        // Poll for updated status if we have a submission ID
        if (result.post_submission_id) {
          const pollResult = await pollBlotatoSubmission(result.post_submission_id);

          if (pollResult.success && pollResult.status) {
            // Update database with latest status
            const updateData: any = {
              status: pollResult.status,
              updated_at: new Date().toISOString(),
            };

            if (pollResult.postUrl) {
              updateData.post_url = pollResult.postUrl;
            }

            if (pollResult.error) {
              updateData.error_message = pollResult.error;
            }

            await supabaseAdmin
              .from('publish_results')
              .update(updateData)
              .eq('id', result.id);

            return {
              platform: result.platform,
              status: pollResult.status,
              post_url: pollResult.postUrl,
              error_message: pollResult.error,
              post_submission_id: result.post_submission_id,
            };
          }
        }

        // Return current state from database
        return {
          platform: result.platform,
          status: result.status,
          post_url: result.post_url,
          error_message: result.error_message,
          post_submission_id: result.post_submission_id,
        };
      })
    );

    // Check if all results are in terminal state
    const allTerminal = enrichedResults.every(
      r => r.status === 'PUBLISHED' || r.status === 'FAILED'
    );
    const anyFailed = enrichedResults.some(r => r.status === 'FAILED');

    // Update publish job if all terminal
    if (allTerminal && publishJob.status !== 'PUBLISHED' && publishJob.status !== 'FAILED') {
      const finalStatus = anyFailed ? 'FAILED' : 'PUBLISHED';

      await supabaseAdmin
        .from('publish_jobs')
        .update({
          status: finalStatus,
          completed_at: new Date().toISOString(),
        })
        .eq('id', jobId);

      publishJob.status = finalStatus;
    }

    // Return aggregated status
    return NextResponse.json({
      publish_job_id: jobId,
      status: publishJob.status,
      media_id: publishJob.media_id,
      platforms: publishJob.platforms || [],
      results: enrichedResults,
      created_at: publishJob.created_at,
      completed_at: publishJob.completed_at,
    });

  } catch (error) {
    console.error('Publish status error:', error);
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
