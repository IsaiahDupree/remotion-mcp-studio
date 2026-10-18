// F0119: GET /api/render/status/:jobId endpoint

/**
 * @openapi
 * /api/render/status/{jobId}:
 *   get:
 *     summary: Get render job status
 *     description: |
 *       Returns the current status of a render job.
 *
 *       **Client Polling (F0122):**
 *       - Poll this endpoint every 3 seconds (3000ms) while status is "RENDERING"
 *       - Stop polling when status is "COMPLETE" or "FAILED"
 *       - Stop polling after timeout_at timestamp is reached (10 minutes from started_at)
 *
 *       The progress_pct field (F0120) is estimated from render logs and updates during rendering.
 *     parameters:
 *       - name: jobId
 *         in: path
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: Job status retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 job_id:
 *                   type: string
 *                 status:
 *                   type: string
 *                   enum: [QUEUED, RENDERING, COMPLETE, FAILED]
 *                 progress_pct:
 *                   type: integer
 *                   minimum: 0
 *                   maximum: 100
 *                   description: Estimated render progress (F0120)
 *                 timeout_at:
 *                   type: string
 *                   format: date-time
 *                   nullable: true
 *                   description: Timestamp when render will timeout (started_at + 600s) (F0123)
 *                 output_url:
 *                   type: string
 *                   nullable: true
 *                 error_message:
 *                   type: string
 *                   nullable: true
 *                 started_at:
 *                   type: string
 *                   format: date-time
 *                   nullable: true
 *                 completed_at:
 *                   type: string
 *                   format: date-time
 *                   nullable: true
 *                 created_at:
 *                   type: string
 *                   format: date-time
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { getSignedMediaURL } from '@/lib/storage/signed-urls'; // F0801: Signed URLs

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    // F0126: Bearer token authentication for render_jobs
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

    // Query render_jobs table with user_id for authorization
    const { data: renderJob, error: dbError } = await supabaseAdmin
      .from('render_jobs')
      .select('user_id, status, output_url, error_message, started_at, completed_at, created_at')
      .eq('id', jobId)
      .single();

    if (dbError || !renderJob) {
      return NextResponse.json(
        {
          error: 'Render job not found',
          code: 'JOB_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // F0126: Owner-only access authorization
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

    // F0120: Calculate progress_pct from latest render_logs
    let progressPct = 0;
    if (renderJob.status === 'RENDERING') {
      try {
        const { data: latestLog } = await supabaseAdmin
          .from('render_logs')
          .select('content')
          .eq('render_job_id', jobId)
          .order('line_number', { ascending: false })
          .limit(20); // Check last 20 lines for frame info

        if (latestLog && latestLog.length > 0) {
          // Look for pattern: "Frame 150/300" or similar
          const framePattern = /Frame\s+(\d+)\/(\d+)/i;
          for (const log of latestLog) {
            const match = log.content.match(framePattern);
            if (match) {
              const current = parseInt(match[1], 10);
              const total = parseInt(match[2], 10);
              if (total > 0) {
                progressPct = Math.round((current / total) * 100);
                break;
              }
            }
          }
        }
      } catch (error) {
        console.warn('Failed to calculate progress_pct:', error);
        // Continue with progressPct = 0
      }
    } else if (renderJob.status === 'COMPLETE') {
      progressPct = 100;
    }

    // F0123: Calculate timeout_at timestamp (started_at + 600 seconds)
    let timeoutAt: string | null = null;
    if (renderJob.started_at) {
      const startedDate = new Date(renderJob.started_at);
      const timeoutDate = new Date(startedDate.getTime() + 600 * 1000); // +600 seconds
      timeoutAt = timeoutDate.toISOString();
    }

    // F0801: Generate fresh signed URL for completed renders (1 hour expiry)
    let outputUrl = renderJob.output_url;
    if (renderJob.status === 'COMPLETE' && renderJob.output_url) {
      try {
        // Extract file path from storage URL (e.g., "render_job_123/output.mp4")
        // Assuming output_url contains the file path or we stored it separately
        const signedUrl = await getSignedMediaURL(renderJob.output_url, 'video');
        if (signedUrl) {
          outputUrl = signedUrl;
          console.log(`[Render] Generated fresh signed URL for job ${jobId}`);
        }
      } catch (error) {
        console.warn(`[Render] Failed to generate signed URL for ${jobId}:`, error);
        // Fall back to raw URL if signing fails
      }
    }

    return NextResponse.json({
      success: true,
      job_id: jobId,
      status: renderJob.status,
      progress_pct: progressPct,  // F0120
      timeout_at: timeoutAt,       // F0123
      output_url: outputUrl,        // F0801: Fresh signed URL with 1-hour expiry
      error_message: renderJob.error_message,
      started_at: renderJob.started_at,
      completed_at: renderJob.completed_at,
      created_at: renderJob.created_at,
    });

  } catch (error) {
    console.error('Render status error:', error);
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
